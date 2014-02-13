


import os



if __name__ == "__main__":
    os.environ['ENVIRONMENT'] = 'test'
    global mongo
    import mongomock as mongo
    from whiskeynode.indexes import ensure_indexes
    ensure_indexes(do_print=False)
    import nose
    nose.run()