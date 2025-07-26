from tradingagents.core.interface import TradingStrategy
from tradingagents.plugins import registry
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import textwrap

class ConservativeStrategy(TradingStrategy):
    def __init__(self, llm=None):
        self.llm = llm

    def execute(self, analysis_reports: List[str]) -> str:
        """执行保守交易策略"""
        if not self.llm:
            raise ValueError("LLM未初始化")
        
        # 组合所有分析报告
        combined_reports = "\n\n".join([
            f"### {report_type}报告\n{content}"
            for report_type, content in zip(
                ["市场分析", "情感分析", "新闻分析", "基本面分析"],
                analysis_reports
            )
        ])
        
        prompt_text = textwrap.dedent("""
            你是一名保守型交易策略师，擅长在控制风险的前提下获取稳定收益。请根据以下分析报告，
            制定保守的交易策略：
            
            {combined_reports}
            
            策略要求:
            1. 优先考虑资本保值和风险控制
            2. 避免高波动性资产
            3. 采用分散投资原则
            4. 设置严格的止损点
            5. 偏好股息稳定的大盘股
            
            输出格式:
            - 资产配置比例（股票/债券/现金）
            - 具体股票选择建议（不超过3支）
            - 买入/卖出价格区间
            - 止损点设置
            - 持有期限建议
            
            最后以"最终决策: [买入/持有/卖出]"结尾
        """)
        
        prompt = ChatPromptTemplate.from_template(prompt_text)
        chain = prompt | self.llm | StrOutputParser()
        
        return chain.invoke({"combined_reports": combined_reports})

# 注册插件
registry.register_plugin("strategies", "conservative", ConservativeStrategy)
