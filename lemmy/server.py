#!/usr/bin/env python3
# coding=utf-8

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib import parse
import json


class MyHttpHander(BaseHTTPRequestHandler):

    def do_GET(self):
        print("client_address:" + repr(self.client_address))
        print("doGET_path:" + self.path)
        parse_result = parse.urlparse(self.path)
        print("result_path:" + str(parse_result.path))
        print("result_params:" + str(parse_result.params))
        print("result_query:" + str(parse.parse_qs(parse_result.query)))
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write("HELLO 测试".encode())

    def do_POST(self):
        print("doPOST_path:" + self.path)
        content_length = int(self.headers["content-length"])
        data = self.rfile.read(content_length)
        print("doPOST_data:" + str(data, encoding="utf-8"))
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        d = {'姓名': 'Tom', '年龄': 12}
        self.wfile.write(json.dumps(d).encode("utf-8"))


httpserver = ThreadingHTTPServer(("127.0.0.1", 8088), MyHttpHander)
print("serverport:", str(httpserver.server_port))
httpserver.serve_forever()
