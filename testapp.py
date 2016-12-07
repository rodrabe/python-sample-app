
def application(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [b"Hello from Brant's gunicorn WSGI application!"]
