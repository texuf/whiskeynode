

class TerminalType():
    NODE = 'node'
    LIST_OF_NODES = 'list_of_nodes'




class TerminalDict(dict):
    def __getattr__(self, attr):
        return self.get(attr, None)
    __setattr__= dict.__setitem__
    __delattr__= dict.__delitem__

    def __repr__(self):
        ret_val = ['{\n']
        keys = self.keys()
        keys.sort()
        for key in keys:
            ret_val.append('  %s: %r\n' % (key, self[key]))
        ret_val.append('}')
        return ''.join(ret_val)
