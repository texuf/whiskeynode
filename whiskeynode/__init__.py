from bson.objectid import ObjectId, InvalidId
from collections import deque
from datetime import datetime
from functools import partial
from pprint import pformat
from pprintpp import pprint
from whiskeynode import whiskeycache
from whiskeynode.db import db
from whiskeynode.exceptions import (BadEdgeRemovalException,
                                    CollectionNotDefinedException,
                                    ConnectionNotFoundException,
                                    FieldNameNotDefinedException,
                                    InvalidFieldNameException,
                                    InvalidConnectionNameException,)
from whiskeynode.fieldtypes import FieldDict
from whiskeynode.terminaltypes import TerminalDict, TerminalType
from copy import copy, deepcopy
import itertools
import os

environment = os.environ.get('ENVIRONMENT')
save_id = 0



#helper function for current user id
def get_current_user_id():
    return None

def get_new_save_id():
    global save_id
    i = save_id
    save_id = save_id + 1
    return i


''' WhiskeyNode '''
class WhiskeyNode(object):

    ''' REQUIRED OVERRIDES '''
    #DATABASE, override these variables in your class
    COLLECTION_NAME = '_whiskeynode'
    COLLECTION      = db[COLLECTION_NAME]

    FIELDS =            {
                            #'name':type
                        }

    PRE_RENDER_FIELDS = ['createdAt', 'lastModified']

    ''' DEFAULT PROPERTIES '''
    #DATABASE FIELDS, fields must be bson types
    DEFAULT_FIELDS =    {
                            '_id': ObjectId,
                            'createdAt' : datetime.now, #storing created at to send to the client - to search on createdAt, use the _id's date properties
                            'lastModified': datetime.now,
                        }

    #ENSURE_INDEXES, indexed fields are indexed during the database migration, 
    #                       for performance reasons try not to index anything, if an index should be unique,
    #                       it should also be added to ENSURE_UNIQUE_INDEXES
    ENSURE_INDEXES = set(
                        [ 
                            #'name',
                        ]) 
    ENSURE_UNIQUE_INDEXES = set(
                        [
                            #'name'
                        ])

    #DATABASE FIELD MANAGEMENT, these properties auto manage data sent to and from the client
    DO_NOT_UPDATE_FIELDS = set([])
    DEFAULT_DO_NOT_UPDATE_FIELDS = set(
                        [ 
                            '_id',
                            'createdAt',
                            'lastModified',
                        ])

    DO_NOT_RENDER_FIELDS = set([])
    DEFAULT_DO_NOT_RENDER_FIELDS = set(
                        [ 
                            '_id',
                        ]) 

    RESERVED_FIELDS = set(
                        [
                            'messages',
                            'terminals',
                            'fields',
                        ])

    TERMINALS = {}
    TRAVERSALS = {}

    fields = {} #PRIVATE

    check_errors = True #really speeds up initialization

    def __init__(self, init_with=None, dirty=True):
        if self.check_errors:
            assert self.__class__ != WhiskeyNode, 'WhiskeyNode is meant to be an abstract class'
        self._dict = init_with if init_with else {}  #why a variable here? store everything that we get out of mongo, so we don't have data loss
        self._dirty = dirty
        self._is_new_local = False
        self._save_record = {}
        self._terminals = None
        self._traversals = None
        self.DO_NOT_RENDER_FIELDS.update(self.DEFAULT_DO_NOT_RENDER_FIELDS)
        self.DO_NOT_UPDATE_FIELDS.update(self.DEFAULT_DO_NOT_UPDATE_FIELDS)
        
        #INIT CLASS FIELDS
        if self.__class__.fields == {}:
            self.__class__.fields = FieldDict(self.DEFAULT_FIELDS, **self.FIELDS)
        #self.fields = self.__class__._FIELDS.copy()

        #INIT CLASS TERMINALS
        if self.__class__.TERMINALS == {}:
            self.__class__.init_terminals()
            for name in self.__class__.TERMINALS:
                self.__class__._add_terminal_property(self, name)
            if self.check_errors:
                bad_fields = set(self.__class__.fields.keys()).intersection(list(self.__class__.RESERVED_FIELDS) + self.__class__.TERMINALS.keys() + self.__dict__.keys())
                if len(bad_fields) > 0:
                    raise InvalidFieldNameException('Fields %s cannot be used on class %s because they are reserved or terminals.' % (str(bad_fields), str(self.__class__)))
            for name in self.__class__.TRAVERSALS:
                self.__class__._add_traversal_property(self, name)

        #INIT INSTANCE FIELDS
        for field, field_type in self.fields.items():
            try: #this is in two places to prevent a function call in a loop
                if field_type is dict or field_type is list:
                    self.__dict__[field] = deepcopy(self._dict[field]) #make a copy so we can compare it later (this is in two places)
                else:
                    self.__dict__[field] = self._dict[field]
            except KeyError:
                self.__dict__[field] = field_type()
                if field == '_id':
                    self._is_new_local = True
        for field, trav in self.traversals.items():
            try:
                self.__dict__[field] = self._dict[field]
            except KeyError:
                self.__dict__[field] = trav.default_value
        
        whiskeycache.save( self )

    ##
    ## classmethods
    ##

    @classmethod
    def distinct(self, field):
        return self.COLLECTION.distinct(field)


    @classmethod
    def drop(cls):
        ''' usefull for testing, not sure if this should be used in production ever '''
        for node in cls.find():
            node.remove()


    @classmethod
    def find(cls, query={}, limit=0, skip_cache=False, sort=None, skip=0):
        '''
            Returns an iterator of whiskeynodes SORTED HIGHEST TO LOWEST _id (most recent first)
            all params are passed to pymongo except skip_cache - this allows you to make complex queries to mongodb
        ''' 
        if sort is None:
            sort = [('_id', -1)]
        else:
            assert isinstance(sort, list) and len(sort) >= 1, 'sort should be a list of tuples'
            assert isinstance(sort[0], tuple), 'sort should be a list of tuples'

        existing = deque( whiskeycache.find(cls, query, sort)) if not skip_cache else [] #grab the items we already have in RAM
        
        if limit > 0:
            cursor = cls.COLLECTION.find(query, limit=limit+skip).sort(sort) #otherwise, hit the db, todo, pass a $notin:_ids
        else:
            cursor = cls.COLLECTION.find(query).sort(sort) #todo - take out the if else after fixing mongo mock
        class WhiskeyCursor():
            def __init__(self, existing, cursor, limit=0, skip=0):
                self.existing = existing
                self.cursor = cursor
                self.__count = None
                self.__limit = limit
                self.__retrieved = 0
                if skip > 0:
                    skipped = 0
                    for s in self:
                        skipped += 1
                        if skipped >= skip:
                            self.__retrieved = 0
                            break
            def __iter__(self):
                ''' this will return the items in cache and the db sorted by _id, newest first '''
                if self.__limit == 0 or self.__retrieved < self.__limit:
                    self.__retrieved = self.__retrieved + 1
                    for d in cursor:
                        #we need tiebreakers for items in cache vs items in the db, unfortunately we only tiebreak on the first item in a sort list
                        if sort[0][1] == -1:
                            while len(self.existing) > 0 and getattr(self.existing[0], sort[0][0]) > d.get(sort[0][0]):
                                yield self.existing.popleft()
                        else:
                            while len(self.existing) > 0 and getattr(self.existing[0], sort[0][0]) < d.get(sort[0][0]):
                                yield self.existing.popleft()
                        if len(self.existing) > 0 and self.existing[0]._id == d['_id']:
                            yield self.existing.popleft()
                        else:
                            yield whiskeycache.from_cache(cls, d, dirty=False)
                    while len(self.existing) > 0:
                        yield self.existing.popleft()

            def next(self):
                """ return the next item in cursor, sorted by _id, newest first """
                try:
                    d = self.cursor.next()
                except StopIteration:
                    return self.existing.popleft()
                if len(self.existing) > 0 and self.existing[0]._id > d['_id']:
                    self.cursor = itertools.chain([d], self.cursor)
                    return self.existing.popleft()
                elif len(self.existing) > 0 and self.existing[0]._id == d['_id']:
                    return self.existing.popleft()
                else:
                    return whiskeycache.from_cache(cls, d, dirty=False)

            def count(self):
                ''' NOTE - this count isn't exactly accurate
                    since we don't know how many items will already be in the cache, but it's pretty close '''
                if self.__count is None:
                    #self.__count = len(self.existing) + self.cursor.count()
                    self.__count = self.cursor.count() #we're only looking at what's actually in the db for now...
                    for x in self.existing:
                        if x._is_new_local:
                            self.__count = self.__count + 1
                return self.__count
            def limit(self, limit):
                self.__limit = self.cursor.limit = limit

            def __len__(self):
                return self.count()
        return WhiskeyCursor(existing, cursor, limit, skip)


    @classmethod
    def find_one(cls, query={}):
        '''Returns one node as a Node object or None.'''
        from_cache = whiskeycache.find_one(cls, query)
        if from_cache is not None:
            return from_cache
        else:
            data = cls.COLLECTION.find_one(query, sort=[('_id',-1)])
            if data is not None:
                return whiskeycache.from_cache(cls, data, dirty=False)
            else:
                return None


    @classmethod
    def from_dbref(cls, collection, _id):
        ''' try to avoid using this function - it's not recomended in the mongodb docs '''
        data = db[collection].find_one({'_id':_id})
        if data:
            c = cls.from_dict(data)
            c.COLLECTION_NAME = collection
            c.COLLECTION = db[collection]
            return c
        else:
            return None


    @classmethod
    def from_dict(cls, data, dirty=False):
        if data is None:
            return None
        return whiskeycache.from_cache(cls, data, dirty)


    @classmethod
    def from_id(cls, _id):
        '''Returns a node based on the _id field.
           if objectid is a string it will try to cast it to an objectid'''
        if type(_id) is not ObjectId:
            try:
                _id = ObjectId(_id)
            except InvalidId:
                return None
        rv = whiskeycache.from_id(_id, cls.COLLECTION_NAME)
        return rv if rv else cls.find_one({'_id': _id})


    @classmethod
    def from_ids(cls, ids):
        if len(ids) == 0:
            return []
        if not isinstance(ids[0], ObjectId):
            ids = [ObjectId(x) for x in ids]
        to_query = []
        to_return = []
        for _id in ids:
            if _id in whiskeycache.RAM:
                to_return.append(whiskeycache.RAM[_id])
            else:
                to_query.append(_id)
        if len(to_query) > 0:
            cursor = cls.COLLECTION.find({'_id':{'$in':to_query}})
            to_return.extend([whiskeycache.from_cache(cls, data, dirty=False) for data in cursor])
        return to_return


    @classmethod
    def init_terminals(cls):
        cls.TERMINALS =     {
                            }
        cls.TRAVERSALS =    {
                            }


    ##
    ## properties
    ##

    @property
    def guid(self):
        ''' for migrating to the new code base, this doens't get saved to the db '''
        return str(self._id)

    @property
    def terminals(self):
        if self._terminals is None:
            self._terminals = TerminalDict()
            self._init_terminals()
        return self._terminals

    @property
    def traversals(self):
        if self._traversals is None:
            self._traversals = TerminalDict()
            self._init_traversals()
        return self._traversals


    ##
    ## functions
    ##


    def add_field(self, field, field_type, render=True, update=True, dirty=True):
        if self.check_errors:
                self._check_add_field_errors(field, field_type)
        try: #this is in two places to prevent a function call in a loop
            if field_type is dict or field_type is list:
                self.__dict__[field] = deepcopy(self._dict[field]) #make a copy so we can compare it later
            else:
                self.__dict__[field] = self._dict[field]
        except KeyError:
            self.__dict__[field] = field_type()
        self.fields[field] = field_type
        if render == False:
            self.DO_NOT_RENDER_FIELDS.add(field)
        if update == False:
            self.DO_NOT_UPDATE_FIELDS.add(field)
        self._dirty = self._dirty or dirty

    def add_inbound_edge(self, name, edge):
        terminal = self._get_inbound_terminal(name, edge)
        if terminal is not None:
            terminal.add_inbound_edge(edge)

    def add_outbound_edge(self, name, edge):
        if name in self.terminals:
            self.terminals[name].add_outbound_edge(edge)
        
    def add_terminal(self, name, connection_def):
        self._add_terminal(self, name, connection_def)
        self._add_terminal_property(self, name)

    def get_field(self, name, default=None):
        ''' for generically getting fields on a whiskey node '''
        try:
            return self.__dict__[name]
        except KeyError:
            return self._dict.get(name, default)

    def get_inbound_edges(self):
        from whiskeynode.edges import Edge
        return Edge.find({'inboundId':self._id}) #don't worry, find's are cached at the WN level

    def _get_inbound_terminal(self, name, edge):
        inbound_terminals = [terminal for terminal in self.terminals.values() if \
                                terminal.name == name and \
                                (terminal.direction == 'INBOUND' or terminal.direction == 'BIDIRECTIONAL') and \
                                terminal.to_node_class.COLLECTION_NAME == edge.outboundCollection]
        assert len(inbound_terminals) <= 1, 'why do we have more than one terminal?'
        return inbound_terminals[0] if len(inbound_terminals) > 0 else None

    def get_outbound_edges(self):
        from whiskeynode.edges import Edge
        return Edge.find({'outboundId':self._id}) #don't worry, find's are cached at the WN level


    def has_terminal(self, name):
        return name in self.terminals

    def pre_render(self):
        data = {}
        for field in self.PRE_RENDER_FIELDS:
            try:
                data[field] = self.__dict__[field]
            except KeyError:
                try:
                    data[field] = self._dict[field]
                except KeyError:
                    pass
        data['guid'] = str(self._id)
        return data

    def remove(self):
        ''' removes this node and all inbound and outbound edges pointing to this node'''
        ob = list(self.get_outbound_edges())
        for edge in ob:
            if edge.inboundId in whiskeycache.RAM:
                whiskeycache.RAM[edge.inboundId].remove_inbound_edge(edge.name, edge)
            edge.remove()
        ib = list(self.get_inbound_edges())
        for edge in ib:
            if edge.outboundId in whiskeycache.RAM:
                whiskeycache.RAM[edge.outboundId].remove_outbound_edge(edge.name, edge)
            edge.remove()
        whiskeycache.remove(self)
        self.COLLECTION.remove(self._id)

    def remove_field(self, field):
        if field in self.__dict__:
            del self.__dict__[field]
        if field in self._dict:
            del self._dict[field]

    def remove_inbound_edge(self, name, edge):
        terminal = self._get_inbound_terminal(name, edge)
        if terminal is not None:
            terminal.remove_inbound_edge(edge)

    def remove_outbound_edge(self, name, edge):
        if name in self.terminals:
            terminal = self.terminals[name]
            if self.check_errors:
                assert (terminal.direction == 'OUTBOUND' or terminal.direction== 'BIDIRECTIONAL') and \
                  terminal.to_node_class.COLLECTION_NAME == edge.inboundCollection, 'bad edge removal'
            terminal.remove_outbound_edge(edge)

    def render(self, render_terminals=True):
        data = self._to_dict()
        for field in self.DO_NOT_RENDER_FIELDS:
            try:
                del data[field]
            except KeyError:
                pass
        if render_terminals:
            for key, terminal in self.terminals.items():
                if terminal._render and terminal.exists():
                    data[key] = terminal.render()
        data['guid'] = str(self._id)
        return data

    def render_pretty(self, do_print=True, *args, **kwargs):
        rendr = self.render(*args, **kwargs)
        r = pprint(rendr)
        if do_print:
            print r
        else:
            return r

    def save(self, update_last_modified=True, current_user_id = None, save_id=None, save_terminals=True):
        if save_id is None:
            save_id = get_new_save_id()

        if current_user_id is None:
            current_user_id=get_current_user_id()
        
        if save_id not in self._save_record:
            self._save_record[save_id] = True #prevent infinite recursive loops
            data = self._to_dict()

            is_saving = self._dirty or self._diff_dict(data)
            #from logger import logger
            #logger.debug(    '--------------- save ' + str(self) + " : " + str(data.get('name','')))
            if is_saving:

                #for k in data:
                #    if self._dict.get(k) is None or cmp(data[k], self._dict.get(k)) != 0:
                #        try:
                #            logger.debug(    '!! ' + k + " : " + str(data[k]) + " : " + str(self._dict.get(k)))
                #        except UnicodeEncodeError:
                #            logger.debug(    '!! ' + k + " : bad UnicodeEncodeError")


                if self.check_errors:
                    assert self._id is not None and self._id != ''
                if update_last_modified:
                    data['lastModified'] = self.lastModified = datetime.now()
                if self.check_errors:
                    assert self.COLLECTION_NAME != '_whiskeynode', 'COLLECTION_NAME has not ben defined for class %s' % self.__class__

                #save to db
                
                #logger.debug('+++++++++++++++++ save ' + str(self) + " : " + str(data.get('name','')))
                key = self.COLLECTION.save(data, safe=True)
                self._dirty = False
                self._is_new_local = False
                #record changes in event if requested
                self.on_save(new_dict=data, old_dict=self._dict)
                #reset our current state
                self._dict = data

            #save our terminals
            if save_terminals:
                for name, terminal in self.terminals.items():
                    terminal.save(update_last_modified=update_last_modified, current_user_id=current_user_id, save_id=save_id)
        return self

    def on_save(self, new_dict, old_dict):
        pass

    def set_field(self, name, value):
        ''' for generically getting fields on a whiskey node '''
        if name not in self.fields:
            self.add_field(name, type(value))
        self.__dict__[name] = value

    def _to_dict(self):
        data = self._dict.copy()
        for field, field_type in self.fields.items():
            value = getattr(self, field)
            if value is not None:
                if field_type is dict or field_type is list:
                    data[field] = deepcopy(value) #make a copy so we can compare it later
                else:
                    data[field] = value
        for field in self.TRAVERSALS:
            value = getattr(self, field)
            if value is not None:
                data[field] = value
        return data

    def to_dbref(self):
        return  {
                    '_id':self._id,
                    'collection':self.COLLECTION_NAME,
                }
                

    def update(self, data):
        '''Performs an update on the node from a dict. Does not save.'''
        fields = set(self.fields.keys()) - self.DO_NOT_UPDATE_FIELDS
        for field in fields:
            if field in data:
                self.__dict__[field] = data[field]
        if self.check_errors and environment != 'production':
            legit_fields = self.fields.keys() + self.terminals.keys() + self.traversals.keys() + ['guid']
            bad_fields = set(data.keys()) - set(legit_fields)
            if len(bad_fields) > 0:
                raise FieldNameNotDefinedException('Fields names %s with values %s are not defined in class [%s]' % (str(list(bad_fields)), str([(x,data[x]) for x in bad_fields]), self.__class__))



    ##
    ## Class level helpers
    ##

    def _check_add_field_errors(self, field, field_type):
        if  field in self.__dict__ or field in self.RESERVED_FIELDS or field in self.TERMINALS:
            raise InvalidFieldNameException('Field name [%s] on %s is not valid because it is a reserved field or a terminal' % (field, self.__class__))
    
    def _init_terminals(self):
        for name, connection_def in self.TERMINALS.items():
            self._add_terminal(self, name, connection_def)


    @classmethod
    def _add_terminal(cls, self, name, connection_def):
        if cls.check_errors:
            if name in self.terminals:
                raise InvalidConnectionNameException('Terminal name [%s] on %s is not valid because it is already in use.' % (name, self.__class__))

        self.terminals[name] = connection_def(self, name)

        
    @classmethod
    def _add_terminal_property(cls, self, name):
        if cls.check_errors:
            if name in self.RESERVED_FIELDS or name in self.fields or name in self.__dict__:
                raise InvalidConnectionNameException('Terminal name [%s] on %s is not valid because it is a reserved field.' % (name, self.__class__))
        
        if not hasattr(cls, name):
            setattr(cls, 
                name, 
                property(
                    partial(cls.__get_terminal, name=name), 
                    partial(cls.__set_terminal, name=name), 
                    partial(cls.__del_terminal, name=name)))

    def __get_terminal(self, name):
        return self.terminals[name].get_self()
    def __set_terminal(self, value, name):
        return self.terminals[name].set(value)
    def __del_terminal(self, name):
        return self.terminals[name].delete()

    def _init_traversals(self):
        for name, traversal_def in self.TRAVERSALS.items():
            if self.check_errors:
                if name in self.traversals:
                    raise InvalidConnectionNameException('Traversal name [%s] on %s is not valid because it is already in use.' % (name, self.__class__))
            self.traversals[name] = traversal_def(self, name)
            self._add_traversal_property(self, name)


    @classmethod
    def _add_traversal_property(cls, self, name):
        if cls.check_errors:
            if name in self.RESERVED_FIELDS:
                raise InvalidConnectionNameException('Traversal name [%s] on %s is not valid because it is a reserved field.' % (name, self.__class__))
        
        if not hasattr(cls, name):
            setattr(cls, 
                name, 
                property(
                    partial(cls.__get_traversal, name=name), 
                    partial(cls.__set_traversal, name=name), 
                    partial(cls.__del_traversal, name=name)))

    def __get_traversal(self, name):
        return self.traversals[name].get()
    def __set_traversal(self, value, name):
        return self.traversals[name].set(value)
    def __del_traversal(self, name):
        return self.traversals[name].delete()
    

    def _diff_dict(self, target_dict):
        ''' return false if same same, true if we find diffs '''
        return cmp(self._dict, target_dict) != 0

    def __eq__(self, other):
        return other != None and self._id == other._id

    def __ne__(self, other):
        return other == None or self._id != other._id

    def to_string(self):
        ''' must return string that is key safe (no periods) '''
        return '%s:%s' % (self.__class__.__name__, self.guid)


def str_to_objectid(guid):
    #guid should be a string, try to cast the guid to an ObjectId - hopefully it works maybe
    if guid is None:
        return None
    if type(guid) is ObjectId:
        return guid
    try:
        return ObjectId(guid)
    except:
        return guid