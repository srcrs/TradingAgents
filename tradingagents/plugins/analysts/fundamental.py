from tradingagents.core.interface import AnalystModule
from tradingagents.plugins import registry
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import textwrap

class FundamentalAnalyst(AnalystModule):
    def __init__(self, llm=None):
        self.llm = llm

    def analyze(self, data: dict) -> str:
        """执行基本面分析"""
        if not self.llm:
            raise ValueError("LLM未初始化")
        
        financials = data.get("financial_statements", {})
        
        prompt_text = textwrap.dedent("""
            你是一名资深基本面分析师，擅长评估公司内在价值。请根据以下财务报表数据，
            对公司进行全面的基本面分析：
            
            财务报表数据:
            {financials}
            
            分析要求:
            1. 评估公司财务健康状况（盈利能力/偿债能力/运营效率）
            2. 计算关键财务比率（PE/PB/ROE等）
            3. 分析现金流状况
            4. 评估公司成长性和行业地位
            5. 给出长期投资建议
            
            请使用专业财务分析术语呈现报告。
        """)
        
        prompt = ChatPromptTemplate.from_template(prompt_text)
        chain = prompt | self.llm | StrOutputParser()
        
        return chain.invoke({"financials": financials})

# 注册插件
registry.register_plugin("analysts", "fundamental", FundamentalAnalyst)
