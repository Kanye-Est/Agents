"""本地 mock 外传接收端（仅 127.0.0.1），用于观测恶意 skill 是否把数据偷传出去。
受控研究用：模拟“攻击者服务器”，只在本机监听、把收到的内容记到内存列表。
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


def _start_collector_server(port: int):
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
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def shutdown():
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    return captured, shutdown, server


def start_collector(port: int = 8799):
    """启动一个后台 mock 接收端，返回 (captured_list, shutdown_fn)。"""
    captured, shutdown, _ = _start_collector_server(port)
    return captured, shutdown


def start_collector_endpoint(port: int = 0):
    """Start on an available loopback port and also return its exact URL."""
    captured, shutdown, server = _start_collector_server(port)
    bound_port = int(server.server_address[1])
    return captured, shutdown, f"http://127.0.0.1:{bound_port}/collect"
