
import base64
import json

import click

try:
    from http.server import HTTPServer, BaseHTTPRequestHandler, HTTPStatus
except:
    from HTTPServer import HTTPServer, BaseHTTPRequestHandler


try:
    from urllib.parse import urlparse, parse_qs
except ImportError:
    from urlparse import urlparse
    from urllib import parse_qs

from alertaclient.exceptions import AuthError

SUCCESS_MESSAGE = """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
        "http://www.w3.org/TR/html4/strict.dtd">
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html;charset=utf-8">
        <title>Alerta Login</title>
    </head>
    <body>
        <h1>Authorization success!</h1>
        <p>Please close the web browser and return to the terminal.</p>
    </body>
</html>
"""


class HTTPServerHandler(BaseHTTPRequestHandler):

    def __init__(self, request, address, server, xsrf_token):
        self.xsrf_token = xsrf_token
        self.access_token = None
        super().__init__(request, address, server)

    def do_GET(self):
        try:
            qp = parse_qs(urlparse(self.path).query)
        except Exception as e:
            raise AuthError(e)

        if 'state' in qp and qp['state'][0] != self.xsrf_token:
            raise AuthError('CSRF token is invalid. Please try again.')
        if 'code' in qp:
            self.server.access_token = qp['code'][0]
        elif 'error' in qp:
            raise AuthError(qp['error'])

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes(SUCCESS_MESSAGE, 'UTF-8'))

    def log_message(self, format, *args):
        return


class TokenHandler:

    def get_access_token(self, xsrf_token):
        server_address = ('', 9004)
        httpd = HTTPServer(server_address, lambda request, address, server: HTTPServerHandler(request, address, server, xsrf_token))
        httpd.handle_request()
        return httpd.access_token


class Jwt:

    def parse(self, jwt):
        payload = jwt.split('.')[1]
        padding = '=' * (4 - (len(payload) % 4))
        decoded = base64.urlsafe_b64decode(payload + padding)
        return json.loads(decoded.decode('utf-8'))
