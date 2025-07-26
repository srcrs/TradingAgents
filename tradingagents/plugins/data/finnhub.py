import json
import os
from pathlib import Path
from tradingagents.core.interface import DataSource
from typing import Dict, Any, Tuple

class FinnHubSource(DataSource):
    def fetch_data(self, ticker: str, start_date: str, end_date: str, data_type: str, period: str = None) -> Dict[str, Any]:
        """
        从FinnHub获取格式化金融数据
        
        参数:
            ticker: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            data_type: 数据类型 (insider_trans, SEC_filings, news_data等)
            period: 可选，周期 (annual/quarterly)
        """
        # 项目根目录路径
        project_dir = Path(__file__).resolve().parent.parent.parent.parent
        data_dir = project_dir / "dataflows" / "data_cache"
        
        if period:
            data_path = data_dir / "finnhub_data" / data_type / f"{ticker}_{period}_data_formatted.json"
        else:
            data_path = data_dir / "finnhub_data" / data_type / f"{ticker}_data_formatted.json"
        
        # 确保目录存在
        data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 如果文件不存在则返回空字典
        if not data_path.exists():
            return {}
        
        with open(data_path, "r") as f:
            data = json.load(f)
        
        # 按日期范围过滤数据
        filtered_data = {}
        for key, value in data.items():
            if start_date <= key <= end_date and len(value) > 0:
                filtered_data[key] = value
        
        return filtered_data

# 注册插件
from tradingagents.plugins import registry
registry.register_plugin("data_sources", "finnhub", FinnHubSource)
