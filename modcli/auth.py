import socket
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import parse

import requests

from modcli import __version__


def login(username: str, password: str, url: str):
    result = requests.post('{0}/users/tokens'.format(url), json={
        'user_id': username,
        'password': password,
        'agent': 'modcli:{0}'.format(__version__),
    })
    if result.status_code != 200:
        raise Exception('Error: {0}'.format(result.json()['error-message']))
    return result.json()['message'].strip()


def get_open_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port


def login_sso(url: str):
    server_host = 'localhost'
    server_port = get_open_port()
    local_server = 'http://{0}:{1}'.format(server_host, server_port)

    class SSORequestHandler(BaseHTTPRequestHandler):
        token = ''

        def do_HEAD(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

        def do_GET(self):
            response = self.handle_http(200)
            _, _, _, query, _ = parse.urlsplit(self.path)
            result = parse.parse_qs(query)
            tokens = result.get('token', None)
            SSORequestHandler.token = tokens[0] if len(tokens) > 0 else None
            self.wfile.write(response)

        def handle_http(self, status_code):
            self.send_response(status_code)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            content = '''
            <html><head><title>Success</title></head>
            <body>Authentication successful! This browser window can be closed.</body></html>
            '''
            return bytes(content, 'UTF-8')

        def log_message(self, format, *args):
            pass

    httpd = HTTPServer((server_host, server_port), SSORequestHandler)
    httpd.timeout = 30

    webbrowser.open('{0}/users/tokens_sso?local_url={1}'.format(url, local_server))

    try:
        httpd.handle_request()
    except KeyboardInterrupt:
        pass

    token = SSORequestHandler.token
    if not token:
        raise Exception('Authentication failed!')
    return token
