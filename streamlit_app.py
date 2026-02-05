import streamlit as st
import streamlit.components.v1 as components
import os
import json
from datetime import datetime, timedelta
import find_similar_patterns
import repair_chart

# 设置页面配置
st.set_page_config(
    page_title="Bitcoin 智能对比系统",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS 优化界面
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #f7931a;
        color: white;
    }
    .stDateInput input {
        background-color: #262730;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("₿ Bitcoin 历史形态智能搜索系统")
st.markdown("---")

# 侧边栏设置
with st.sidebar:
    st.header("🔍 搜索参数设置")
    
    # 获取当前最后数据的时间
    data_file = 'btc_1h_ohlc.json'
    last_date = datetime.now()
    if os.path.exists(data_file):
        with open(data_file, 'r') as f:
            data = json.load(f)
            if data:
                last_date = datetime.fromtimestamp(data[-1]['time'])

    st.info(f"💾 当前本地数据量: {len(data) if os.path.exists(data_file) else 0} 小时")
    
    # 模式选择
    search_mode = st.radio("选择搜索起点", ["今日凌晨 (默认)", "自定义历史日期"])
    
    selected_date = last_date.date()
    selected_time = last_date.time()
    
    if search_mode == "自定义历史日期":
        selected_date = st.date_input("选择起始日期", value=last_date.date() - timedelta(days=1))
        selected_time = st.time_input("选择起始具体小时", value=datetime.strptime("00:00", "%H:%M").time())
    
    pattern_length = st.slider("模式长度 (K 线数量/小时)", min_value=6, max_value=168, value=24)
    
    search_btn = st.button("🚀 开始历史深度搜索")

# 主界面逻辑
if search_btn:
    with st.spinner('🧠 正在调动 Python 引擎进行全量历史 DTW 相似度匹配...'):
        try:
            # 格式化时间字符串
            start_str = f"{selected_date.strftime('%Y-%m-%d')} {selected_time.strftime('%H:%M')}"
            
            # 执行核心搜索逻辑
            stats = find_similar_patterns.do_search(start_str=start_str, length=pattern_length)
            
            st.success(f"✅ 搜索完成！胜率: {stats['win_rate']}% | 平均回报: {stats['avg_return']}%")
            
        except Exception as e:
            st.error(f"❌ 搜索过程中出错: {e}")

# 展示图表
chart_file = 'tradingview_1h_chart.html'
if os.path.exists(chart_file):
    with open(chart_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
        
    # 注意：Streamlit 的 components.html 会在一个 iframe 中运行
    # 如果 HTML 中有外部脚本引用，需要确保跨域允许（目前使用的 unpkg 没问题）
    components.html(html_content, height=1200, scrolling=True)
else:
    st.warning("🏮 尚未生成图表数据，请在侧边栏点击“开始搜索”按钮触发初次计算。")

# 页脚
st.markdown("---")
st.caption("基于 FastDTW 算法与最近 3 年比特币 1h 历史数据构建。本工具仅供技术参考，不构成投资建议。")
