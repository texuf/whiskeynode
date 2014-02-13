'''
because sometimes you want a boolean that defaults to true
'''

#suppored types from pymongo:
'''
    ===================================  =============  ===================
    Python Type                          BSON Type      Supported Direction
    ===================================  =============  ===================
    None                                 null           both
    bool                                 boolean        both
    int [#int]_                          int32 / int64  py -> bson
    long                                 int64          both
    float                                number (real)  both
    string                               string         py -> bson
    unicode                              string         both
    list                                 array          both
    dict / `SON`                         object         both
    datetime.datetime [#dt]_ [#dt2]_     date           both
    compiled re                          regex          both
    `bson.binary.Binary`                 binary         both
    `bson.objectid.ObjectId`             oid            both
    `bson.dbref.DBRef`                   dbref          both
    None                                 undefined      bson -> py
    unicode                              code           bson -> py
    `bson.code.Code`                     code           py -> bson
    unicode                              symbol         bson -> py
    bytes (Python 3) [#bytes]_           binary         both
    ===================================  =============  ===================
'''

#more types

def _true_bool():
    return True

def _none():
    return None



class FieldDict(dict):
    def __getattr__(self, attr):
        return self.get(attr, None)
    __setattr__= dict.__setitem__
    __delattr__= dict.__delitem__

    def __repr__(self):
        ret_val = ['{\n']
        keys = self.keys()
        keys.sort()
        for key in keys:
            ret_val.append('  %s: %r\n' % (key, self[key]))
        ret_val.append('}')
        return ''.join(ret_val)
