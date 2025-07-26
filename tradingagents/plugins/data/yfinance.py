import yfinance as yf
from tradingagents.core.interface import DataSource
from tradingagents.plugins import registry
from datetime import datetime, timedelta
import pandas as pd

class YFinanceSource(DataSource):
    def fetch_data(self, ticker: str, start_date: str, end_date: str, data_type: str) -> Dict[str, Any]:
        """
        从Yahoo Finance获取股票数据
        
        参数:
            ticker: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            data_type: 数据类型 (historical, options, dividends)
        """
        stock = yf.Ticker(ticker)
        
        if data_type == "historical":
            # 获取历史价格数据
            data = stock.history(
                start=start_date,
                end=(datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"),
                interval="1d"
            )
            # 转换为字典格式
            return data.reset_index().to_dict(orient="records")
        
        elif data_type == "options":
            # 获取期权数据
            return {
                "calls": stock.options,
                "expirations": stock.options
            }
        
        elif data_type == "dividends":
            # 获取股息数据
            return stock.dividends.to_dict()
        
        else:
            raise ValueError(f"不支持的Yahoo Finance数据类型: {data_type}")

# 注册插件
registry.register_plugin("data_sources", "yfinance", YFinanceSource)
