import http.server
import socketserver
import json
import urllib.parse
import os
import sys
from datetime import datetime

# 将当前目录加入路径以便导入我们的模块
sys.path.append(os.getcwd())

import find_similar_patterns
from repair_chart import regenerate_html

PORT = 8000

class SearchHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/search':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = json.loads(post_data)
            
            start_time = params.get('startTime')
            length = params.get('length', 24)
            
            # 转换时间为字符串格式 YYYY-MM-DD HH:MM
            dt = datetime.fromtimestamp(start_time)
            start_str = dt.strftime('%Y-%m-%d %H:%M')
            
            print(f"🚀 收到前端请求: 起点 {start_str}, 长度 {length}h")
            
            try:
                # 执行搜索
                stats = find_similar_patterns.do_search(start_str=start_str, length=length)
                
                # 返回成功
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    "status": "success",
                    "stats": stats
                }
                self.wfile.write(json.dumps(response).encode())
            except Exception as e:
                print(f"❌ 搜索失败: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        # 默认返回图表页面
        if self.path == '/' or self.path == '/index.html':
            self.path = '/tradingview_1h_chart.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

print(f"📡 交互式服务器正在启动: http://localhost:{PORT}")
print(f"👉 请在浏览器打开以上地址，并在图表上【点击选择】开始对比")

with socketserver.TCPServer(("", PORT), SearchHandler) as httpd:
    httpd.serve_forever()
