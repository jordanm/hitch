from htmlentitydefs import codepoint2name
from re import compile
from uuid import uuid4

from django.conf.urls.defaults import url
from django.views.static import serve as serve_static_files
from jinja2.filters import escape as _escape_html

def choices(choices, capitalize=True):
    values = []
    for choice in choices or ():
        choice = str(choice)
        values.append((choice, (choice.capitalize() if capitalize else choice)))
    else:
        return tuple(values)
    
def escape_html(value):
    return unicode(_escape_html(unicode(value)))

PLURALIZATION_TOKENS = {
    'is': 'are',
    'was': 'were',
}
PLURALIZATION_RULES = (
    (compile(r'ife$'), compile(r'ife$'), 'ives'),
    (compile(r'eau$'), compile(r'eau$'), 'eaux'),
    (compile(r'lf$'), compile(r'lf$'), 'lves'),
    (compile(r'[sxz]$'), compile(r'$'), 'es'),
    (compile(r'[^aeioudgkprt]h$'), compile(r'$'), 'es'),
    (compile(r'(qu|[^aeiou])y$'), compile(r'y$'), 'ies'),
)

def pluralize(word):
    try:
        return PLURALIZATION_TOKENS[word]
    except KeyError:
        for pattern, target, replacement in PLURALIZATION_RULES:
            if pattern.search(word):
                return target.sub(replacement, word)
        else:
            return word + 's'
        
def static_serve_url(path, root):
    return url(r'^%s(?P<path>.*)$' % path.lstrip('/'), serve_static_files, {'document_root': root})

def uniqid():
    return str(uuid4()).replace('-', '')