


if __name__ == "__main__":
    import nose
    if not nose.run():
        import sys
        global mongo
        import mongomock as mongo
    
        sys.exit(123) #if the tests fail, return non zero value to break build script
    
