


class WhiskeyNodeException(Exception):pass

'''
cache
'''
class WhiskeyCacheException(WhiskeyNodeException):pass


'''
node connections
'''
class ConnectionNotFoundException(WhiskeyNodeException):pass
class FieldNameNotDefinedException(WhiskeyNodeException):pass
class CollectionNotDefinedException(WhiskeyNodeException):pass
class BadEdgeRemovalException(WhiskeyNodeException):pass
class InvalidTerminalParameterException(WhiskeyNodeException):pass

'''
node naming conventions
'''
class InvalidNameException(WhiskeyNodeException):pass

class InvalidEdgeDataException(InvalidNameException):pass
class InvalidFieldNameException(InvalidNameException):pass
class InvalidConnectionNameException(InvalidNameException):pass
class InvalidTerminalException(InvalidNameException):pass
class InvalidTerminalOperationException(WhiskeyNodeException):pass
class InvalidTerminalStateException(InvalidNameException):pass


'''
edges
'''
class InvalidEdgeParameterException(WhiskeyNodeException):pass