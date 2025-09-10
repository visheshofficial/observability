import http.server
import random
from prometheus_client import Counter, start_http_server, Summary
COUNTER = Counter('hello_requests_total', 'Total number of hello requests')
EXCEPTION_COUNTER = Counter('hello_exceptions_total', 'Total number of exceptions in hello handler')


class HelloHandler(http.server.BaseHTTPRequestHandler):
    REQUEST_TIME = Summary('hello_request_processing_seconds', 'Time spent processing hello requests')
    

    @REQUEST_TIME.time()
    def do_GET(self):
        if self.path == '/hello':
            COUNTER.inc()
            with EXCEPTION_COUNTER.count_exceptions():
                if random.random() < 0.3:
                    raise Exception("Random failure!")

            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Hello, World!')
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    start_http_server(8000, addr="0.0.0.0")
    server_address = ('0.0.0.0', 8080)
    httpd = http.server.HTTPServer(server_address, HelloHandler)
    print("Starting server on port 8080...")
    httpd.serve_forever()