from tradingagents.core.interface import GraphEngine
from langgraph.graph import Graph
from typing import Any, Dict

class DefaultGraphEngine(GraphEngine):
    def build_graph(self, graph_setup: Any) -> Graph:
        """
        构建默认计算图
        
        参数:
            graph_setup: 图设置对象，包含构建图所需的所有组件
        返回:
            构建好的计算图对象
        """
        # 创建新图实例
        workflow = Graph()
        
        # 添加节点（代理工作流）
        workflow.add_node("market_analyst", graph_setup.market_analyst_node)
        workflow.add_node("sentiment_analyst", graph_setup.sentiment_analyst_node)
        workflow.add_node("news_analyst", graph_setup.news_analyst_node)
        workflow.add_node("fundamentals_analyst", graph_setup.fundamentals_analyst_node)
        workflow.add_node("bull_researcher", graph_setup.bull_researcher_node)
        workflow.add_node("bear_researcher", graph_setup.bear_researcher_node)
        workflow.add_node("investment_judge", graph_setup.investment_judge_node)
        workflow.add_node("trader", graph_setup.trader_node)
        workflow.add_node("aggressive_risk", graph_setup.aggressive_risk_node)
        workflow.add_node("conservative_risk", graph_setup.conservative_risk_node)
        workflow.add_node("neutral_risk", graph_setup.neutral_risk_node)
        workflow.add_node("risk_judge", graph_setup.risk_judge_node)
        workflow.add_node("final_decision", graph_setup.final_decision_node)
        
        # 定义工作流
        workflow.set_entry_point("market_analyst")
        workflow.add_edge("market_analyst", "sentiment_analyst")
        workflow.add_edge("sentiment_analyst", "news_analyst")
        workflow.add_edge("news_analyst", "fundamentals_analyst")
        workflow.add_edge("fundamentals_analyst", "bull_researcher")
        workflow.add_edge("bull_researcher", "investment_judge")
        workflow.add_edge("investment_judge", "bear_researcher")
        workflow.add_edge("bear_researcher", "investment_judge")
        workflow.add_edge("investment_judge", "trader")
        workflow.add_edge("trader", "aggressive_risk")
        workflow.add_edge("trader", "conservative_risk")
        workflow.add_edge("trader", "neutral_risk")
        workflow.add_edge("aggressive_risk", "risk_judge")
        workflow.add_edge("conservative_risk", "risk_judge")
        workflow.add_edge("neutral_risk", "risk_judge")
        workflow.add_edge("risk_judge", "final_decision")
        workflow.set_finish_point("final_decision")
        
        # 添加条件边
        workflow.add_conditional_edges(
            "investment_judge",
            graph_setup.conditional_logic.decide_to_invite_bear_researcher,
            {
                "end": "trader",  # 不需要继续辩论
                "continue": "bear_researcher",  # 继续空头研究
            },
        )
        
        return workflow

# 注册插件
from tradingagents.plugins import registry
registry.register_plugin("graph_engine", "default", DefaultGraphEngine)
