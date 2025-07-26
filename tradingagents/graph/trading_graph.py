# TradingAgents/graph/trading_graph.py

import os
from pathlib import Path
import json
import yaml  # 添加yaml支持
from datetime import date
from typing import Dict, Any, Tuple, List, Optional

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.prebuilt import ToolNode

from tradingagents.agents import *
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.agents.utils.memory import FinancialSituationMemory
from tradingagents.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
)
from tradingagents.dataflows.interface import set_config
from tradingagents.core.interface import DataSource, AnalystModule, TradingStrategy  # 添加接口导入
from tradingagents.plugins import registry  # 添加插件注册表

from .conditional_logic import ConditionalLogic
from .setup import GraphSetup
from .propagation import Propagator
from .reflection import Reflector
from .signal_processing import SignalProcessor


class TradingAgentsGraph:
    """Main class that orchestrates the trading agents framework."""

    def __init__(
        self,
        selected_analysts=["market", "social", "news", "fundamentals"],
        debug=False,
        config: Dict[str, Any] = None,
    ):
        """Initialize the trading agents graph and components.

        Args:
            selected_analysts: List of analyst types to include
            debug: Whether to run in debug mode
            config: Configuration dictionary. If None, uses default config
        """
        self.debug = debug
        self.config = config or DEFAULT_CONFIG

        # Update the interface's config
        set_config(self.config)

        # Create necessary directories
        os.makedirs(
            os.path.join(self.config["project_dir"], "dataflows/data_cache"),
            exist_ok=True,
        )

        # Initialize LLMs
        if self.config["llm_provider"].lower() == "openai" or self.config["llm_provider"] == "ollama" or self.config["llm_provider"] == "openrouter":
            self.deep_thinking_llm = ChatOpenAI(model=self.config["deep_think_llm"], base_url=self.config["backend_url"])
            self.quick_thinking_llm = ChatOpenAI(model=self.config["quick_think_llm"], base_url=self.config["backend_url"])
        elif self.config["llm_provider"].lower() == "anthropic":
            self.deep_thinking_llm = ChatAnthropic(model=self.config["deep_think_llm"], base_url=self.config["backend_url"])
            self.quick_thinking_llm = ChatAnthropic(model=self.config["quick_think_llm"], base_url=self.config["backend_url"])
        elif self.config["llm_provider"].lower() == "google":
            self.deep_thinking_llm = ChatGoogleGenerativeAI(model=self.config["deep_think_llm"])
            self.quick_thinking_llm = ChatGoogleGenerativeAI(model=self.config["quick_think_llm"])
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config['llm_provider']}")
        
        self.toolkit = Toolkit(config=self.config)

        # Initialize memories
        self.bull_memory = FinancialSituationMemory("bull_memory", self.config)
        self.bear_memory = FinancialSituationMemory("bear_memory", self.config)
        self.trader_memory = FinancialSituationMemory("trader_memory", self.config)
        self.invest_judge_memory = FinancialSituationMemory("invest_judge_memory", self.config)
        self.risk_manager_memory = FinancialSituationMemory("risk_manager_memory", self.config)

        # Create tool nodes
        self.tool_nodes = self._create_tool_nodes()

        # Initialize components
        self.conditional_logic = ConditionalLogic()
        self.graph_setup = GraphSetup(
            self.quick_thinking_llm,
            self.deep_thinking_llm,
            self.toolkit,
            self.tool_nodes,
            self.bull_memory,
            self.bear_memory,
            self.trader_memory,
            self.invest_judge_memory,
            self.risk_manager_memory,
            self.conditional_logic,
        )

        self.propagator = Propagator()
        self.reflector = Reflector(self.quick_thinking_llm)
        self.signal_processor = SignalProcessor(self.quick_thinking_llm)

        # State tracking
        self.curr_state = None
        self.ticker = None
        self.log_states_dict = {}  # date to full state dict

        # 加载图引擎插件
        self.graph_engine = None
        try:
            if "graph_engine" in self.config and "default" in self.config["graph_engine"]:
                engine_class = registry.get_plugin("graph_engine", "default")
                self.graph_engine = engine_class()
                self.graph = self.graph_engine.build_graph(self.graph_setup)
            else:
                # 回退到原始图构建方式
                self.graph = self.graph_setup.setup_graph(selected_analysts)
        except Exception as e:
            print(f"加载图引擎失败: {e}")
            self.graph = self.graph_setup.setup_graph(selected_analysts)

    def _create_tool_nodes(self) -> Dict[str, ToolNode]:
        """动态创建工具节点，基于插件配置"""
        tool_nodes = {}
        
        # 加载插件配置
        try:
            with open('config/plugins.yaml', 'r') as f:
                plugins_config = yaml.safe_load(f)
        except:
            plugins_config = {}
        
        # 为每种分析类型创建工具节点
        for analyst_type in ["market", "social", "news", "fundamentals"]:
            tools = []
            
            # 添加数据源插件
            if "data_sources" in plugins_config:
                for name, class_path in plugins_config["data_sources"].items():
                    module_name, class_name = class_path.rsplit('.', 1)
                    module = __import__(module_name, fromlist=[class_name])
                    plugin_class = getattr(module, class_name)
                    plugin_instance = plugin_class()
                    
                    # 包装为ToolNode兼容函数
                    def plugin_wrapper(ticker, start_date, end_date, data_type=analyst_type, instance=plugin_instance):
                        return instance.fetch_data(ticker, start_date, end_date, data_type)
                    
                    tools.append(plugin_wrapper)
            
            # 添加分析插件
            if analyst_type in plugins_config.get("analysts", {}):
                class_path = plugins_config["analysts"][analyst_type]
                module_name, class_name = class_path.rsplit('.', 1)
                module = __import__(module_name, fromlist=[class_name])
                plugin_class = getattr(module, class_name)
                plugin_instance = plugin_class()
                
                # 包装为ToolNode兼容函数
                def analyst_wrapper(data, instance=plugin_instance):
                    return instance.analyze(data)
                
                tools.append(analyst_wrapper)
            
            # 如果配置了插件，则创建ToolNode
            if tools:
                tool_nodes[analyst_type] = ToolNode(tools)
        
        return tool_nodes

    def propagate(self, company_name, trade_date):
        """运行交易代理图"""
        self.ticker = company_name

        # 加载策略插件
        strategy_plugin = None
        try:
            with open('config/plugins.yaml', 'r') as f:
                plugins_config = yaml.safe_load(f)
                if "strategies" in plugins_config:
                    # 使用配置中的第一个策略
                    strategy_name = next(iter(plugins_config["strategies"]))
                    class_path = plugins_config["strategies"][strategy_name]
                    module_name, class_name = class_path.rsplit('.', 1)
                    module = __import__(module_name, fromlist=[class_name])
                    strategy_class = getattr(module, class_name)
                    strategy_plugin = strategy_class()
        except:
            pass

        # 初始化状态
        init_agent_state = self.propagator.create_initial_state(company_name, trade_date)
        args = self.propagator.get_graph_args()

        if self.debug:
            trace = []
            for chunk in self.graph.stream(init_agent_state, **args):
                if chunk["messages"]:
                    chunk["messages"][-1].pretty_print()
                    trace.append(chunk)
            final_state = trace[-1]
        else:
            final_state = self.graph.invoke(init_agent_state, **args)

        # 加载交易员插件
        trader_plugin = None
        try:
            if "traders" in self.config and "basic" in self.config["traders"]:
                trader_class = registry.get_plugin("traders", "basic")
                trader_plugin = trader_class(llm=self.quick_thinking_llm)
        except Exception as e:
            print(f"加载交易员插件失败: {e}")

        # 执行决策
        analysis_reports = [
            final_state["market_report"],
            final_state["sentiment_report"],
            final_state["news_report"],
            final_state["fundamentals_report"]
        ]
        
        if trader_plugin:
            context = {"company": company_name, "date": trade_date}
            final_decision = trader_plugin.make_decision(analysis_reports, context)
        elif strategy_plugin:  # 回退到旧策略系统
            final_decision = strategy_plugin.execute(analysis_reports)
        else:
            final_decision = "无法生成交易决策：未配置有效插件"

        final_state["final_trade_decision"] = final_decision

        # 存储状态用于反思
        self.curr_state = final_state
        self._log_state(trade_date, final_state)

        return final_state, self.process_signal(final_state["final_trade_decision"])

    def _log_state(self, trade_date, final_state):
        """Log the final state to a JSON file."""
        self.log_states_dict[str(trade_date)] = {
            "company_of_interest": final_state["company_of_interest"],
            "trade_date": final_state["trade_date"],
            "market_report": final_state["market_report"],
            "sentiment_report": final_state["sentiment_report"],
            "news_report": final_state["news_report"],
            "fundamentals_report": final_state["fundamentals_report"],
            "investment_debate_state": {
                "bull_history": final_state["investment_debate_state"]["bull_history"],
                "bear_history": final_state["investment_debate_state"]["bear_history"],
                "history": final_state["investment_debate_state"]["history"],
                "current_response": final_state["investment_debate_state"][
                    "current_response"
                ],
                "judge_decision": final_state["investment_debate_state"][
                    "judge_decision"
                ],
            },
            "trader_investment_decision": final_state["trader_investment_plan"],
            "risk_debate_state": {
                "risky_history": final_state["risk_debate_state"]["risky_history"],
                "safe_history": final_state["risk_debate_state"]["safe_history"],
                "neutral_history": final_state["risk_debate_state"]["neutral_history"],
                "history": final_state["risk_debate_state"]["history"],
                "judge_decision": final_state["risk_debate_state"]["judge_decision"],
            },
            "investment_plan": final_state["investment_plan"],
            "final_trade_decision": final_state["final_trade_decision"],
        }

        # Save to file
        directory = Path(f"eval_results/{self.ticker}/TradingAgentsStrategy_logs/")
        directory.mkdir(parents=True, exist_ok=True)

        with open(
            f"eval_results/{self.ticker}/TradingAgentsStrategy_logs/full_states_log_{trade_date}.json",
            "w",
        ) as f:
            json.dump(self.log_states_dict, f, indent=4)

    def reflect_and_remember(self, returns_losses):
        """Reflect on decisions and update memory based on returns."""
        self.reflector.reflect_bull_researcher(
            self.curr_state, returns_losses, self.bull_memory
        )
        self.reflector.reflect_bear_researcher(
            self.curr_state, returns_losses, self.bear_memory
        )
        self.reflector.reflect_trader(
            self.curr_state, returns_losses, self.trader_memory
        )
        self.reflector.reflect_invest_judge(
            self.curr_state, returns_losses, self.invest_judge_memory
        )
        self.reflector.reflect_risk_manager(
            self.curr_state, returns_losses, self.risk_manager_memory
        )

    def process_signal(self, full_signal):
        """Process a signal to extract the core decision."""
        return self.signal_processor.process_signal(full_signal)
