from bson.objectid import ObjectId
from operator import attrgetter
from threading import Lock
from whiskeynode.exceptions import WhiskeyCacheException
import itertools
import weakref

'''
Weak Reference RAM - if something exists in memory, you should be able to find it here
'''

#MONKEY PATCH FOR 2.7
def weak_ref_len(self):
    return len(self.data) - len(self._pending_removals)
weakref.WeakSet.__len__ = weak_ref_len
#END MONKEY PATCH FOR 2.7

RAM = weakref.WeakValueDictionary()
RAM_ALL = {} #'collectionName':weakSet

lock = Lock()

def from_cache(cls, data, dirty=True):
    try:
        return RAM[data['_id']]
    except KeyError:
        return cls(init_with=data, dirty=dirty)

def clear_cache():
    ''' for testing '''
    with lock:
        for key in RAM.keys():
            try:
                del RAM[key]
            except KeyError:
                pass
        for key in RAM_ALL.keys():
            try:
                del RAM_ALL[key]
            except KeyError:
                pass
    
def remove(node):
    with lock:
        try:
            del RAM[node._id]
            try:
                RAM_ALL[node.COLLECTION_NAME].remove(node)
            except KeyError:
                pass
        except:
            pass

def save(node):
    #print "SAVE %s  - %s" %(str(node), str(node.ENSURE_INDEXES))
    with lock:
        RAM[node._id] = node
        try:
            RAM_ALL[node.COLLECTION_NAME].add(node)
        except: #KeyError
            RAM_ALL[node.COLLECTION_NAME] = weakref.WeakSet([node])

def from_id(_id, collection_name):
    if _id in RAM:
        rv = RAM[_id]
        return rv if rv is not None and rv.COLLECTION_NAME == collection_name else None
    else:
        return None

def from_ids(_ids):
    with lock:
        l = [RAM[x] for x in _ids if x in RAM]
    return l

def find_one(cls, query):
    if query == {}:
        for x in RAM.values():
            if type(x) is cls:
                return x
    elif '_id' in query:
        return from_id(query['_id'], cls.COLLECTION_NAME)
    try:
        with lock:
            l = list(RAM_ALL[cls.COLLECTION_NAME])
        for x in l:
            is_true = True
            for key in query.keys():
                if getattr(x, key, None) != query[key]:
                    is_true = False
                    break
            if is_true:
                return x
    except KeyError:
        return None


def _sort(dataset, sort):
    if sort:
        if len(sort) == 1:
            return sorted(dataset, key=attrgetter(sort[0][0]), reverse=sort[0][1]==-1)
        for sortKey, sortDirection in reversed(sort):
            dataset = iter(sorted(dataset, key = attrgetter(sortKey), reverse = sortDirection < 0))
    return dataset

def find(cls, query, sort):
    ''' find (should be mostly like pymongo find) '''
    
    def search(search_set, query):
        return_values = set([])
        if query == {}:
            try:
                l = list(RAM_ALL[cls.COLLECTION_NAME])
                return [x for x in l]
            except KeyError:
                return []

        if '_id' in query:
            if not isinstance(query['_id'], dict):
                try:
                    return [RAM[query['_id']]]
                except KeyError:
                    return []

        if '$or' == query.keys()[0] and len(query) == 1:
            lol = [search(search_set, x) for x in query['$or']] #list of lists (lol)
            return set(itertools.chain(*lol))

        if '$and' == query.keys()[0] and len(query) == 1:
            lol = [search(search_set, x) for x in query['$and']]
            return set.intersection(*lol)

        if len(query) > 1:
            lol = [search(search_set, {k:v}) for k,v in query.items()]
            return set.intersection(*lol)

        key = query.keys()[0]
        for x in search_set:
            #print " "
            #print " "
            #print "current query is %s" % str(query)
            is_true = True
            
            #print "key is %s" % str(key)
            #print "value of %s is %s" % (str(key), str(query[key]))
            if type(query[key]) is dict:
                if query[key] == {}:
                    is_true = getattr(x,key, None) == query[key]
                    break
                query_keys = query[key].keys()
                supported = ('$in', '$ne', '$gt', '$nin')
                if len(query_keys) == 1 and query_keys[0] in supported:
                    if query_keys[0] == '$in':
                        is_true = getattr(x, key, None) in query[key]['$in']
                    elif query_keys[0] == '$nin':
                        is_true = getattr(x, key, None) not in query[key]['$nin']
                    elif query_keys[0] == '$ne':
                        is_true = getattr(x, key, None) != query[key]['$ne']
                    elif query_keys[0] == '$gt':
                        is_true = getattr(x, key, None) > query[key]['$gt']
                else:
                    raise WhiskeyCacheException('Whiskey cache only supports the %s paramater, for deeper searches like [%s] with key [%s], use the COLLECTION' % (str(supported), str(query[key]),key))
            elif type(query[key]) is list:
                if query[key] == []:
                    is_true = getattr(x,key,None) == [] #com doesn't work for empty lists too well
                else:
                    is_true = cmp(query[key], getattr(x,key,None))
                #print "is_true is " + str(is_true) + ' wanted: ' + str(query[key]) + ' got: ' + str(getattr(x,key,None))
            else:
                #print "Not a list or dict"
                is_true = getattr(x,key, None) == query[key]
            
            if is_true:
                #print "APPEND"
                return_values.add(x)
        
        return return_values

    try:
        l = list(RAM_ALL[cls.COLLECTION_NAME])
    except KeyError:
        return []
    else:
        return _sort(search(l, query), sort) #i think i need the list here for weakref reasons

def _quick_sort(values):
    pass



