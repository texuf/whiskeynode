from bson.objectid import ObjectId
from whiskeynode import WhiskeyNode
from whiskeynode.db import db
from whiskeynode.exceptions import InvalidEdgeParameterException
from whiskeynode.fieldtypes import _none

class WhiskeyEvent(WhiskeyNode):
    ''' 
    DOCUMENTBASE PROPERTIES 
    '''
    COLLECTION_NAME = 'whiskeynode_events'
    COLLECTION = db[COLLECTION_NAME]

    FIELDS =            {
                            'nodeId': _none, #ObjectId
                            'collection':unicode,
                            'currentUserId':_none,
                            'data':dict,
                            'type':unicode,
                        }

    def __init__(self, *args, **kwargs):
        WhiskeyNode.__init__(self, *args, **kwargs)

    @classmethod
    def init_terminals(cls):
        cls.TERMINALS =    {
                            }


    @classmethod
    def create(cls, node, event_type, data, current_user_id):
        return cls.COLLECTION.save({
                '_id':ObjectId(),
                'nodeId':node._id,
                'collection':node.COLLECTION_NAME,
                'currentUserId':current_user_id,
                'type':event_type,
                'data':data,
            })
