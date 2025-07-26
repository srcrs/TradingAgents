from abc import ABC, abstractmethod
from typing import Dict, Tuple, List, Any

class DataSource(ABC):
    """数据源插件接口"""
    @abstractmethod
    def fetch_data(self, ticker: str, start_date: str, end_date: str) -> Dict[str, Any]:
        pass

class AnalystModule(ABC):
    """分析插件接口"""
    @abstractmethod
    def analyze(self, data: Dict[str, Any]) -> str:
        pass

class TradingStrategy(ABC):
    """交易策略插件接口"""
    @abstractmethod
    def execute(self, analysis_reports: List[str]) -> str:
        pass

class TraderPlugin(ABC):
    """交易员决策插件接口"""
    @abstractmethod
    def make_decision(self, analysis_reports: List[str], context: dict) -> str:
        """
        生成交易决策
        
        参数:
            analysis_reports: 分析报告列表
            context: 交易上下文 (公司/日期等)
        返回:
            交易决策报告
        """
        pass

class GraphEngine(ABC):
    """图计算引擎插件接口"""
    @abstractmethod
    def build_graph(self, components: dict) -> Any:
        """
        构建计算图
        
        参数:
            components: 图节点组件
        返回:
            构建好的计算图对象
        """
        pass
