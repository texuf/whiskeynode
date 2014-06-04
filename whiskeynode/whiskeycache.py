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
    ''' RETURNS SORTED HIGHEST TO LOWEST _id (most recent first)'''
    if query == {}:
        try:
            with lock:
                l = list(RAM_ALL[cls.COLLECTION_NAME])
            return _sort([x for x in l], sort)
        except KeyError:
            return []

#    if '$or' == query.keys()[0] and len(query) == 1:
#        #  can be optimized
#        lol = [find(cls, x, sort) for x in query['$or']]  #list of lists (lol)
#        return _sort(set(itertools.chain(*lol)), sort)

    if '_id' in query:
        if type(query['_id']) is ObjectId:
            try:
                return [RAM[query['_id']]]
            except KeyError:
                return []
        if type(query['_id']) is dict:
            keys = query['_id'].keys()
            if len(keys) == 1:
                if keys[0] == '$in':
                    ids = query['_id']['$in']
                    return _sort([RAM[x] for x in ids if x in RAM], sort)
                elif keys[0] == '$gt':
                    try:
                        l = list(RAM_ALL[cls.COLLECTION_NAME])
                        cmp_val = query['_id']['$gt']
                        return _sort([x for x in l if x._id > cmp_val], sort)
                    except KeyError:
                        return []

        raise WhiskeyCacheException('Whiskey cache only supports the $in, and $gt paramaters, for deeper searches like [%s] use the COLLECTION' % str(query['_id']['$in']))
    try:
        return_values = set([])
        with lock:
            search_set = list(RAM_ALL[cls.COLLECTION_NAME])
        for x in search_set:
            print "new doc"
            is_true = True
            for key in query:
                print "query key is " + str(key)
#                if key[0] == '$' and key != '$in':
#                    raise WhiskeyCacheException('Whiskey cache only supports the $in paramater, for deeper searches like [%s] with key [%s], use the COLLECTION' % (str(query[key]),key))
                if type(query[key]) is dict:
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
                    if key == '$or':
                        valid_k_v = {}
                        for d in query[key]:
                            for k in d:
                                if valid_k_v.get(k, None) == None:
                                    valid_k_v[k] = []
                                valid_k_v[k].append(d[k])
                        is_true = any([getattr(x, k, None) in valid_k_v[k] for k in valid_k_v])
                else:
                    is_true = getattr(x,key, None) == query[key]
                if not is_true:
                    break
            if is_true:
                print x.FIELDS
                print "^ is valid"
                print "we got here"
                return_values.add(x)
        print "length of return values"
        print len(_sort(return_values, sort))
        return _sort(return_values, sort)
    except KeyError:
        return []

def _quick_sort(values):
    pass



