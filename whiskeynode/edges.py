from whiskeynode import WhiskeyNode
from whiskeynode.db import db
from whiskeynode.exceptions import InvalidEdgeParameterException
from whiskeynode.fieldtypes import _none

class Edge(WhiskeyNode):

    ''' 
    DOCUMENTBASE PROPERTIES 
    '''
    COLLECTION_NAME = 'whiskeynode_edges'
    
    COLLECTION = db[COLLECTION_NAME]

    FIELDS =            {
                            'inboundId': _none, #query for edges with an inboundId that matches mine for all connections pointing to me
                            'inboundCollection':_none,
                            'name':unicode,
                            'outboundId': _none, #query for edges with an outboundId that matches mine for all my connections
                            'outboundCollection': _none,
                            'terminalType':unicode,
                            'data':dict, #don't use this if you can help it. created for AttributedNodeListManager
                        }

    ENSURE_INDEXES =    [
                            #todo - i want to sort these by _id - newest first, may need to update the indexes
                            [('inboundId',1), ('outboundCollection',1), ('name',1)],
                            [('outboundId',1), ('name',1)],
                            [('name', 1), ('outboundCollection', 1), ('createdAt', 1)], #for the metrics
                        ]

    def __init__(self, *args, **kwargs):
        WhiskeyNode.__init__(self, *args, **kwargs)

    @classmethod
    def init_terminals(cls):
        '''
        from whiskeynode.terminals import outbound_list
        from whiskeynode.traversals import lazy_traversal
        from whiskeynode.users.user import User
        
        cls.TRAVERSALS =    {
                                'votes':lazy_traversal('voters.count'),
                                'why':lazy_traversal('voters.edges.why')
                            }
        cls.TERMINALS =     {
                                'voters' : outbound_list(User, attributes=['why']),
                            }
        '''


    @classmethod
    def create(cls, outbound_id, outbound_collection, inbound_id, inbound_collection, name, terminaltype):
        return cls({
                'inboundId':inbound_id,
                'inboundCollection':inbound_collection,
                'outboundId':outbound_id,
                'outboundCollection':outbound_collection,
                'name':name,
                'terminalType':terminaltype,
            })

    @classmethod
    def from_nodes(cls, outbound_node, inbound_node, name, terminaltype):
        #if checkerrors
        if not isinstance(outbound_node, WhiskeyNode):
            raise InvalidEdgeParameterException()
        if not isinstance(inbound_node, WhiskeyNode):
            raise InvalidEdgeParameterException()

        return cls.create(
                outbound_node._id,
                outbound_node.COLLECTION_NAME,
                inbound_node._id,
                inbound_node.COLLECTION_NAME,
                name,
                terminaltype,
            )


    def __str__(self):
        return '<Edge %s %s::%s->%s>' % (self.guid, self.name, self.outboundCollection, self.inboundCollection)


