from bson.objectid import ObjectId
from unittest import TestCase
from whiskeynode import WhiskeyNode
from whiskeynode.db import db
from whiskeynode.edges import Edge
from whiskeynode.exceptions import InvalidConnectionNameException, InvalidTerminalException, InvalidTerminalStateException
from whiskeynode.terminals import outbound_node, inbound_node, outbound_list, inbound_list, bidirectional_list
from whiskeynode.terminaltypes import TerminalType
from whiskeynode import whiskeycache  


#Define a sub doc
class SubNode(WhiskeyNode):
    COLLECTION_NAME = 'subnode_collection'
    COLLECTION = db[COLLECTION_NAME]

    FIELDS =        {
                        'sub_prop':unicode,
                    }

    def __init__(self, *args, **kwargs):
        WhiskeyNode.__init__(self, *args, **kwargs)

    @classmethod
    def init_terminals(cls):
        cls.TERMINALS =    {
                                'parent': inbound_node(ParentNode, 'sub_node'),
                                'parents': inbound_list(ParentNode, 'sub_node_list')
                            }



#Define a parent doc that connects to the sub doc
class ParentNode(WhiskeyNode):
    COLLECTION_NAME = 'parent_collection'
    COLLECTION = db[COLLECTION_NAME]

    FIELDS =        {
                        'parent_prop':unicode,
                    }

    def __init__(self, *args, **kwargs):
        WhiskeyNode.__init__(self, *args, **kwargs)

    @classmethod
    def init_terminals(cls):
        cls.TERMINALS =    {
                                'sub_node':outbound_node(SubNode,create_on_request=True),
                                'sub_node_list':outbound_list(SubNode),
                            }



class InvaldConnectionsNode(WhiskeyNode):
    COLLECTION_NAME = 'invalid_collection'
    COLLECTION = db[COLLECTION_NAME]

    FIELDS =        {
                    }

    @classmethod
    def init_terminals(cls):
        cls.TERMINALS =    {
                                'terminals':outbound_node(
                                to_node_class=SubNode,
                                create_on_request=True,
                                )
                            }

class TreeNode(WhiskeyNode):
    COLLECTION_NAME = 'treenode_collection'
    COLLECTION = db[COLLECTION_NAME]
    FIELDS = {
                'name':unicode
             }

    @classmethod
    def init_terminals(cls):
        cls.TERMINALS =    {
                                'parent':outbound_node(TreeNode),
                                'children':inbound_list(TreeNode, 'parent'),
                            }


class NodeBaseConnectionTest(TestCase):
    def tearDown(self):
        WhiskeyNode.COLLECTION.drop()
        Edge.COLLECTION.drop()
        ParentNode.COLLECTION.drop()
        SubNode.COLLECTION.drop()

    def test_terminals(self):
        parent_node = ParentNode()
        self.assertIsInstance(parent_node, ParentNode)
        sub_node = parent_node.sub_node
        self.assertIsInstance(sub_node, SubNode)

        #save parent_node
        parent_node.parent_prop = 'Oh no'
        parent_node.sub_node.sub_prop = 'Oh yes'
        parent_node.save()

        #pull parent_node back out of the db
        parent_node_retrieved = ParentNode.from_id(parent_node._id)
        #make sure the parent doc matches the previous one, and that the sub doc id's match
        self.assertTrue(parent_node_retrieved._id ==  parent_node._id)
        self.assertTrue(parent_node_retrieved.sub_node._id ==  sub_node._id)
        #pull the sub doc out of the db, make sure the _id's match
        sub_node_retrieved = SubNode.from_id(sub_node._id)
        self.assertTrue(parent_node.sub_node._id == sub_node_retrieved._id)
        #make sure the property that we set matches
        self.assertTrue(parent_node.sub_node.sub_prop == sub_node_retrieved.sub_prop)

    def test_remove_node_removes_parent_connection(self):
        
        parent_node = ParentNode()
        sub_node = parent_node.sub_node
        parent_node.save()

        #remove the doc (delete it from the db)
        sub_node.remove()

        #make sure it no longer exists in the db
        self.assertTrue(SubNode.from_id(sub_node._id)==None)

        #make sure requesting it again makes a fresh copy
        #print "requesting fresh copy"
        sub_node2 = parent_node.sub_node
        #print "%s : %s " % (str(sub_node), str(sub_node2))
        self.assertTrue(sub_node._id != sub_node2._id)

    def test_assigning_subdoc(self):
        whiskeycache.clear_cache()
        #print '\n\nRAM: %s\n\nMORE_RAM: %s\n\n' % (whiskeycache.RAM, whiskeycache.MORE_RAM)
        sub_node = SubNode()
        parent_node = ParentNode()
        #print '\n\nRAM: %s\n\nMORE_RAM: %s\n\n' % (whiskeycache.RAM, whiskeycache.MORE_RAM)
        self.assertTrue(sub_node.parent == None)
        #you should be able to set the value of a connection before it's created
        parent_node.sub_node = sub_node
        #print '\n\nRAM: %s\n\nMORE_RAM: %s\n\n' % (whiskeycache.RAM, whiskeycache.MORE_RAM)
        #print 'sub.p '+str(sub_node.parent)
        #print 'parent '+str(parent_node)
        self.assertTrue(sub_node.parent == parent_node)

        parent_node.save()
        
        whiskeycache.clear_cache()

        parent_node2 = ParentNode.from_id(parent_node._id)
        self.assertTrue(parent_node2 == parent_node)
        #print "parent node id %s subnode id %s" % (str(parent_node2.sub_node._id), str(sub_node._id))
        self.assertTrue(parent_node2.sub_node._id == sub_node._id)

        #print "START"
        #print "DONE"
        #self.assertTrue(False)

        #setting the value again should throw an error

    def test_connection_with_reserved_name_throws_error(self):
        try:
            invalid_doc = InvaldConnectionsNode()
            self.assertTrue(False, "Invalid connection node should raise error")
        except InvalidConnectionNameException:
            pass

    def test_outbound_list_terminal(self):
        Edge.COLLECTION.drop()

        parent = ParentNode()
        for i in range(4):
            parent.sub_node_list.append(SubNode())

        parent.save()
        self.assertTrue(Edge.COLLECTION.find().count() == 4)

        whiskeycache.clear_cache()

        parent2 = ParentNode.from_id(parent._id)
        self.assertTrue(len(parent2.sub_node_list) == 4)

        parent2.sub_node_list.pop()
        self.assertTrue(len(parent2.sub_node_list) == 3)

        parent2.sub_node_list.extend([SubNode(), SubNode()])
        self.assertTrue(len(parent2.sub_node_list) == 5)

        parent2.save()
        #print parent2

        whiskeycache.clear_cache()

        parent3 = ParentNode.from_id(parent._id)
        #print parent3
        self.assertTrue(len(parent3.sub_node_list) == 5)

        #print "Edge.COLLECTION.find().count() %d" % Edge.COLLECTION.find().count()
        self.assertTrue(Edge.COLLECTION.find().count() == 5)
    
        #parent3.sub_node_list.insert(2, SubNode())

        parent3.sub_node_list.pop(1)

        parent3.sub_node_list.remove(parent3.sub_node_list[0])

        try:
            parent3.sub_node_list.append(ParentNode())
        except AssertionError, e:
            pass
        else:
            raise AssertionError('you can\'t append to inbound lists')

    def test_inbound_node(self):
        parent = ParentNode()
        sub = parent.sub_node
        parent.save()
        self.assertTrue(sub.parent == parent)

        try:    
            del sub.parent
        except AssertionError, e:
            pass
        else:
            raise AssertionError('you can\'t delete inbound nodes')

        #print 'removing parent'
        sub.parent.remove()
        self.assertTrue(sub.parent == None)

    def test_inbound_list(self):
        sub = SubNode()
        sub.save()
        p1 = ParentNode()
        p2 = ParentNode()
        p3 = ParentNode()

        p1.sub_node_list.append(sub)
        p2.sub_node_list.append(sub)
        p3.sub_node_list.append(sub)
        #print sub.parent
        p1.save()
        p2.save()
        p3.save()

        self.assertTrue(len(sub.parents) == 3)

        self.assertTrue(sub in sub.parents[0].sub_node_list) #oh fuck yes
        sub.save() #save again to test for infinite recursion (we're connected in a loop here)
        try:
            sub.parents.pop()
        except AssertionError, e:
            pass
        else:
            raise AssertionError('Removing from inbount terminal should assert')

        sub.remove()
        self.assertTrue(len(p1.sub_node_list) == 0)
        self.assertTrue(len(p2.sub_node_list) == 0)
        self.assertTrue(len(p3.sub_node_list) == 0)

    def test_bidirectional_node(self):
        return 
        '''
        a = BidirectionalNode()
        
        b = BidirectionalNode()

        c = BidirectionalNode()

        d = BidirectionalNode()




        print "dljfdd" + str(a.nodes)
        print "dljfdd" + str(b.nodes)
        print "dljfdd" + str(c.nodes)
        a.nodes.append(b)
        a.nodes.append(c)
        a.nodes.append(d)

        b.nodes.append(a)
        print "dljfdd" + str(b.nodes)
        self.assertTrue(len(a.nodes) == 3)
        self.assertTrue(len(b.nodes) == 1)
        self.assertTrue(len(c.nodes) == 1)

        c.nodes.append(b)
        self.assertTrue(len(b.nodes) == 2)
        self.assertTrue(len(c.nodes) == 2)
        '''

    def test_tree_node(self):
        t = TreeNode()
        t2 = TreeNode()
        t.parent = t2
        t.save()





