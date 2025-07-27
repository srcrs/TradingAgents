import sqlite3
from rank_bm25 import BM25Okapi
import jieba
import os
from typing import List, Dict, Any, Tuple

class PersistentBM25Memory:
    """基于BM25算法的持久化记忆系统，支持中文分词和SQLite存储"""
    
    def __init__(self, db_path: str):
        """
        初始化记忆系统
        :param db_path: SQLite数据库文件路径
        """
        self.db_path = db_path
        self.documents: List[Dict[str, Any]] = []  # 存储记忆记录
        self.tokenized_docs: List[List[str]] = []  # 分词后的文档
        self.bm25: BM25Okapi = None
        
        # 初始化数据库
        self.conn = sqlite3.connect(db_path)
        self._init_db()
        self._load_from_db()
        
        # 初始化分词器
        jieba.initialize()
    
    def _init_db(self):
        """创建数据库表结构"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY,
                text TEXT NOT NULL,
                outcome TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
    
    def _load_from_db(self):
        """从数据库加载记忆记录"""
        cursor = self.conn.execute("SELECT id, text, outcome FROM memories")
        for row in cursor:
            doc_id, text, outcome = row
            self.documents.append({
                "id": doc_id,
                "text": text,
                "outcome": outcome
            })
            tokens = jieba.lcut(text)  # 中文分词
            self.tokenized_docs.append(tokens)
        
        # 初始构建BM25索引
        if self.tokenized_docs:
            self.bm25 = BM25Okapi(self.tokenized_docs)
    
    def add_memory(self, text: str, outcome: str):
        """
        添加新记忆记录
        :param text: 记忆文本内容
        :param outcome: 相关结果描述
        """
        # 添加到内存
        doc_id = len(self.documents) + 1
        self.documents.append({
            "id": doc_id,
            "text": text,
            "outcome": outcome
        })
        tokens = jieba.lcut(text)
        self.tokenized_docs.append(tokens)
        
        # 添加到数据库
        self.conn.execute(
            "INSERT INTO memories (text, outcome) VALUES (?, ?)",
            (text, outcome)
        )
        self.conn.commit()
        
        # 重建BM25索引
        self._rebuild_index()
    
    def query(self, text: str, top_n: int = 3) -> List[Dict[str, Any]]:
        """
        查询相似记忆记录
        :param text: 查询文本
        :param top_n: 返回结果数量
        :return: 相似记忆记录列表
        """
        if not self.bm25 or not self.tokenized_docs:
            return []
        
        tokens = jieba.lcut(text)
        scores = self.bm25.get_scores(tokens)
        
        # 获取最高分记录
        scored_docs = [(score, self.documents[i]) for i, score in enumerate(scores)]
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        return [doc for _, doc in scored_docs[:top_n]]
    
    def _rebuild_index(self):
        """重建BM25索引"""
        self.bm25 = BM25Okapi(self.tokenized_docs)
    
    def __del__(self):
        """关闭数据库连接"""
        if hasattr(self, 'conn'):
            self.conn.close()
