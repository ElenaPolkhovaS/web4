"""Веб-додаток з маршрутізацією для 2-х сторінок"""
import urllib.parse
import mimetypes
import pathlib
import socket
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        # print(data)
        data_parse = urllib.parse.unquote_plus(data.decode())
        # print(data_parse)
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        print(data_dict)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

        # Відправити дані до Socket сервера
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.sendto(json.dumps(data_dict).encode('utf-8'), ('localhost', 5000))
        except Exception as e:
            print(f"Error sending data to Socket server: {e}")

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())


def run_http_server():
    server_address = ('', 3000)
    http = HTTPServer(server_address, HttpHandler)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


def echo_server(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        print(f"Socket server started on {host}:{port}")
        while True:
            data, addr = s.recvfrom(1024)
            print(f'Received from {addr}: {data}')
            try:
                message_dict = json.loads(data.decode('utf-8'))
                # Додаємо об'єкт до словника з використанням часу отримання як ключа
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                message_dict = {timestamp: message_dict}
                print(message_dict)
                # Зберігаємо у файл
                with open('storage/data.json', 'a') as file:
                    json.dump(message_dict, file, ensure_ascii=False)
                    file.write('\n')
            except json.JSONDecodeError:
                print("Error decoding JSON data from client")

if __name__ == '__main__':
    http_thread = threading.Thread(target=run_http_server)
    socket_thread = threading.Thread(target=echo_server, args=('', 5000))

    http_thread.start()
    socket_thread.start()

    http_thread.join()
    socket_thread.join()
