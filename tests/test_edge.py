from unittest import TestCase
from whiskeynode.edges import Edge



class EdgeBaseTest(TestCase):
    def tearDown(self):
        Edge.COLLECTION.drop()


    def test_init_should_return_yeah(self):
        d = Edge()
        self.assertIsInstance(d, Edge)
        

