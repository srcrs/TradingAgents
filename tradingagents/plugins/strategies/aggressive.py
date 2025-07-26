from tradingagents.core.interface import TradingStrategy
from tradingagents.plugins import registry
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import textwrap
from typing import List

class AggressiveStrategy(TradingStrategy):
    def __init__(self, llm=None):
        self.llm = llm

    def execute(self, analysis_reports: List[str]) -> str:
        """执行激进交易策略"""
        if not self.llm:
            raise ValueError("LLM未初始化")
        
        # 组合分析报告
        combined_reports = "\n\n".join([
            f"▼▼ {report_type} ▼▼\n{content}"
            for report_type, content in zip(
                ["技术分析", "市场情绪", "新闻事件", "基本面"],
                analysis_reports
            )
        ])
        
        prompt_text = textwrap.dedent("""
            你是一名激进型交易策略师，专注捕捉高风险高回报机会。请根据以下分析报告，
            制定具有高潜在收益的交易策略：
            
            {combined_reports}
            
            策略要求:
            1. 优先考虑高波动性资产
            2. 合理运用杠杆（2-5倍）
            3. 识别短期交易机会（持仓<3天）
            4. 设置动态止盈/止损点
            5. 关注突破形态和成交量异动
            
            输出格式:
            - 目标资产及仓位配比
            - 杠杆使用建议
            - 入场价格区间
            - 止盈/止损点位（追踪止损建议）
            - 预期持仓时间
            
            最后以"最终决策: [全仓买入/部分持仓/清仓]"结尾
        """)
        
        prompt = ChatPromptTemplate.from_template(prompt_text)
        chain = prompt | self.llm | StrOutputParser()
        
        return chain.invoke({"combined_reports": combined_reports})

# 注册插件
registry.register_plugin("strategies", "aggressive", AggressiveStrategy)
