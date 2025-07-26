from tradingagents.core.interface import AnalystModule
from tradingagents.plugins import registry
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import textwrap

class TechnicalAnalyst(AnalystModule):
    def __init__(self, llm=None):
        # LLM可在运行时注入
        self.llm = llm

    def analyze(self, data: dict) -> str:
        """执行技术分析"""
        if not self.llm:
            raise ValueError("LLM未初始化")
        
        # 从数据中提取技术指标
        indicators = data.get("technical_indicators", {})
        
        # 构建提示词
        prompt_text = textwrap.dedent("""
            你是一名经验丰富的技术分析师，擅长解读股票技术指标。请根据以下技术指标数据，
            对股票近期走势进行全面分析，并给出专业见解：
            
            技术指标数据:
            {indicators}
            
            分析要求:
            1. 评估当前趋势（上涨/下跌/盘整）
            2. 识别关键支撑位和阻力位
            3. 分析成交量变化及其意义
            4. 给出未来1-3个交易日的价格预测
            5. 提供交易建议（买入/卖出/持有）
            
            请以专业分析报告的形式呈现结果。
        """)
        
        prompt = ChatPromptTemplate.from_template(prompt_text)
        chain = prompt | self.llm | StrOutputParser()
        
        return chain.invoke({"indicators": indicators})

# 注册插件
registry.register_plugin("analysts", "technical", TechnicalAnalyst)
