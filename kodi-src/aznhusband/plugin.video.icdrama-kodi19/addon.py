import sys
from urllib import parse
from lib import actions

if __name__ == '__main__':
    qs = sys.argv[2]
    kargs = dict((k, parse.unquote(v))for k, v in parse.parse_qsl(qs.lstrip('?')))

    action_name = kargs.pop('action', 'index') # popped
    if action_name in actions.actions:
        action_func = getattr(actions, action_name)
        action_func(**kargs)
    else:
        raise Exception('Invalid action: %s' % action_name)


