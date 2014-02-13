from whiskeynode import WhiskeyNode
from whiskeynode.db import db
from whiskeynode.exceptions import InvalidEdgeParameterException
from whiskeynode.fieldtypes import _none

class Voter(WhiskeyNode):

    ''' 
    DOCUMENTBASE PROPERTIES 
    '''
    COLLECTION_NAME = 'edges_voters'
    COLLECTION = db[COLLECTION_NAME]

    FIELDS =            {
                        }

    ENSURE_INDEXES =    [
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

