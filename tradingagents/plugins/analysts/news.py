from tradingagents.core.interface import AnalystModule
from tradingagents.plugins import registry
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import textwrap
from datetime import datetime

class NewsAnalyst(AnalystModule):
    def __init__(self, llm=None):
        self.llm = llm

    def analyze(self, data: dict) -> str:
        """执行新闻事件分析"""
        if not self.llm:
            raise ValueError("LLM未初始化")
        
        news_items = data.get("news", [])
        
        # 格式化新闻数据
        formatted_news = []
        for item in news_items:
            date_str = datetime.fromisoformat(item["datetime"]).strftime("%Y-%m-%d %H:%M")
            formatted_news.append(f"[{date_str}] {item['headline']}: {item['summary']}")
        
        news_text = "\n".join(formatted_news)
        
        prompt_text = textwrap.dedent("""
            你是一名专业新闻分析师，擅长解读财经新闻对市场的影响。请分析以下新闻事件，
            评估其对相关股票和整体市场的潜在影响：
            
            近期相关新闻:
            {news_text}
            
            分析要求:
            1. 识别关键事件及其影响范围
            2. 评估事件对行业和个股的短期/长期影响
            3. 分析市场情绪变化（积极/消极）
            4. 识别潜在的市场反应模式
            5. 提供基于新闻事件的投资策略建议
            
            请以专业分析报告的形式呈现结果。
        """)
        
        prompt = ChatPromptTemplate.from_template(prompt_text)
        chain = prompt | self.llm | StrOutputParser()
        
        return chain.invoke({"news_text": news_text})

# 注册插件
registry.register_plugin("analysts", "news", NewsAnalyst)
