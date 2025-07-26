from tradingagents.core.interface import AnalystModule
from tradingagents.plugins import registry
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import textwrap

class SentimentAnalyst(AnalystModule):
    def __init__(self, llm=None):
        self.llm = llm

    def analyze(self, data: dict) -> str:
        """执行社交媒体情感分析"""
        if not self.llm:
            raise ValueError("LLM未初始化")
        
        # 提取社交媒体数据
        reddit_posts = data.get("reddit", [])
        twitter_posts = data.get("twitter", [])
        
        # 构建社交媒体文本
        social_text = "### Reddit讨论\n"
        social_text += "\n".join([
            f"标题: {post['title']}\n内容: {post['content'][:200]}...\n情绪: {post['sentiment']}\n"
            for post in reddit_posts[:5]  # 限制数量
        ])
        
        social_text += "\n### Twitter讨论\n"
        social_text += "\n".join([
            f"@{tweet['user']}: {tweet['text']}\n点赞: {tweet['likes']} 转发: {tweet['retweets']}\n"
            for tweet in twitter_posts[:5]  # 限制数量
        ])
        
        prompt_text = textwrap.dedent("""
            你是一名社交媒体情感分析师，擅长从用户讨论中捕捉市场情绪变化。请分析以下社交媒体内容，
            评估投资者对特定股票的情绪倾向：
            
            {social_text}
            
            分析要求:
            1. 识别主流情绪（看涨/看跌/中立）
            2. 量化情绪强度（0-100分）
            3. 检测异常情绪波动
            4. 识别关键影响者和热门话题
            5. 评估情绪与价格变动的相关性
            
            输出格式:
            - 总体情绪评分
            - 关键情绪驱动因素
            - 短期情绪趋势预测
            - 投资建议摘要
            
            最后以"情感结论: [强烈看涨/看涨/中性/看跌/强烈看跌]"结尾
        """)
        
        prompt = ChatPromptTemplate.from_template(prompt_text)
        chain = prompt | self.llm | StrOutputParser()
        
        return chain.invoke({"social_text": social_text})

# 注册插件
registry.register_plugin("analysts", "sentiment", SentimentAnalyst)
