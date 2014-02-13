''' to run:
from whiskeynode.indexes import ensure_indexes
ensure_indexes()
'''

import pkgutil
import pyclbr
import whiskeynode

try:
    import nodes
except:
    nodes = None

def ensure_indexes(logger=None, do_print=True):
    if nodes:
        _ensure_index(nodes, logger, do_print)
    _ensure_index(whiskeynode, logger, do_print)

def _ensure_index(package, logger, do_print):
    prefix = package.__name__ + "."
    for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
        full_modname = prefix+modname
        outer_module = __import__(full_modname, fromlist="dummy")
        if not ispkg:
            
            #print "Found submodule %s (is a package: %s)" % (modname, ispkg)
            #print "inspected: "+str(classes)
            
            classes = pyclbr.readmodule(full_modname)
            module = getattr(package, modname)
            for key,value in classes.items():
                #print full_modname
                if 'Document' in value.super or 'WhiskeyNode' in value.super:
                    cls = getattr(module, value.name)
                    try:    
                        inst = cls()
                        for index in inst.ENSURE_INDEXES:
                            if isinstance(index, list) or index not in inst.ENSURE_UNIQUE_INDEXES:
                                dbug_msg = "ensuring index cls: %s collection: %s index: %s " % (full_modname, inst.COLLECTION_NAME, index)
                                if logger is not None:
                                    logger(dbug_msg)
                                elif do_print:
                                    print dbug_msg
                                inst.COLLECTION.ensure_index(index)
                        for index in inst.ENSURE_UNIQUE_INDEXES:
                            dbug_msg =  "ensuring unique index cls: %s collection: %s index: %s " % (full_modname, inst.COLLECTION_NAME, index)
                            if logger is not None:
                                logger(dbug_msg)
                            elif do_print:
                                print dbug_msg

                            if index not in inst.ENSURE_INDEXES:
                                raise Exception('All indexes in ENSURE_UNIQUE_INDEXES should also be in ENSURE_INDEXES')
                            inst.COLLECTION.ensure_index(index, unique=True)
                    except Exception, e:
                        pass
                        dbug_msg = "Failed to import %s %s" % (full_modname, str(e))
                        if logger is not None:
                            logger(dbug_msg)
                        elif do_print:
                            print dbug_msg
        else:
            _ensure_index(outer_module, logger, do_print)
                    


