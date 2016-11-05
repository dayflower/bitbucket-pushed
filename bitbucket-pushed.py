import logging
import sys
import os.path
import subprocess
import json

def handler(environ):
    if environ.get('HTTP_X_EVENT_KEY', '') != 'repo:push':
        return

    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except (ValueError):
        request_body_size = 0

    request_body = environ['wsgi.input'].read(request_body_size)
    body = json.loads(request_body)

    change = body['push']['changes'][0]
    commit = change['new']
    target = commit['target']
    if commit['type'] != 'branch' or target['type'] != 'commit':
        return

    repository = body['repository']['full_name']
    branch = commit['name']
    date = target['date']
    commit_id = target['hash']
    message = target['message']

    script = os.path.basename(environ['PATH_INFO'])
    if script == '':
        script = 'pushed'
    script = os.path.abspath(script)

    args = ( script, repository, branch, commit_id, date, message )

    logging.info('execute "%s" "%s" "%s" "%s" "%s" "%s"' % args)

    try:
        subprocess.call(args, shell=False)
    except OSError as e:
        logging.warning('failed to execute %s (%s)' % (script, e))

def application(environ, start_response):
    try:
        handler(environ)
    except Exception as e:
        logging.warning('failed to handle (%s)' % (e))

    start_response('204 No Content', [])
    return ''

from wsgiref.simple_server import make_server

def main():
    logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] [%(levelname)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    port = int(sys.argv[1]) if sys.argv[1:] else 8000

    httpd = make_server('', port, application)

    sa = httpd.socket.getsockname()
    print "Serving on", sa[0], "port", sa[1], "..."
    httpd.serve_forever()

if __name__ == '__main__':
    main()
