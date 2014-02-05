#! /usr/bin/env python
__author__ = 'jag'
def myapp(environ, start_response):
    start_response('200 OK', [('Location', '/summary?'),('Content-Type', 'text/html')])
    return ["Redirecting...\n"]

if __name__ == '__main__':
    from flup.server.fcgi import WSGIServer
    WSGIServer(myapp).run()

