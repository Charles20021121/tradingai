import json
import os

def regenerate_html():
    """
    重新从数据文件生成整个 HTML 页面。
    智能看板版：根据涨跌胜率大小，自动显示占优的情绪概率。
    """
    data_path = 'btc_1h_ohlc.json'
    sim_path = 'similarity_results.json'
    
    if not os.path.exists(data_path):
        print(f"❌ 找不到数据文件: {data_path}")
        return
        
    with open(data_path, 'r') as f:
        ohlc_data = json.load(f)
        
    sim_meta = {'target_time': 0, 'target_date': '实时数据', 'pattern_length': 24, 'stats': {}, 'results': []}
    if os.path.exists(sim_path):
        with open(sim_path, 'r') as f:
            sim_meta = json.load(f)

    stats = sim_meta.get('stats', {})
    win_rate = stats.get('win_rate', 0)
    avg_return = stats.get('avg_return', 0)
    max_up = stats.get('max_up', 0)
    max_down = stats.get('max_down', 0)
    
    target_date = sim_meta.get('target_date', '实时数据')
    pattern_length = sim_meta.get('pattern_length', 24)

    # --- 智能情绪逻辑 ---
    loss_rate = round(100 - win_rate, 2)
    if win_rate >= 50:
        sentiment_label = "历史上涨概率 (看多趋势)"
        sentiment_value = win_rate
        sentiment_color = "#f7931a" # 橙色
        sentiment_gradient = "linear-gradient(90deg, #f7931a, #ffb347)"
    else:
        sentiment_label = "历史下跌概率 (看空趋势)"
        sentiment_value = loss_rate
        sentiment_color = "#ef5350" # 红色
        sentiment_gradient = "linear-gradient(90deg, #ef5350, #ff5252)"

    avg_return_str = f"{'+' if avg_return > 0 else ''}{avg_return}%"
    avg_color = "green" if avg_return >= 0 else "red"

    # 生成 HTML
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bitcoin 智能对比系统 - 占优情绪版</title>
    <script src="https://unpkg.com/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, sans-serif;
            background: linear-gradient(135deg, #1a1a2e, #16213e, #0f3460);
            min-height: 100vh;
            color: #fff;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        header {{ text-align: center; padding: 10px 0; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; }}
        h1 {{ font-size: 1.8rem; background: linear-gradient(90deg, #f7931a, #ffb347); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
        
        .toolbar {{ display: flex; gap: 10px; align-items: center; }}
        .btn {{ 
            padding: 8px 16px; border-radius: 8px; border: 1px solid #f7931a; background: transparent; 
            color: #f7931a; font-weight: bold; cursor: pointer; transition: 0.3s; font-size: 0.9rem;
        }}
        .btn:hover {{ background: rgba(247, 147, 26, 0.1); }}
        .btn.active {{ background: #f7931a; color: #000; }}
        
        .info-box {{ 
            background: rgba(38, 166, 154, 0.1); 
            border: 1px solid rgba(38, 166, 154, 0.3); 
            border-radius: 8px; padding: 10px; margin-bottom: 20px; text-align: center; font-size: 0.85rem;
        }}

        /* 统计看板 */
        .dashboard {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .dash-card {{
            background: rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 15px; border: 1px solid rgba(255, 255, 255, 0.1); text-align: center;
        }}
        .dash-label {{ color: #aaa; font-size: 0.8rem; margin-bottom: 5px; }}
        .dash-value {{ font-size: 1.5rem; font-weight: bold; }}
        
        .progress-container {{ width: 100%; background: rgba(255,255,255,0.1); border-radius: 10px; height: 8px; margin-top: 8px; overflow: hidden; }}
        .progress-bar {{ height: 100%; background: {sentiment_gradient}; transition: 1s ease-out; }}

        .chart-container {{ background: rgba(22, 33, 62, 0.8); border-radius: 16px; padding: 20px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 20px; position: relative; }}
        #chart {{ width: 100%; height: 500px; }}
        
        #selection-tip {{
            position: absolute; top: 10px; right: 10px; z-index: 20;
            background: rgba(247, 147, 26, 0.9); color: #000; padding: 8px 15px; border-radius: 5px;
            font-weight: bold; font-size: 0.85rem; display: none; pointer-events: none;
        }}

        .legend {{ position: absolute; top: 30px; left: 30px; z-index: 10; background: rgba(0, 0, 0, 0.6); padding: 10px; border-radius: 8px; font-size: 0.75rem; }}
        .legend-item {{ display: flex; align-items: center; margin-bottom: 4px; }}
        .legend-color {{ width: 10px; height: 10px; border-radius: 2px; margin-right: 8px; }}

        .similarity-panel {{ background: rgba(22, 33, 62, 0.8); border-radius: 16px; padding: 20px; border: 1px solid rgba(255, 255, 255, 0.1); }}
        .similarity-list {{ 
            display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; margin-top: 15px; max-height: 400px; overflow-y: auto; padding-right: 5px;
        }}
        .similarity-item {{ background: rgba(255, 255, 255, 0.03); border-radius: 10px; padding: 10px; border: 1px solid rgba(255, 255, 255, 0.1); cursor: pointer; transition: 0.2s; position: relative; }}
        .similarity-item:hover {{ border-color: #f7931a; background: rgba(247, 147, 26, 0.1); }}
        .similarity-item.active {{ border-color: #f7931a; background: rgba(247, 147, 26, 0.2); }}
        .sim-date {{ color: #f7931a; font-weight: bold; font-size: 0.75rem; }}
        
        .loading-overlay {{ 
            position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
            background: rgba(0,0,0,0.7); display: none; justify-content: center; align-items: center; z-index: 999;
            flex-direction: column; gap: 15px;
        }}
        .spinner {{ width: 50px; height: 50px; border: 5px solid #f7931a55; border-top: 5px solid #f7931a; border-radius: 50%; animation: spin 1s linear infinite; }}
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}

        .green {{ color: #26a69a; }} .red {{ color: #ef5350; }} .orange {{ color: #f7931a; }}
    </style>
</head>
<body>
    <div class="loading-overlay" id="loading">
        <div class="spinner"></div>
        <div style="font-weight:bold; color:#f7931a">🧠 正在进行 DTW 全量历史搜索...</div>
    </div>

    <div class="container">
        <header>
            <h1>₿ Bitcoin 智能对比系统</h1>
            <div class="toolbar">
                <button class="btn" id="btn-select">🖱️ 画面点选范围</button>
                <button class="btn" onclick="location.reload()">🔄 刷新数据</button>
            </div>
        </header>
        
        <div class="info-box">
            🎯 当前基准：<strong>{target_date}</strong> | 周期：<strong>{pattern_length}h</strong>
        </div>

        <div class="dashboard">
            <div class="dash-card">
                <div class="dash-label">{sentiment_label}</div>
                <div class="dash-value" style="color: {sentiment_color}">{sentiment_value}%</div>
                <div class="progress-container"><div class="progress-bar" style="width: {sentiment_value}%"></div></div>
            </div>
            <div class="dash-card">
                <div class="dash-label">平均预期回报</div>
                <div class="dash-value {avg_color}">{avg_return_str}</div>
            </div>
            <div class="dash-card">
                <div class="dash-label">波动极限 (跌~涨)</div>
                <div style="display: flex; justify-content: space-around; font-size: 1.1rem; font-weight:bold; margin-top:5px">
                    <span class="red">{max_down}%</span> ··· <span class="green">{max_up}%</span>
                </div>
            </div>
        </div>

        <div class="chart-container">
            <div id="selection-tip">请选择一个起点蜡烛...</div>
            <div id="chart"></div>
        </div>
        
        <div class="similarity-panel">
            <h3>🔍 相似剧本列表 ({len(sim_meta['results'])} 项)</h3>
            <div class="similarity-list" id="sim-list"></div>
        </div>
    </div>
    
    <script>
        const ohlcData = {json.dumps(ohlc_data)};
        const simMeta = {json.dumps(sim_meta)};
        const similarityData = simMeta.results;
        const targetTime = simMeta.target_time;
        const patternLength = simMeta.pattern_length || 24;

        const chart = LightweightCharts.createChart(document.getElementById('chart'), {{
            layout: {{ background: {{ color: 'transparent' }}, textColor: '#DDD' }},
            grid: {{ vertLines: {{ color: 'rgba(255,255,255,0.05)' }}, horzLines: {{ color: 'rgba(255,255,255,0.05)' }} }},
            timeScale: {{ timeVisible: true, borderColor: '#444' }},
            rightPriceScale: {{ borderColor: '#444' }}
        }});

        const candleSeries = chart.addCandlestickSeries({{
            upColor: '#26a69a', downColor: '#ef5350', borderVisible: false,
            wickUpColor: '#26a69a', wickDownColor: '#ef5350'
        }});
        candleSeries.setData(ohlcData);

        const ghostSeries = chart.addCandlestickSeries({{
            upColor: 'rgba(247, 147, 26, 0.6)', downColor: 'rgba(255, 255, 255, 0.2)',
            borderVisible: true, borderColor: '#f7931a', wickUpColor: '#f7931a', wickDownColor: '#f7931a',
            priceLineVisible: false, lastValueVisible: false,
        }});
        const futureLineSeries = chart.addLineSeries({{ color: '#2196F3', lineWidth: 3, lineStyle: 2, priceLineVisible: false }});

        let selectionMode = false;
        let selectStartTime = null;
        const tipEl = document.getElementById('selection-tip');
        const loadEl = document.getElementById('loading');

        document.getElementById('btn-select').onclick = () => {{
            selectionMode = !selectionMode;
            document.getElementById('btn-select').classList.toggle('active', selectionMode);
            tipEl.style.display = selectionMode ? 'block' : 'none';
            selectStartTime = null;
            tipEl.innerText = "请点击图表上的一根蜡烛作为【起点】";
        }};

        chart.subscribeClick(param => {{
            if (!selectionMode || !param.time) return;
            if (!selectStartTime) {{
                selectStartTime = param.time;
                tipEl.innerText = "起点已选。请点击【结束点】蜡烛...";
            }} else {{
                const selectEndTime = param.time;
                const length = Math.round((selectEndTime - selectStartTime) / 3600);
                if (length <= 0) {{ alert("选区无效！"); return; }}
                
                loadEl.style.display = 'flex';
                fetch('/api/search', {{
                    method: 'POST',
                    body: JSON.stringify({{ startTime: selectStartTime, length: length }})
                }}).then(() => location.reload());
            }}
        }});

        similarityData.forEach((item, idx) => {{
            const div = document.createElement('div');
            div.className = 'similarity-item';
            div.innerHTML = `<div class="sim-date">${{item.date}}</div><div style="font-size:0.65rem">相似度: ${{Math.max(0, 100-item.distance*10).toFixed(1)}}% | 后果: ${{item.future_change>0?'+':''}}${{item.future_change.toFixed(2)}}%</div>`;
            div.onclick = () => {{
                const curIdx = ohlcData.findIndex(d => d.time === targetTime);
                const offset = ohlcData[curIdx].open - item.ohlc[0].open;
                const ghostData = item.ohlc.map((h, i) => ({{
                    time: ohlcData[curIdx].time + i * 3600, 
                    open: h.open + offset, high: h.high + offset, low: h.low + offset, close: h.close + offset
                }}));
                ghostSeries.setData(ghostData.slice(0, patternLength));
                futureLineSeries.setData(ghostData.map(d => ({{ time: d.time, value: d.close }})));
            }};
            document.getElementById('sim-list').appendChild(div);
        }});
    </script>
</body>
</html>
'''
    with open('tradingview_1h_chart.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ 智能情绪版已生成：自动显示主导概率（上涨/下跌）")

if __name__ == "__main__":
    regenerate_html()
