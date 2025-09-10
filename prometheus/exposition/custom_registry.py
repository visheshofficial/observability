from prometheus_client import CollectorRegistry, Counter, generate_latest, start_http_server, make_asgi_app

# Create a new registry
my_registry = CollectorRegistry()

# Register your metrics with it
REQUESTS = Counter("hello_requests_total", "Total hello requests", registry=my_registry)

# Start an HTTP server serving only this registry
from prometheus_client import start_http_server, make_wsgi_app
from wsgiref.simple_server import make_server

app = make_wsgi_app(my_registry)
httpd = make_server('', 8000, app)
httpd.serve_forever()



'''
the above code exposes metrics at http://localhost:8000/metrics with output like:

# HELP hello_requests_total Total hello requests
# TYPE hello_requests_total counter
hello_requests_total 0.0
# HELP hello_requests_created Total hello requests
# TYPE hello_requests_created gauge
hello_requests_created 1.7568005416254878e+09
'''