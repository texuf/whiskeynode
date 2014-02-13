from bson.objectid import ObjectId
from operator import attrgetter
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

def from_cache(cls, data, dirty=True):
    try:
        return RAM[data['_id']]
    except KeyError:
        return cls(init_with=data, dirty=dirty)

def clear_cache():
    ''' for testing '''
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


def find(cls, query, sort):
    ''' RETURNS SORTED HIGHEST TO LOWEST _id (most recent first)'''
    if query == {}:
        try:
            l = list(RAM_ALL[cls.COLLECTION_NAME])
            return sorted([x for x in l], key=attrgetter('_id'), reverse=True)
        except KeyError:
            return []
    
    if '$or' == query.keys()[0]:
        #can be optimized
        lol = [find(cls, x, sort) for x in query['$or']] #list of lists (lol)
        return sorted(set(itertools.chain(*lol)), key=attrgetter(sort[0]), reverse=sort[1]==-1)
    
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
                    return sorted([RAM[x] for x in ids if x in RAM], key=attrgetter(sort[0]), reverse=sort[1]==-1)
                elif keys[0] == '$gt':
                    try:
                        l = list(RAM_ALL[cls.COLLECTION_NAME])
                        cmp_val = query['_id']['$gt']
                        return sorted([x for x in l if x._id > cmp_val], key=attrgetter(sort[0]), reverse=sort[1]==-1)
                    except KeyError:
                        return []

        raise WhiskeyCacheException('Whiskey cache only supports the $in, and $gt paramaters, for deeper searches like [%s] use the COLLECTION' % str(query['_id']['$in']))
    try:
        return_values = set([])
        search_set = list(RAM_ALL[cls.COLLECTION_NAME])
        for x in search_set:
            is_true = True
            for key in query.keys():
                if key[0] == '$' and key != '$in':
                    raise WhiskeyCacheException('Whiskey cache only supports the $in paramater, for deeper searches like [%s] use the COLLECTION' % str(query[key]))
                if type(query[key]) is dict:
                    try:
                        is_true = getattr(x, key, None) in query[key]['$in']
                    except KeyError:
                        raise WhiskeyCacheException('Whiskey cache only supports the $in paramater, for deeper searches like [%s] use the COLLECTION' % str(query[key]))
                else:
                    is_true = getattr(x,key, None) == query[key]
                if not is_true:
                    break
            if is_true:
                return_values.add(x)
        return sorted(return_values, key=attrgetter(sort[0]), reverse=sort[1]==-1)
    except KeyError:
        return []

def _quick_sort(values):
    pass



