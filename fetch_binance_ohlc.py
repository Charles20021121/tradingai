"""
从 Binance API 获取真实的 1小时 OHLC 蜡烛图数据
"""
import requests
import pandas as pd
import json
from datetime import datetime, timedelta

def fetch_binance_klines(symbol="BTCUSDT", interval="1h", limit=500):
    """
    从 Binance 获取 K线数据
    
    interval 选项:
    - 1m, 3m, 5m, 15m, 30m (分钟)
    - 1h, 2h, 4h, 6h, 8h, 12h (小时)
    - 1d, 3d, 1w, 1M (日/周/月)
    
    limit: 最多 1000 条
    """
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    
    print(f"📈 从 Binance 获取 {symbol} {interval} K线数据...")
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    # Binance 返回格式: [开盘时间, 开, 高, 低, 收, 成交量, ...]
    df = pd.DataFrame(data, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
        'taker_buy_quote', 'ignore'
    ])
    
    # 转换类型
    df['datetime'] = pd.to_datetime(df['open_time'], unit='ms')
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)
    
    # 只保留需要的列
    df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
    
    print(f"✅ 获取到 {len(df)} 条 OHLC 数据")
    print(f"📅 时间范围: {df['datetime'].min()} 至 {df['datetime'].max()}")
    
    return df

def convert_to_tradingview_format(df):
    """转换为 TradingView Lightweight Charts 格式"""
    candles = []
    for _, row in df.iterrows():
        # 使用日期字符串格式
        time_str = row['datetime'].strftime('%Y-%m-%d')
        # 对于小时级，需要使用时间戳
        timestamp = int(row['datetime'].timestamp())
        candles.append({
            "time": timestamp,
            "open": round(row['open'], 2),
            "high": round(row['high'], 2),
            "low": round(row['low'], 2),
            "close": round(row['close'], 2)
        })
    return candles

def fetch_binance_klines_batch(symbol="BTCUSDT", interval="1h", total_limit=2000):
    """
    分批获取超过 1000 条的 K线数据
    """
    all_data = []
    end_time = None
    remaining = total_limit
    
    print(f"📈 从 Binance 获取 {symbol} {interval} K线数据 (共 {total_limit} 条)...")
    
    while remaining > 0:
        limit = min(remaining, 1000)
        url = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        if end_time:
            params["endTime"] = end_time
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            break
        
        all_data = data + all_data  # 新数据在前
        end_time = data[0][0] - 1  # 下一批的结束时间
        remaining -= len(data)
        print(f"  已获取 {total_limit - remaining} 条...")
    
    # 转换为 DataFrame
    df = pd.DataFrame(all_data, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
        'taker_buy_quote', 'ignore'
    ])
    
    df['datetime'] = pd.to_datetime(df['open_time'], unit='ms')
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)
    df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
    df = df.sort_values('datetime').reset_index(drop=True)
    
    print(f"✅ 获取到 {len(df)} 条 OHLC 数据")
    print(f"📅 时间范围: {df['datetime'].min()} 至 {df['datetime'].max()}")
    
    return df

def main():
    # 获取 26280 条 1小时 K线数据 (约 3 年)
    df = fetch_binance_klines_batch("BTCUSDT", interval="1h", total_limit=26280)
    
    # 转换并保存 JSON
    candles = convert_to_tradingview_format(df)
    with open('btc_1h_ohlc.json', 'w') as f:
        json.dump(candles, f)
    print("💾 已保存到 btc_1h_ohlc.json")
    
    return df, candles

if __name__ == "__main__":
    df, candles = main()
