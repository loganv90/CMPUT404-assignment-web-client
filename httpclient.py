#!/usr/bin/env python3
# coding: utf-8
# Copyright 2023 Logan Vaughan, Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it


import sys
import socket
import re
import urllib.parse
import json


def help():
    print("httpclient.py [GET/POST] [URL] [DATA]\n")


class HTTPResponse(object):

    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

    def __repr__(self): 
        return f"<HTTPResponse code: {self.code}, body: {self.body}>"


class HTTPClient(object):

    def get_host_port(self, url):
        parse = urllib.parse.urlparse(url)
        host = parse.netloc
        port = 80
        path = '/'
        scheme = 'HTTP/1.1'

        if parse.path:
            path = parse.path
        
        if ':' in host:
            split_host = parse.netloc.split(':')
            host = split_host[0]
            port = int(split_host[1])

        if parse.scheme != 'http':
            scheme = parse.scheme

        return host, port, path, parse.netloc, scheme

    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        return None

    def get_code(self, data):
        response_info = data[0].split(' ')
        if len(response_info) < 3:
            return 500
        return int(response_info[1])

    def get_headers(self, data):
        return data[0].decode('utf-8').split('\r\n')

    def get_body(self, data, charset):
        if len(data) < 2:
            return ''
        return data[1].decode(charset)

    def get_charset(self, data):
        charset = 'utf-8'
        for header in data:
            if header.startswith('Content-Type'):
                for item in header.split(' '):
                    if item.startswith('charset='):
                        charset = item.split("charset=")[1]
        return charset

    def get_request_body(self, data):
        if type(data) is dict:
            l = []
            for k, v in data.items():
                l.append(f'{k}={v}')
            return '&'.join(l)
        return ''

    def sendall(self, data):
        self.socket.sendall(data.encode('utf-8'))

    def close(self):
        self.socket.close()

    def recvall(self, host, port, request):
        self.connect(host, port)
        self.sendall(request)
        full_data = bytearray()

        while True:
            data = self.socket.recv(2048)
            if data:
                full_data.extend(data)
            else:
                break
            
        self.close()
        return full_data

    def GET(self, url, args=None):
        host, port, path, netloc, scheme = self.get_host_port(url)

        request = f'GET {path} {scheme}\r\nHost: {netloc}\r\nAccept: */*\r\nConnection: close\r\n\r\n'
        full_data = self.recvall(host, port, request)
        split_data = full_data.split(b'\r\n\r\n', 1)
        
        headers = self.get_headers(split_data)
        response_code = self.get_code(headers)
        charset = self.get_charset(headers)
        body = self.get_body(split_data, charset)

        return HTTPResponse(response_code, body)

    def POST(self, url, args=None):
        host, port, path, netloc, scheme = self.get_host_port(url)
        request_body = self.get_request_body(args)

        request = f'POST {path} {scheme}\r\nHost: {netloc}\r\nAccept: */*\r\nConnection: close\r\n'
        request += f'Content-Type: application/x-www-form-urlencoded\r\nContent-Length: {len(request_body)}\r\n\r\n{request_body}'
        full_data = self.recvall(host, port, request)
        split_data = full_data.split(b'\r\n\r\n', 1)
        
        headers = self.get_headers(split_data)
        response_code = self.get_code(headers)
        charset = self.get_charset(headers)
        body = self.get_body(split_data, charset)

        return HTTPResponse(response_code, body)

    def command(self, url, command="GET", args=None):
        if args is not None:
            try:
                args = json.loads(args)
            except Exception as _:
                args = None

        if (command == "POST"):
            return self.POST(url, args)
        else:
            return self.GET(url, args)
    

if __name__ == "__main__":
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 2):
        print(HTTPClient().command(sys.argv[1]))
    elif (len(sys.argv) == 3):
        print(HTTPClient().command(sys.argv[2], sys.argv[1]))
    else:
        print(HTTPClient().command(sys.argv[2], sys.argv[1], sys.argv[3]))
