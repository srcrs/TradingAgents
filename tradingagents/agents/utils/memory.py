import chromadb
from chromadb.config import Settings
from openai import OpenAI


from .bm25_memory import PersistentBM25Memory

class FinancialSituationMemory:
    """基于BM25算法的记忆系统，替代原向量检索方案"""
    
    def __init__(self, name, config):
        """
        初始化记忆系统
        :param name: 记忆名称，用于数据库文件名
        :param config: 配置字典
        """
        self.memory = PersistentBM25Memory(f"{name}_memory.db")
        
    def add_situations(self, situations_and_advice):
        """
        添加情景与建议
        :param situations_and_advice: [(情景描述, 建议), ...]
        """
        for situation, recommendation in situations_and_advice:
            self.memory.add_memory(situation, recommendation)
    
    def get_memories(self, current_situation, n_matches=1):
        """
        检索相似记忆
        :param current_situation: 当前情景描述
        :param n_matches: 返回结果数量
        :return: 匹配的记忆记录列表
        """
        return self.memory.query(current_situation, top_n=n_matches)


if __name__ == "__main__":
    # Example usage
    matcher = FinancialSituationMemory()

    # Example data
    example_data = [
        (
            "High inflation rate with rising interest rates and declining consumer spending",
            "Consider defensive sectors like consumer staples and utilities. Review fixed-income portfolio duration.",
        ),
        (
            "Tech sector showing high volatility with increasing institutional selling pressure",
            "Reduce exposure to high-growth tech stocks. Look for value opportunities in established tech companies with strong cash flows.",
        ),
        (
            "Strong dollar affecting emerging markets with increasing forex volatility",
            "Hedge currency exposure in international positions. Consider reducing allocation to emerging market debt.",
        ),
        (
            "Market showing signs of sector rotation with rising yields",
            "Rebalance portfolio to maintain target allocations. Consider increasing exposure to sectors benefiting from higher rates.",
        ),
    ]

    # Add the example situations and recommendations
    matcher.add_situations(example_data)

    # Example query
    current_situation = """
    Market showing increased volatility in tech sector, with institutional investors 
    reducing positions and rising interest rates affecting growth stock valuations
    """

    try:
        recommendations = matcher.get_memories(current_situation, n_matches=2)

        for i, rec in enumerate(recommendations, 1):
            print(f"\nMatch {i}:")
            print(f"Similarity Score: {rec['similarity_score']:.2f}")
            print(f"Matched Situation: {rec['matched_situation']}")
            print(f"Recommendation: {rec['recommendation']}")

    except Exception as e:
        print(f"Error during recommendation: {str(e)}")
