from tradingagents.core.interface import TraderPlugin
from tradingagents.plugins import registry
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import textwrap
from typing import List

class BasicTrader(TraderPlugin):
    def __init__(self, llm=None, memory=None):
        self.llm = llm
        self.memory = memory

    def make_decision(self, analysis_reports: List[str], context: dict) -> str:
        """生成基本交易决策"""
        if not self.llm:
            raise ValueError("LLM未初始化")
        
        # 组合分析报告
        combined_reports = "\n\n".join([
            f"### {report_type}报告\n{content}"
            for report_type, content in zip(
                ["市场分析", "情感分析", "新闻分析", "基本面分析"],
                analysis_reports
            )
        ])
        
        # 添加上下文信息
        context_info = f"公司: {context.get('company', '未知')}, 日期: {context.get('date', '未知')}"
        
        # 构建提示词
        prompt_text = textwrap.dedent("""
            你是一名专业交易员，负责根据以下分析报告做出最终交易决策：
            
            {combined_reports}
            
            当前交易上下文:
            {context_info}
            
            决策要求:
            1. 综合评估所有分析因素
            2. 平衡风险和收益
            3. 给出明确的交易指令（买入/持有/卖出）
            4. 提供仓位管理建议
            
            输出格式:
            - 总体市场评估
            - 具体交易指令
            - 目标价位
            - 止损点设置
            
            最后以"最终决策: [买入/持有/卖出]"结尾
        """)
        
        prompt = ChatPromptTemplate.from_template(prompt_text)
        chain = prompt | self.llm | StrOutputParser()
        
        return chain.invoke({
            "combined_reports": combined_reports,
            "context_info": context_info
        })

# 注册插件
registry.register_plugin("traders", "basic", BasicTrader)
