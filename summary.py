#! /usr/bin/env python
import subprocess
from mako.template import Template
from mako.lookup import TemplateLookup
from cgi import parse_qs, escape

def myapp(environ, start_response):
    try:
        d = parse_qs(environ['QUERY_STRING'])
        display = d.get('page_type',[''])[0]# Returns the first age value.
        display = escape(display)
    except:
        display = 'usr_list'

    lookup = TemplateLookup(directories=['/var/www/templates'], input_encoding='utf-8', output_encoding='utf-8')
    mytemplate = lookup.get_template("sidebar_temp.html")

    start_response('200 OK', [('Content-Type', 'text/html')])
    return [str(mytemplate.render(page_type=display))]

if __name__ == '__main__':
    from flup.server.fcgi import WSGIServer
    WSGIServer(myapp).run()
