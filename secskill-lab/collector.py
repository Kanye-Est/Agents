"""本地 mock 外传接收端（仅 127.0.0.1），用于观测恶意 skill 是否把数据偷传出去。
受控研究用：模拟“攻击者服务器”，只在本机监听、把收到的内容记到内存列表。
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


def start_collector(port: int = 8799):
    """启动一个后台 mock 接收端，返回 (captured_list, shutdown_fn)。"""
    captured = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8", "replace")
            try:
                data = json.loads(body)
            except Exception:
                data = body
            captured.append(data)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ok":true}')

        def log_message(self, *args):
            pass  # 静音访问日志

    server = HTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return captured, server.shutdown
