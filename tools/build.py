import sys
src = open(sys.argv[1]).read()
i = src.index('<div id="app">')
head, body = src[:i], src[i:]
out = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
       + head + '</head>\n<body>\n' + body + '</body>\n</html>\n')
open(sys.argv[2], 'w').write(out)
