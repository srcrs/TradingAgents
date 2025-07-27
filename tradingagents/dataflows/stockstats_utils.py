import pandas as pd
import yfinance as yf
from stockstats import wrap
from typing import Annotated
import os
import datetime  # 添加datetime导入
from .config import get_config


class StockstatsUtils:
    @staticmethod
    def get_stock_stats(
        symbol: Annotated[str, "ticker symbol for the company"],
        indicator: Annotated[
            str, "quantitative indicators based off of the stock data for the company"
        ],
        curr_date: Annotated[
            str, "curr date for retrieving stock price data, YYYY-mm-dd"
        ],
        data_dir: Annotated[
            str,
            "directory where the stock data is stored.",
        ],
        online: Annotated[
            bool,
            "whether to use online tools to fetch data or offline tools. If True, will use online tools.",
        ] = False,
    ):
        df = None
        data = None

        # 确保日期为字符串格式
        if not isinstance(curr_date, str):
            curr_date = str(curr_date)
        
        if not online:
            try:
                data = pd.read_csv(
                    os.path.join(
                        data_dir,
                        f"{symbol}-YFin-data-2015-01-01-2025-03-25.csv",
                    )
                )
                df = wrap(data)
            except FileNotFoundError:
                raise Exception("Stockstats fail: Yahoo Finance data not fetched yet!")
        else:
            # 获取当前日期字符串
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            
            # 计算开始日期（15年前）
            start_date = (datetime.date.today() - datetime.timedelta(days=15*365)).strftime("%Y-%m-%d")
            
            # 构建文件路径
            data_file = os.path.join(
                data_dir,
                f"{symbol}-YFin-data-{start_date}-{today_str}.csv",
            )
            
            if os.path.exists(data_file):
                data = pd.read_csv(data_file)
                data["Date"] = pd.to_datetime(data["Date"])
            else:
                data = yf.download(
                    symbol,
                    start=start_date,
                    end=today_str,
                    multi_level_index=False,
                    progress=False,
                    auto_adjust=True,
                )
                data = data.reset_index()
                data.to_csv(data_file, index=False)

            df = wrap(data)
            df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

        df[indicator]  # 触发指标计算
        matching_rows = df[df["Date"].str.startswith(curr_date)]

        if not matching_rows.empty:
            indicator_value = matching_rows[indicator].values[0]
            return indicator_value
        else:
            return "N/A: Not a trading day (weekend or holiday)"
