"""
数据获取模块 - 使用akshare获取A股数据
支持多数据源 + 离线降级mock数据
"""
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import os
import json
import time
import random

CACHE_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(CACHE_DIR, exist_ok=True)

# ETF代码列表
ETF_CODES = {'515980', '512980', '513500', '159920', '510300', '510500', '159915', '513050'}

# Mock数据配置（用于网络不可用时的演示）
MOCK_PRICES = {
    '688318': 113.40,  # 财富趋势
    '688210': 44.16,   # 统联精密
    '603220': 26.67,   # 中贝通信
    '600255': 3.62,    # 鑫科材料
    '301236': 38.92,   # 软通动力
    '515980': 1.28,    # 人工智能ETF
}

def _retry_get(func, *args, max_retries=2, **kwargs):
    """带重试的获取函数"""
    for i in range(max_retries):
        try:
            result = func(*args, **kwargs)
            if result is not None and not result.empty:
                return result
        except Exception as e:
            if i < max_retries - 1:
                time.sleep(0.5)
            else:
                raise e
    return pd.DataFrame()

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """标准化列名"""
    col_map = {}
    for c in df.columns:
        cl = c.lower()
        if '日期' in c or 'date' in cl:
            col_map[c] = 'date'
        elif '开盘' in c or 'open' in cl:
            col_map[c] = 'open'
        elif '收盘' in c or 'close' in cl:
            col_map[c] = 'close'
        elif '最高' in c or 'high' in cl:
            col_map[c] = 'high'
        elif '最低' in c or 'low' in cl:
            col_map[c] = 'low'
        elif '成交量' in c or 'volume' in cl:
            col_map[c] = 'volume'
        elif '成交额' in c or 'amount' in cl:
            col_map[c] = 'amount'
    
    df = df.rename(columns=col_map)
    needed = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount']
    df = df[[c for c in needed if c in df.columns]]
    
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])
        df = df.sort_values('date').reset_index(drop=True)
    
    return df

def _generate_mock_data(code: str, days: int = 120) -> pd.DataFrame:
    """生成模拟数据（当网络不可用时使用）"""
    base_price = MOCK_PRICES.get(code, 10.0)
    today = datetime.now()
    records = []
    
    price = base_price * random.uniform(0.85, 0.95)  # 从较低位置开始，模拟一段时间的涨跌
    
    for i in range(days):
        date = today - timedelta(days=days - i)
        # 跳过周末
        if date.weekday() >= 5:
            continue
        
        # 随机涨跌模拟真实K线
        change = random.uniform(-0.03, 0.035)
        open_p = price * (1 + random.uniform(-0.01, 0.01))
        close_p = price * (1 + change)
        high_p = max(open_p, close_p) * (1 + random.uniform(0, 0.015))
        low_p = min(open_p, close_p) * (1 - random.uniform(0, 0.015))
        volume = random.randint(500000, 5000000)
        amount = volume * close_p
        
        records.append({
            'date': date,
            'open': round(open_p, 2),
            'close': round(close_p, 2),
            'high': round(high_p, 2),
            'low': round(low_p, 2),
            'volume': volume,
            'amount': round(amount, 2)
        })
        
        price = close_p
    
    df = pd.DataFrame(records)
    df['date'] = pd.to_datetime(df['date'])
    return df

def get_stock_daily(code: str, days: int = 120, use_mock: bool = False) -> pd.DataFrame:
    """获取股票日K线数据
    
    Args:
        code: 股票代码
        days: 获取天数
        use_mock: 是否使用mock数据（网络不可用时自动降级）
    """
    # 优先从缓存加载
    cached = _load_cached(code)
    if cached is not None and not cached.empty:
        return cached
    
    if use_mock:
        return _generate_mock_data(code, days)
    
    errors = []

    # 数据源1: 东方财富
    try:
        end = datetime.now().strftime('%Y%m%d')
        start = (datetime.now() - timedelta(days=days*2)).strftime('%Y%m%d')
        df = _retry_get(ak.stock_zh_a_hist, symbol=code, period="daily",
                         start_date=start, end_date=end, adjust="qfq")
        if not df.empty:
            df = _normalize_columns(df)
            _cache_data(code, df)
            return df
    except Exception as e:
        errors.append(f"eastmoney")

    # 数据源2: 腾讯股票
    try:
        df = _retry_get(ak.stock_zh_a_hist_tx, symbol=code, adjust="qfq")
        if not df.empty:
            df = _normalize_columns(df)
            _cache_data(code, df)
            return df
    except Exception as e:
        errors.append(f"tencent")
    
    # 所有数据源都失败，降级到mock
    print(f"⚠️ 网络不可用({code})，使用模拟数据演示")
    return _generate_mock_data(code, days)

def _cache_data(code: str, df: pd.DataFrame):
    """缓存数据"""
    cache_file = os.path.join(CACHE_DIR, f"{code}.pkl")
    df.to_pickle(cache_file)

def _load_cached(code: str) -> pd.DataFrame:
    """加载缓存（只返回180天内数据）"""
    cache_file = os.path.join(CACHE_DIR, f"{code}.pkl")
    if os.path.exists(cache_file):
        df = pd.read_pickle(cache_file)
        cutoff = datetime.now() - timedelta(days=180)
        df = df[df['date'] >= cutoff]
        if not df.empty:
            return df
    return None

def get_realtime_quote(codes: list) -> dict:
    """获取实时行情（真实数据或mock）"""
    try:
        df = ak.stock_zh_a_spot_em()
        df = df[df['代码'].isin(codes)]
        result = {}
        for _, row in df.iterrows():
            result[row['代码']] = {
                'name': row['名称'],
                'price': float(row['最新价']),
                'change': float(row['涨跌幅']),
                'volume': float(row['成交量']),
                'amount': float(row['成交额'])
            }
        return result
    except Exception:
        # 降级到mock
        result = {}
        for code in codes:
            base = MOCK_PRICES.get(code, 10.0)
            result[code] = {
                'name': code,
                'price': base,
                'change': random.uniform(-3, 3),
                'volume': random.randint(1000000, 10000000),
                'amount': random.randint(5000000, 50000000)
            }
        return result

def warmup_cache(codes: list, days: int = 120):
    """预热缓存（批量获取数据）"""
    results = {}
    for code in codes:
        print(f"获取 {code}...", end=" ", flush=True)
        df = get_stock_daily(code, days)
        if not df.empty:
            print(f"✅ {len(df)}条")
            results[code] = df
        else:
            print("❌ 失败")
    return results

if __name__ == "__main__":
    print("测试数据获取（演示模式）...")
    for code in ['688318', '688210', '603220']:
        df = get_stock_daily(code, 60)
        if not df.empty:
            last = df.iloc[-1]
            print(f"  {code}: ¥{last['close']} ({last['date'].strftime('%Y-%m-%d')})")
