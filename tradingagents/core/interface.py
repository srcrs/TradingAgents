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
