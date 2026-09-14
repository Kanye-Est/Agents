#!/usr/bin/env python3
import argparse, http.server, json, os, pathlib, signal, time
p=argparse.ArgumentParser()
p.add_argument('--stage',required=True)
a=p.parse_args()
control=pathlib.Path(a.stage)/'control'
requests=(control/'osv-requests.jsonl').open('x')
class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        length=int(self.headers.get('Content-Length','0'))
        if not 0 <= length <= 65536:
            self.send_error(413)
            return
        body=self.rfile.read(length)
        row={'time_ns':time.time_ns(),'client':list(self.client_address),'method':'POST','path':self.path,'body_utf8':body.decode('utf8',errors='replace'),'status':503,'meaning':'Scanner unavailable in the isolated rig; no clean verdict is supplied.'}
        requests.write(json.dumps(row,ensure_ascii=False)+'\n')
        requests.flush()
        answer=b'{"error":"OSV unavailable in isolated rig; no scan verdict"}\n'
        self.send_response(503)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(answer)))
        self.send_header('Connection','close')
        self.end_headers()
        self.wfile.write(answer)
    def log_message(self,*args):
        pass
server=http.server.HTTPServer(('127.0.0.1',4874),Handler)
ready={'pid':os.getpid(),'ready_ns':time.time_ns(),'bind':['127.0.0.1',4874],'response_status':503,'no_upstream_requests':True}
with (control/'osv-ready.json').open('x') as f:
    json.dump(ready,f,indent=2)
    f.write('\n')
server.serve_forever(poll_interval=0.2)
