
from functools import partial
from whiskeynode.terminaltypes import TerminalType


def lazy_traversal(path, render=True, default_value=None, default_attr=None):
    return partial(LazyTraversal, path, render=render, default_value=default_value, default_attr=default_attr)




class LazyTraversal():
    def __init__(self, path, origin_node, name, render=True, default_value=None, default_attr=None):
        self.render = render
        self.name = name
        self.node = origin_node
        self.path_parts = path.split('.')
        self.default_value = default_value
        self.default_attr = default_attr

        if len(self.path_parts) < 2:
            assert 0, 'Lazy traversals should be declared as <terminal_name>.<field_value>'
        if len(self.path_parts) > 2:
            assert 0, 'Support for more than one traversal hasn\'t been developed, why don\'t you give it a shot?'

        self.terminal_name = self.path_parts[0]
        self.field_name = self.path_parts[1]

    def get(self): 
        if self.node.terminals[self.terminal_name].activated:

            if self.field_name == 'exists':
                return self.node.terminals[self.terminal_name].exists()

            #LISTS
            if self.node.terminals[self.terminal_name].terminaltype == TerminalType.LIST_OF_NODES:
            
                terminal = getattr(self.node, self.terminal_name, [])
                if self.field_name == 'count':
                    return terminal.count()
                elif len(terminal) > 0:
                    #just grab the property off the first item in the list
                    return getattr(terminal[0], self.field_name)
            #NODES
            else:
                if self.default_attr is not None:
                    return getattr(getattr(self.node, self.terminal_name, {}), self.field_name, getattr(self.node, self.default_attr, self.default_value))
                else:
                    return getattr(getattr(self.node, self.terminal_name, {}), self.field_name, self.default_value)
        
        #defalut bahavior
        if self.default_attr is not None:
            return self.node.__dict__.get(self.name, getattr(self.node, self.default_attr, self.default_value))
        else:
            return self.node.__dict__.get(self.name, self.default_value)

    def set(self, value):
        assert 0, 'Traversals don\'t support set... yet'

    def delete(self):
        assert 0, 'Traversals don\'t suppot delete... yet'


    