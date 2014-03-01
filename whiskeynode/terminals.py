
from functools import partial
from whiskeynode import whiskeycache
from whiskeynode import WhiskeyNode
from whiskeynode.edges import Edge
from whiskeynode.terminaltypes import TerminalType
from whiskeynode.exceptions import (BadEdgeRemovalException,
                                    InvalidEdgeDataException,
                                    InvalidTerminalException,
                                    InvalidTerminalOperationException,
                                    InvalidTerminalParameterException,
                                    InvalidTerminalStateException,
                                    )


'''
    Requirements of connection terminals
    -Lazy loading, only grab data if you have to
    -Caching in memory - only grab data once
    -easy to declare - simple dictionary declaration
    -easy to use - dot notation syntax
'''
OUTBOUND='OUTBOUND'
INBOUND='INBOUND'
BIDIRECTIONAL = 'BIDIRECTIONAL'

IDID = 0


def outbound_node(  to_node_class, 
                    create_on_request=False, 
                    render=False, 
                    record_changes=False,
                    voteable=False,
                 ):
    return partial(NodeTerminal, to_node_class, OUTBOUND, render=render, create_on_request=create_on_request, record_changes=record_changes)

def inbound_node(   to_node_class, 
                    inbound_name, 
                    render=False, 
                    record_changes=False,
                    voteable=False,
                ):
    ''' inbound nodes just grab the first node. if there could ever be more than one connection use a list '''
    return partial(NodeTerminal, to_node_class, INBOUND, inbound_name=inbound_name, render=render, record_changes=record_changes)

def outbound_list(  to_node_class, 
                    render=False, 
                    attributes=None, 
                    sort_func=None, 
                    record_changes=False,
                    voteable=False,
                 ):
    if attributes is not None:
        return partial(AttributedListOfNodesTerminal, to_node_class, OUTBOUND, render=render, attributes=attributes, sort_func=sort_func, record_changes=record_changes)
    else:
        return partial(ListOfNodesTerminal,           to_node_class, OUTBOUND, render=render, record_changes=record_changes)

def inbound_list(   to_node_class, 
                    inbound_name, 
                    attributes=None, 
                    sort_func=None, 
                    render=False, 
                    edge_filter=None,  
                    record_changes=False,
                    voteable=False,
                ):
    if attributes is not None:
        return partial(AttributedListOfNodesTerminal, to_node_class, INBOUND, inbound_name=inbound_name, attributes=attributes, sort_func=sort_func, render=render, edge_filter=edge_filter, record_changes=record_changes)
    else:
        return partial(ListOfNodesTerminal,           to_node_class, INBOUND, inbound_name=inbound_name, render=render, record_changes=record_changes)

def bidirectional_list( to_node_class, 
                        render=False, 
                        record_changes=False,
                        voteable=False,
                      ):
    return partial(ListOfNodesTerminal, to_node_class, BIDIRECTIONAL, render=render, record_changes=record_changes)

'''
class BaseTerminal():
    def __init__(self, to_node_class, direction, origin_node, name, inbound_name, render, terminaltype):
        self.activated = False
        self.name = inbound_name if inbound_name is not None else name
        self.node = origin_node
        self.to_node_class = to_node_class
        self.terminaltype = terminaltype
        self.direction = direction
        self._render = render
        self._insave = False

        if self.direction == INBOUND and inbound_name == None:
            raise InvalidTerminalException('inbound_name cannot be none when direction is INBOUND')

    def edge_display_name(self):
        return '%s:%s' % (self.name, self.to_node_class.COLLECTION_NAME)
    def edge_query(self):
        raise NotImplementedError()
    def get(self):
        raise NotImplementedError()
    def set(self, value):
        raise NotImplementedError()
    def delete(self):
        raise NotImplementedError()
    def render(self):
        raise NotImplementedError()
    def exists(self):
        raise NotImplementedError()
    def add_inbound_edge(self):
        raise NotImplementedError()
    def remove_inbound_edge(self):
        raise NotImplementedError()
    def remove_outbound_edge(self, edge):
        raise NotImplementedError()
'''

class NodeTerminal():
    def __init__(self, to_node_class, direction, origin_node, name, inbound_name=None, render=False, create_on_request=False, record_changes=False ): #, inbound_edges, outbound_edges):
        self.activated = False
        self.name = inbound_name if inbound_name is not None else name
        self.original_name = name
        self.node = origin_node
        self.record_changes = record_changes
        self.to_node_class = to_node_class
        self.terminaltype = TerminalType.NODE
        self.terminalchanges = []
        self.direction = direction
        self._render = render
        self._insave = False

        if self.direction == INBOUND and inbound_name == None:
            raise InvalidTerminalException('inbound_name cannot be none when direction is INBOUND')

        self._edge = None
        self._to_node = None
        self.create_on_request = create_on_request
        
        if self.direction != OUTBOUND and self.direction != INBOUND:
            raise InvalidTerminalException('Node terminals can only be INBOUND or OUTBOUND')
        
    def __repr__(self):
        return '%s node to %s.%s named %s' % (self.direction, self.to_node_class.__module__, self.to_node_class.__name__, self.name)

    def _get_to_node_id(self):
        self.get_edge()
        if self._edge:
            return self._edge.inboundId if self.direction == OUTBOUND else self._edge.outboundId
        return None

    def _get_to_node_from_cache(self):
        ''' without going to the database '''
        if self._to_node is None:
            _id = self._get_to_node_id()
            if _id:
                self._to_node = whiskeycache.RAM.get(_id, None)
        return self._to_node

    def add_inbound_edge(self, edge):
        assert self.direction == INBOUND, \
                'Terminal [%s] on [%s] is an outbound node, you can\'t add inbound connections to an outbound node' % (self.name, self.node.__class__)
        if self._edge is not None and self._edge != edge:
            self._to_node = None
        if self._to_node is None:
            self.activated = True
            self._edge = edge
            self.get()

    def add_outbound_edge(self, edge):
        self.activated = True
        self._edge = edge
        self._to_node = self.to_node_class.from_id(self._get_to_node_id())

    def delete(self):
        #print "DELETE!!! "+str(self._edge)+" : "+self.name+" : "+str(self.node.__class__)
        assert self.direction == OUTBOUND, \
            'Terminal [%s] on [%s] is an inbound node, you can\'t remove connections from an inbound node' % (self.name, self.node.__class__)

        self.set(None)

    def edge_display_name(self):
        return '%s:%s' % (self.name, self.to_node_class.COLLECTION_NAME)

    def edge_query(self):
        if self.direction == OUTBOUND:
            return {'outboundId':self.node._id, 'name':self.name}
        else: #if self.direction == INBOUND
            return {'inboundId':self.node._id, 'outboundCollection':self.to_node_class.COLLECTION_NAME, 'name':self.name}

    def exists(self):
        return self._edge != None or Edge.find(self.edge_query()).count() > 0

    def get(self):
        if self._to_node == None:
            self.get_edge()
            if self._edge is None and self.create_on_request:
                self.set(self.to_node_class())
            elif self._edge:
                self._to_node = self.to_node_class.from_id(self._get_to_node_id())
                assert self._to_node is not None, 'to node should not be none'
                if self.direction == OUTBOUND:
                    self._to_node.add_inbound_edge(self.name, self._edge)
                else:
                    self._to_node.add_outbound_edge(self.name, self._edge)
        return self._to_node

    def get_edge(self):
        if not self.activated or self._edge is None:
            assert self._edge is None, 'edge should be none'
            self._edge = Edge.find_one(self.edge_query())
            assert  self.direction == INBOUND or \
                    self._edge is None or \
                    self._edge.inboundCollection == self.to_node_class.COLLECTION_NAME, \
                    'Edge collection doesn not match to_node_class on node named [%s] on class [%s] edge: %s' % (self.name, self.node.__class__, str(self._edge.to_dict()))
            self.activated = True
        return self._edge

    def remove_inbound_edge(self, edge):
        assert self.direction == INBOUND, \
                'Terminal [%s] on [%s] is an outbound node, you can\'t remove inbound connections from an outbound node' % (self.name, self.node.__class__)
        if self.activated:
            if self.get_edge() is not None and self._edge._id == edge._id:
                self._edge = None
                self._to_node = None
                #leaving activated as true, so lazy traversals know that something has changed

    def remove_outbound_edge(self, edge):
        assert self.direction == OUTBOUND
        if self.activated:
            if self.get_edge() is not None and self._edge._id == edge._id:
                self._edge = None
                self._to_node = None
                #leaving activated as true, so lazy traversals know that something has changed

    def render(self, render_terminals=False, *args, **kwargs):
        self.get()
        if self._to_node:
            return self._to_node.render(render_terminals=render_terminals, *args, **kwargs)
        else:
            return {}

    def render_pretty(self, do_print=True, *args, **kwargs):
        ret_val = pformat(self.render(*args, **kwargs))
        if do_print:
            print ret_val
        else:
            return ret_val

    def save(self, *args, **kwargs):
        if not self._insave:
            self._insave = True
            #print "SAVE!!! "+str(self._edge)+" : "+self.name+" : "+str(self.node.__class__)

            if self.activated and self._edge:
                if self._to_node:
                    self._to_node.save(*args, **kwargs)
                self._edge.save(*args, **kwargs)

            self._insave = False
        self.terminalchanges = []

    def set(self, value):
        assert self.direction == OUTBOUND, \
                'Terminal [%s] on [%s] is an inbound node, you can\'t add connections to an inbound node' % (self.name, self.node.__class__)

        if value and value._id == self._get_to_node_id():
            return
        if value is None and self._get_to_node_id() is None:
            return

        self._get_to_node_from_cache()
        if self._to_node:
            self._to_node.remove_inbound_edge(self.name, self._edge)

        if self._edge:
            if self.record_changes:
                self.terminalchanges.append({
                                            'terminalName':self.name,
                                            'terminalAction':'removed',
                                            'attributes':{},
                                            'terminalNodeId':self._get_to_node_id()
                                            })
            self._edge.remove()
            self._edge = None
            self._to_node = None

        if value is not None:
            if value.COLLECTION_NAME != self.to_node_class.COLLECTION_NAME:
                raise InvalidTerminalException('Terminal [%s] on [%s] takes [%s] not [%s]' % (
                                                        self.name, self.node.__class__, self.to_node_class, value.__class__))
            

            #print "SET!!! "+str(self._edge)+" : "+self.name+" : "+str(self.node.__class__)
            self._edge = Edge.from_nodes(self.node, value, self.name, self.terminaltype)
            self._to_node = value
            self._to_node.add_inbound_edge(self.name, self._edge)
            self.activated = True

            if self.record_changes:
                self.terminalchanges.append({
                                                'terminalName':self.original_name,
                                                'terminalAction':'added',
                                                'attributes':{},
                                                'terminalNodeId':self._get_to_node_id()
                                                })





class ListOfNodesTerminal():

    def __init__(self, to_node_class, direction, origin_node, name, inbound_name = None, render=False, edge_filter=None, record_changes=False, **kwargs): 
        self.activated = False
        self.name = inbound_name if inbound_name is not None else name
        self.original_name = name
        self.node = origin_node
        self.edge_filter = edge_filter
        self.record_changes = record_changes
        self.to_node_class = to_node_class
        self.terminaltype = TerminalType.LIST_OF_NODES
        self.terminalchanges = []
        self.direction = direction
        self._render = render
        self._insave = False

        if self.direction == INBOUND and inbound_name == None:
            raise InvalidTerminalException('inbound_name cannot be none when direction is INBOUND')

        self._list = None
        self._edges = None
        self._initialized = False
        global IDID
        self._idid = IDID
        IDID += 1

        if self.direction == BIDIRECTIONAL and type(origin_node) != to_node_class:
            raise InvalidTerminalException('Bidirectional lists can only be created between nodes of the same type')

    def __repr__(self):
        return '%s list to %s.%s named %s' % (self.direction, self.to_node_class.__module__, self.to_node_class.__name__, self.name)

    def __len__(self): 
        return len(self.get_edges())

    def __getitem__(self, i): 
        if self.activated:
            self.get()
            return self._list[i]
        else:
            edge = Edge.find_one(self.edge_query())
            if edge.inboundId == self.node._id:
                return self.to_node_class.find_one({'_id':edge.outboundId})
            else:
                return self.to_node_class.find_one({'_id':edge.inboundId})


    def __delitem__(self, i): 
        raise NotImplementedError()

    #def __contains__(self, node):
    #    return node._id in self.get_edges()

    def _add_node(self, to_node):
        assert self.direction != INBOUND, \
            '(wrong direction) Terminal [INBOUND:%s] on [%s] is an inbound node, you can\'t add connections to an inbound node' % (self.name, self.node.__class__)

        assert to_node.COLLECTION_NAME == self.to_node_class.COLLECTION_NAME, \
            'Terminal [%s] on [%s] takes [%s] not [%s]' % (self.name, self.node.__class__, self.to_node_class, to_node.__class__)
        
        if not to_node._id in self.get_edges():
            self.get()
            self._edges[to_node._id] = Edge.from_nodes(self.node, to_node, self.name, self.terminaltype)
            to_node.add_inbound_edge(self.name, self._edges[to_node._id])
            self._list.append(to_node)
            self.sort()
            if self.record_changes:
                self.terminalchanges.append({
                                                'terminalName':self.original_name,
                                                'terminalAction':'added',
                                                'attributes':{},
                                                'terminalNodeId':to_node._id,
                                                })

    def _remove_node(self, to_node):
        assert self.direction != INBOUND, \
            'Terminal [%s] on [%s] is an inbound node, you can\'t remove connections from an inbound node' % (self.name, self.node.__class__)
        if to_node._id in self.get_edges():
            self.get()
            edge = self._edges[to_node._id]
            if edge.inboundId == to_node._id:
                to_node.remove_inbound_edge(self.name, edge)
            else:
                to_node.remove_outbound_edge(self.name, edge)
            edge.remove()
            del self._edges[to_node._id]
            self._list.remove(to_node)
            self.sort()

            if self.record_changes:
                self.terminalchanges.append({
                                                'terminalName':self.original_name,
                                                'terminalAction':'removed',
                                                'attributes':{},
                                                'terminalNodeId':to_node._id,
                                                })

    def add_inbound_edge(self, edge):
        assert self.direction != OUTBOUND
        #we have to add inbound nodes here so that we know a save will 
        #traverse all nodes and make the proper saves
        self.get()
        if edge.outboundId not in self._edges:
            self._edges[edge.outboundId] = edge
            self._list.append(self.to_node_class.from_id(edge.outboundId))
            self.sort()

    def add_outbound_edge(self, edge):
        pass #don't think we need to do anything here

    def append(self, node):
        self._add_node(node)

    def count(self):
        ''' counts all items in db and in local cache '''
        return Edge.find(self.edge_query()).count()

    def delete(self):
        self.set([])

    def edge_display_name(self):
        return '%s:%s' % (self.name, self.to_node_class.COLLECTION_NAME)

    def edge_query(self, direction=None): #todo include to_node=None
        if direction == None: direction = self.direction
        if direction == INBOUND:
            rv = {'inboundId':self.node._id, 'outboundCollection':self.to_node_class.COLLECTION_NAME, 'name':self.name}
        elif direction == OUTBOUND:
            rv = {'outboundId':self.node._id, 'name':self.name}
        elif direction == BIDIRECTIONAL:
            rv = {
                    '$or':[
                        {'inboundId':self.node._id, 'outboundCollection':self.to_node_class.COLLECTION_NAME, 'name':self.name},
                        {'outboundId':self.node._id, 'name':self.name}
                    ]
                }
        else:
            raise NotImplementedError('direction %s is not supported' % direction)
        if self.edge_filter != None:
            rv.update(self.edge_filter)
        return rv

    def exists(self):
        return len(self.get_edges()) > 0

    def extend(self, nodes):
        for node in nodes:
            self._add_node(node)

    def get(self):
        #pulls everything out of the db, returns self
        if self._list is None:
            self.get_edges()
            self._list = self.to_node_class.from_ids(self._edges.keys())
            self.sort()
        return self
        
    def get_edge(self, node):
        #todo run edge_query with to_node
        return self.get_edges()[node._id]
            
    def get_edges(self):
        if self.activated == False:
            assert self._edges is None, '_edges should be None'

            self._edges = {}
            self.activated = True

            if self.direction == INBOUND or self.direction == BIDIRECTIONAL:
                for edge in Edge.find(self.edge_query(INBOUND), skip_cache=self.edge_filter!=None, limit=200): #hack here, if there is an edge filter, skip the cache
                    self._edges[edge.outboundId] = edge

            if self.direction == OUTBOUND or self.direction == BIDIRECTIONAL:
                for edge in Edge.find(self.edge_query(OUTBOUND), skip_cache=self.edge_filter!=None, limit=200): #hack here, if there is an edge filter, skip the cache
                    self._edges[edge.inboundId] = edge
                    #if self.check_errors
                    assert edge.inboundCollection == self.to_node_class.COLLECTION_NAME, \
                        'On node named [%s] on class [%s] data: %s' % (self.name, self.node.__class__, str(edge.to_dict()))

        return self._edges

    def insert(self, i, node):
        raise NotImplementedError()

    def pop(self, index=-1):
        self.get()
        node = self._list[index]
        self._remove_node(node)
        return node

    def remove(self, node):
        self._remove_node(node)

    def remove_inbound_edge(self, edge):
        assert self.direction != OUTBOUND
        if self.activated:
            if edge.outboundId in self._edges:
                if self._list is not None:
                    self._list.remove(self.to_node_class.from_id(edge.outboundId))
                del self._edges[edge.outboundId]
                self.sort()

    def remove_outbound_edge(self, edge):
        ''' called when a node we're connected to is removed '''
        if self.activated:
            if edge.inboundId in self._edges:
                del self._edges[edge.inboundId]
            if self._list != None:
                self._list.remove(self.to_node_class.from_id(edge.inboundId))

    def render(self, render_terminals=False, *args, **kwargs):
        self.get()
        return[x.render(render_terminals=render_terminals, *args, **kwargs) for x in self._list]

    def render_pretty(self, do_print=True, *args, **kwargs):
        ret_val = pformat(self.render(*args, **kwargs))
        if do_print:
            print ret_val
        else:
            return ret_val

    def save(self, *args, **kwargs):
        if not self._insave:
            self._insave = True
            if self.activated and len(self._edges) > 0:
                if self._list:
                    for node in self._list:
                        node.save(*args, **kwargs) #saves shouldn't call the db if nothing has changed
                for edge in self._edges.values():
                    edge.save(*args, **kwargs) #saves shouldn't call the db if nothing has changed
            self._insave = False
        self.terminalchanges = []

    def set(self, nodes):
        if type(nodes) != list:
            raise InvalidTerminalException('Terminal [%s] on [%s] should not be set to anything other than a list' % (self.name, self.to_node_class))
        self.get()
        old_nodes = self._list[:]
        for node in old_nodes:
            self._remove_node(node)
        assert len(self) == 0, 'Why didn\'t we clear our list?'
        for node in reversed(nodes):
            self._add_node(node)


    def sort(self, key=None):
        if self._list != None:
            if key is None:
                edges_for_sort = [(k,v) for k,v in self._edges.items()]
                edges_for_sort.sort(key=lambda x: x[1]._id, reverse=True)
                _ids = [x[0] for x in edges_for_sort]
                self._list.sort(key=lambda x: _ids.index(x._id))
            else:
                self._list.sort(key=key)
        


class AttributedListOfNodesTerminal(ListOfNodesTerminal):
    def __init__(self, *args, **kwargs):
        ListOfNodesTerminal.__init__(self, *args, **kwargs)
        self.attributes = kwargs['attributes']
        self.sort_func = kwargs.get('sort_func', None)

    def __repr__(self):
        return '%s list to %s.%s named %s with %s attributes' % (self.direction, self.to_node_class.__module__, self.to_node_class.__name__, self.name, str(self.attributes))

    def add(self, node, **kwargs):
        return self.append(node, **kwargs)

    def append(self, node, **kwargs):
        ListOfNodesTerminal.append(self, node)
        self.update(node, **kwargs)

    def render(self, render_terminals=False, custom_sort_func=None, *args, **kwargs):
        self.get()
        self.sort()
        ret_val = [self.render_one(x, render_terminals=render_terminals, *args, **kwargs) for x in self._list]
        if custom_sort_func:
            return custom_sort_func(ret_val)
        elif self.sort_func:
            return self.sort_func(ret_val)
        else:
            return ret_val
    
    def render_one(self, node, render_terminals=False, *args, **kwargs):
        return dict(self.get_edge(node).data, **node.render(render_terminals, *args, **kwargs))

    def update(self, node, **kwargs):
        changes = {}
        edge = self.get_edge(node)
        for k,v in kwargs.items():
            if k in self.attributes:
                if v != edge.data.get(k):
                    changes[k] = v
                edge.data[k] = v
            else:
                raise InvalidEdgeDataException('Edge attribute [%s] has not been explicitly defined for terminal [%s] in class [%s]' % (k, self.name, self.node.__class__))

        if self.record_changes and len(changes) > 0:
            self.terminalchanges.append({
                                            'terminalName':self.original_name,
                                            'terminalAction':'updated',
                                            'attributes':changes,
                                            'terminalNodeId':node._id,
                                        })


    



