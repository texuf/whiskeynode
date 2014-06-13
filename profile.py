import sys
import timeit


print 'fuck yes'


def run_profile():
    print 'oh yeah'
    setup='''
from whiskeynode import WhiskeyNode
from whiskeynode import whiskeycache
from whiskeynode.db import db

default_sort = [('_id', -1)]

class Node(WhiskeyNode):
    COLLECTION_NAME = 'test_node'
    COLLECTION = db[COLLECTION_NAME]
    FIELDS = {
        'myVar':int,
    }
    def __init__(self, *args, **kwargs):
        WhiskeyNode.__init__(self, *args, **kwargs)
nodes = [Node({'myVar':i}) for i in range(10000)]
'''

    query='''
whiskeycache.find(Node, {"myVar":{"$gt":500}}, default_sort)
    '''

    N = 1
    R = 3
    print timeit.repeat(query, setup=setup, repeat=R, number=N)


if __name__ == "__main__":
    run_profile()
