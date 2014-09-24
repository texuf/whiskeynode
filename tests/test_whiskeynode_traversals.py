from bson.objectid import ObjectId
from bson.dbref import DBRef
from datetime import datetime
from functools import partial
from unittest import TestCase
from whiskeynode import WhiskeyNode
from whiskeynode import whiskeycache
from whiskeynode.db import db
from whiskeynode.edges import Edge
from whiskeynode.exceptions import InvalidFieldNameException, FieldNameNotDefinedException
from whiskeynode.terminals import outbound_node, outbound_list, inbound_node, inbound_list
from whiskeynode.terminaltypes import TerminalType
from whiskeynode.traversals import lazy_traversal  
import mock
import datetime




class EmailAddress(WhiskeyNode):
    COLLECTION_NAME =   'users_emails'
    COLLECTION =        db[COLLECTION_NAME]

    FIELDS =            {
                            'email':unicode,
                        }
    ''' 
    INIT 
    '''
    def __init__(self, *args, **kwargs):
        WhiskeyNode.__init__(self, *args, **kwargs)

    @classmethod
    def init_terminals(cls):
        cls.TERMINALS = {
                            'user':             outbound_node(User,create_on_request=True),
                        }

class User(WhiskeyNode):
    COLLECTION_NAME =   'users_users'
    COLLECTION =        db[COLLECTION_NAME]

    FIELDS =            {
                            'firstName': unicode,
                        }
    ''' 
    INIT 
    '''
    def __init__(self, *args, **kwargs):
        WhiskeyNode.__init__(self, *args, **kwargs)

    @classmethod
    def init_terminals(cls):
        cls.TRAVERSALS= {
                            'email':            lazy_traversal('emails.email', default_value=''),
                            'hasContactInfo':   lazy_traversal('contactInfo.exists', default_value=False),
                        }
        
        cls.TERMINALS = {
                            'emails':           inbound_list(   EmailAddress,      'user', render=False),
                            'contactInfo':      outbound_node(  ContactInfo),
                        }

class ContactInfo(WhiskeyNode):
    COLLECTION_NAME =   'users_contactinfo'
    COLLECTION =        db[COLLECTION_NAME]

    FIELDS =            {
                            'phoneNumber':unicode,
                        }

    def __init__(self, *args, **kwargs):
        WhiskeyNode.__init__(self, *args, **kwargs)

    @classmethod
    def init_terminals(cls):
        cls.TRAVERSALS= {
                            'email':            lazy_traversal('user.email', default_value=''),
                            'firstName':        lazy_traversal('user.firstName', default_value=False),
                        }
        
        cls.TERMINALS = {
                            'user':             inbound_node(   User,      'contactInfo', render=False),
                        }




class DocumentBaseTest(TestCase):
    def tearDown(self):
        self.__cleanup()

    def __cleanup(self):
        Edge.COLLECTION.drop()
        EmailAddress.COLLECTION.drop()
        User.COLLECTION.drop()
        ContactInfo.COLLECTION.drop()
        whiskeycache.clear_cache()


    def test_create_traversals(self):
        self.__cleanup()
        
        my_email_address = 'boogers@brains.com'
        new_email_address = 'boogers2@brains.com'
        e = EmailAddress({'email':my_email_address})
        self.assertTrue(e.user.contactInfo is None)
        e.user.contactInfo = ContactInfo()
        self.assertTrue(e.user.email == my_email_address)
        
        self.assertTrue(e.user.contactInfo.email == my_email_address)
        e2 = EmailAddress({'email':new_email_address})
        e2.user = e.user
        self.assertTrue(e.user.contactInfo.email == new_email_address)
        self.assertTrue(e2.user.contactInfo.email == new_email_address)

        with mock.patch('mongomock.Collection.save') as save_moc:
            e.save()
            print save_moc.call_count
            self.assertTrue(save_moc.call_count == 7) #2 emails with 2 edges to 1 user with 1 edge to 1 contactInfo

    def __load_objects(self):
        self.__cleanup()

        EmailAddress.COLLECTION.insert({'lastModified': datetime.datetime(2014, 1, 14, 16, 35, 21, 84428), '_id': ObjectId('52d5d7c92cc8230471fedf99'), 'email': 'boogers@brains.com', 'createdAt': datetime.datetime(2014, 1, 14, 16, 35, 21, 83710)})
        User.COLLECTION.insert({'firstName': u'', 'hasContactInfo': True, 'lastModified': datetime.datetime(2014, 1, 14, 16, 35, 21, 85368), '_id': ObjectId('52d5d7c92cc8230471fedf9a'), 'email': 'boogers@brains.com', 'createdAt': datetime.datetime(2014, 1, 14, 16, 35, 21, 83883)})
        ContactInfo.COLLECTION.insert({'phoneNumber': u'', 'firstName': u'', 'lastModified': datetime.datetime(2014, 1, 14, 16, 35, 21, 85447), '_id': ObjectId('52d5d7c92cc8230471fedf9c'), 'email': 'boogers@brains.com', 'createdAt': datetime.datetime(2014, 1, 14, 16, 35, 21, 85027)})
        Edge.COLLECTION.insert({'inboundId': ObjectId('52d5d7c92cc8230471fedf9a'), 'name': 'user',        'outboundId': ObjectId('52d5d7c92cc8230471fedf99'), 'terminalType': 'node', 'inboundCollection': 'users_users',       'lastModified': datetime.datetime(2014, 1, 14, 16, 35, 21, 84540), 'outboundCollection': 'users_emails','_id': ObjectId('52d5d7c92cc8230471fedf9b'), 'data': {}, 'createdAt': datetime.datetime(2014, 1, 14, 16, 35, 21, 84084)})
        Edge.COLLECTION.insert({'inboundId': ObjectId('52d5d7c92cc8230471fedf9c'), 'name': 'contactInfo', 'outboundId': ObjectId('52d5d7c92cc8230471fedf9a'), 'terminalType': 'node', 'inboundCollection': 'users_contactinfo', 'lastModified': datetime.datetime(2014, 1, 14, 16, 35, 21, 85558), 'outboundCollection': 'users_users', '_id': ObjectId('52d5d7c92cc8230471fedf9d'), 'data': {}, 'createdAt': datetime.datetime(2014, 1, 14, 16, 35, 21, 85229)})

    def test_load_traversals(self):
        self.__load_objects()

        my_email_address = 'boogers@brains.com'
        new_email_address = 'boogers2@brains.com'
        
        e = EmailAddress.find_one()
        self.assertTrue(e.email == my_email_address)

        e2 = EmailAddress({'email':new_email_address})
        e2.user = e.user
        self.assertTrue(e.user.contactInfo.email == new_email_address)








