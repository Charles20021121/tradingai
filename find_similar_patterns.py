"""
相似蜡烛走势搜索工具
在历史数据中找到与目标模式最相似的走势
"""
import json
import numpy as np
from fastdtw import fastdtw
from datetime import datetime

def simple_distance(a, b):
    """简单欧几里得距离"""
    return abs(a - b)

def load_data():
    """加载 OHLC 数据"""
    with open('btc_1h_ohlc.json', 'r') as f:
        data = json.load(f)
    print(f"✅ 加载了 {len(data)} 条数据")
    return data

def normalize(arr):
    """归一化到 0-1 范围（保持形态）"""
    arr = np.array(arr, dtype=float)
    min_val, max_val = arr.min(), arr.max()
    if max_val - min_val == 0:
        return arr * 0
    return (arr - min_val) / (max_val - min_val)

def extract_pattern(data, start_idx, length=24):
    """提取一段蜡烛图数据作为 pattern"""
    end_idx = start_idx + length
    if end_idx > len(data):
        return None
    
    segment = data[start_idx:end_idx]
    # 使用收盘价作为主要对比依据
    closes = [c['close'] for c in segment]
    return normalize(closes)

def find_similar_patterns(data, target_start, pattern_length=24, top_n=10, min_gap=24):
    """
    在历史数据中找相似走势
    
    参数:
    - data: OHLC 数据
    - target_start: 目标模式的起始索引
    - pattern_length: 模式长度（默认24小时=1天）
    - top_n: 返回最相似的前N个
    - min_gap: 相似结果之间的最小间隔
    """
    # 提取目标模式
    target_pattern = extract_pattern(data, target_start, pattern_length)
    if target_pattern is None:
        print("❌ 无法提取目标模式")
        return []
    
    target_time = datetime.fromtimestamp(data[target_start]['time'])
    print(f"🎯 目标模式: 从 {target_time} 开始的 {pattern_length} 小时走势")
    print("🔍 正在搜索相似走势...")
    
    similarities = []
    
    # 滑动窗口搜索
    for i in range(0, len(data) - pattern_length):
        # 跳过目标模式附近的时间段
        if abs(i - target_start) < min_gap:
            continue
        
        pattern = extract_pattern(data, i, pattern_length)
        if pattern is None:
            continue
        
        # 使用 DTW 计算相似度
        distance, _ = fastdtw(target_pattern.tolist(), pattern.tolist(), dist=simple_distance)
        
        start_time = datetime.fromtimestamp(data[i]['time'])
        similarities.append({
            'index': i,
            'start_time': start_time,
            'distance': distance,
            'start_price': data[i]['close'],
            'end_price': data[i + pattern_length - 1]['close']
        })
    
    # 按距离排序（距离越小越相似）
    similarities.sort(key=lambda x: x['distance'])
    
    # 过滤掉太接近的结果
    filtered = []
    for s in similarities:
        is_close = any(abs(s['index'] - existing['index']) < min_gap for existing in filtered)
        if not is_close:
            filtered.append(s)
        if len(filtered) >= top_n:
            break
    
    return filtered

def display_results(results, data, pattern_length=24):
    """显示搜索结果"""
    print("\n" + "="*60)
    print("📊 最相似的走势:")
    print("="*60)
    
    for i, r in enumerate(results, 1):
        # 计算相似度百分比（距离转换）
        max_dist = 10  # 归一化后的最大距离估计
        similarity = max(0, 100 - (r['distance'] / max_dist * 100))
        
        # 计算该时段涨跌
        change = (r['end_price'] - r['start_price']) / r['start_price'] * 100
        change_str = f"+{change:.2f}%" if change > 0 else f"{change:.2f}%"
        
        # 查看该模式之后的走势（如果有数据）
        future_idx = r['index'] + pattern_length + 24  # 之后1天
        if future_idx < len(data):
            future_price = data[future_idx]['close']
            future_change = (future_price - r['end_price']) / r['end_price'] * 100
            future_str = f"+{future_change:.2f}%" if future_change > 0 else f"{future_change:.2f}%"
        else:
            future_str = "N/A"
        
        print(f"\n#{i} 相似度: {similarity:.1f}%")
        print(f"   📅 时间: {r['start_time'].strftime('%Y-%m-%d %H:00')}")
        print(f"   💰 期间涨跌: {change_str}")
        print(f"   🔮 之后24小时: {future_str}")

import argparse

def find_target_window(data, start_date=None, length=24):
    """
    根据日期或默认逻辑找到目标窗口。
    """
    if start_date:
        try:
            target_ts = int(datetime.strptime(start_date, '%Y-%m-%d %H:%M').timestamp())
            for i in range(len(data)-1, -1, -1):
                if data[i]['time'] <= target_ts:
                    # 确保有足够的长度
                    if i + length <= len(data):
                        return i, length
                    else:
                        print(f"⚠️ 从 {start_date} 开始的数据不足 {length} 小时，使用最后 {length} 小时")
                        return max(0, len(data) - length), length
            print(f"⚠️ 未找到 {start_date} 对应的数据点，使用默认 12am 窗口")
        except Exception as e:
            print(f"⚠️ 日期解析失败 ({e})，使用默认 12am 窗口")

    # 默认逻辑: 寻找最近的 00:00 (凌晨)
    now = datetime.fromtimestamp(data[-1]['time'])
    target_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    target_ts = int(target_date.timestamp())
    
    for i in range(len(data)-1, -1, -1):
        if data[i]['time'] <= target_ts:
            if i + length <= len(data):
                return i, length
            break
            
    # 如果找不到或数据不够，退回到最后 length 小时
    return max(0, len(data) - length), length

def do_search(start_str=None, length=24, top_n=200):
    """
    执行搜索的核心流：加载数据 -> 寻找窗口 -> DTW 搜索 -> 统计计算 -> 保存结果 -> 刷新页面
    """
    # 加载数据
    data = load_data()
    
    # 确定目标窗口
    target_start, pattern_length = find_target_window(data, start_str, length)
    
    print(f"🎯 目标模式: 从 {datetime.fromtimestamp(data[target_start]['time'])} 开始的 {pattern_length} 小时走势")

    # 搜索相似走势
    results = find_similar_patterns(
        data, 
        target_start=target_start,
        pattern_length=pattern_length,
        top_n=top_n, 
        min_gap=max(48, pattern_length * 2)
    )
    
    # 保存包含完整 OHLC 的结果
    output_results = []
    future_changes = []
    
    for r in results:
        match_end = r['index'] + pattern_length
        future_obs = max(24, pattern_length)
        future_end = min(len(data), match_end + future_obs)
        segment = data[r['index']:future_end]
        
        f_change = 0.0
        if future_end > match_end:
            f_change = (data[future_end-1]['close'] - data[match_end-1]['close']) / data[match_end-1]['close'] * 100
            future_changes.append(f_change)
            
        output_results.append({
            'time': int(r['start_time'].timestamp()),
            'date': r['start_time'].strftime('%Y-%m-%d %H:00'),
            'distance': float(r['distance']),
            'change': float((r['end_price'] - r['start_price']) / r['start_price'] * 100),
            'future_change': float(f_change),
            'ohlc': segment
        })
    
    # 统计学预测计算
    if future_changes:
        up_count = len([x for x in future_changes if x > 0])
        win_rate = (up_count / len(future_changes)) * 100
        avg_return = sum(future_changes) / len(future_changes)
        max_up = max(future_changes)
        max_down = min(future_changes)
        median_return = sorted(future_changes)[len(future_changes)//2]
    else:
        win_rate = avg_return = max_up = max_down = median_return = 0
        
    stats = {
        'count': len(future_changes),
        'win_rate': round(win_rate, 2),
        'avg_return': round(avg_return, 2),
        'max_up': round(max_up, 2),
        'max_down': round(max_down, 2),
        'median_return': round(median_return, 2)
    }
    
    with open('similarity_results.json', 'w') as f:
        json.dump({
            'target_time': int(data[target_start]['time']),
            'target_date': datetime.fromtimestamp(data[target_start]['time']).strftime('%Y-%m-%d %H:%M'),
            'pattern_length': pattern_length,
            'stats': stats,
            'results': output_results
        }, f)
    
    print(f"✅ 统计预测完成: 胜率 {stats['win_rate']}% | 平均回报 {stats['avg_return']}%")
    
    # 自动更新 HTML 页面
    try:
        from repair_chart import regenerate_html
        regenerate_html()
    except Exception as e:
        print(f"⚠️ 更新 HTML 失败: {e}")
        
    return stats

def main():
    parser = argparse.ArgumentParser(description='Bitcoin Pattern Finder')
    parser.add_argument('--start', type=str, help='起始时间 (YYYY-MM-DD HH:MM)')
    parser.add_argument('--length', type=int, default=24, help='对比模式长度 (小时)')
    args = parser.parse_args()
    
    do_search(args.start, args.length)

if __name__ == "__main__":
    main()
