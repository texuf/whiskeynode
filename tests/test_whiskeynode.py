from bson.objectid import ObjectId
from bson.dbref import DBRef
from datetime import datetime
from functools import partial
from unittest import TestCase
from whiskeynode import WhiskeyNode
from whiskeynode import whiskeycache
from whiskeynode.db import db
from whiskeynode.exceptions import InvalidFieldNameException, FieldNameNotDefinedException
import mock

#properties that aren't listed in fields shouldn'd save
class D1(WhiskeyNode):
    COLLECTION_NAME = 'D1'
    COLLECTION = db[COLLECTION_NAME]
    def __init__(self, *args, **kwargs):
        WhiskeyNode.__init__(self, *args, **kwargs)
    @property
    def myJaws(self):
        return 'how_small'

#properties that are listed in fields should save
how_big = 'Very big.'

class D2(WhiskeyNode):
    COLLECTION_NAME = 'D2'
    COLLECTION = db[COLLECTION_NAME]
    FIELDS = {
        'myJaws':unicode,
    }
    def __init__(self, *args, **kwargs):
        WhiskeyNode.__init__(self, *args, **kwargs)
    @property
    def myJaws(self):
        return how_big

class D3(WhiskeyNode):
    COLLECTION_NAME = 'D3'
    COLLECTION = db[COLLECTION_NAME]
    FIELDS = {
        'myJaws':unicode,
        'some_dict':dict,
        'some_list':list,
    }
    def __init__(self, *args, **kwargs):
        WhiskeyNode.__init__(self, *args, **kwargs)
    
class D5(WhiskeyNode):
    COLLECTION_NAME = 'd5'
    COLLECTION = db[COLLECTION_NAME]
    FIELDS = {
        'myJaws':unicode,
    }
    def __init__(self, *args, **kwargs):
        WhiskeyNode.__init__(self, *args, **kwargs)

class DInvalid(WhiskeyNode):
    COLLECTION_NAME = 'DInvalid'
    COLLECTION = db[COLLECTION_NAME]
    FIELDS = {
        'connections':unicode,
        'recepeptors':unicode,
        '_dict':dict
    }
    def __init__(self, *args, **kwargs):
        WhiskeyNode.__init__(self, *args, **kwargs)


class DocumentBaseTest(TestCase):
    def tearDown(self):
        WhiskeyNode.COLLECTION.drop()

    def test_init_should_return_a_document(self):
        class A(WhiskeyNode):pass
        d = A()
        self.assertIsInstance(d, WhiskeyNode)

    def test_render(self):
        d = D3()
        dic = d.render()
        self.assertTrue('myJaws' in dic.keys())
        self.assertTrue('_id' not in dic.keys())

    def test_save_find_remove(self):
        d = D3()
        d.save()
        c = D3.COLLECTION.find({'_id':d._id})
        self.assertTrue(c.count() == 1)
        d.remove()
        c = D3.COLLECTION.find({'_id':d._id})
        self.assertTrue(c.count() == 0)

    def test_properties_save(self):
        how_small = 'Very small.'
        
        d1 = D1()
        d1.save()
        d1_returned = d1.COLLECTION.find_one({'_id':d1._id})
        self.assertTrue(d1_returned is not None)
        self.assertTrue(d1_returned.get('myJaws') is None)
        
        d2 = D2()
        d2.save()

        d2_returned = d2.COLLECTION.find_one({'_id':d2._id})
        #print "d2_returned: " + str(d2_returned)
        self.assertTrue(d2_returned is not None)
        self.assertTrue(d2_returned.get('myJaws') is not None)
        self.assertTrue(d2_returned['myJaws'] == how_big)

    def test_update(self):
        how_big = 'So big.'
        class A(WhiskeyNode):pass
        d = A()
        
        try:
            d.update({'myJaws':'Are so small.'}) #updates should ignore properties that aren't in Fields
        except FieldNameNotDefinedException as e:
            pass
        else:
            raise FieldNameNotDefinedException('Updating with invalid field names should raise an exception.')

        d1 = D3()
        d1.update({'myJaws':how_big})
        self.assertTrue(d1.myJaws == how_big)

        d1.save()
        d1_returned = D3.COLLECTION.find_one({'_id':d1._id})
        self.assertTrue(d1_returned['myJaws'] == how_big)

        d2 = D3.from_dict({'myJaws':how_big, 'someOtherProp':True})
        d2.save()
        d2_returned = D3.COLLECTION.find_one({'_id':d2._id})
        self.assertTrue(d2_returned.get('myJaws') == how_big)
        self.assertTrue(d2_returned.get('someOtherProp') == True)


    def test_from_dict(self):
        how_big = 'So big.'
        d = D3.from_dict({'myJaws':how_big})
        d.save()
        
        d2 = D3.COLLECTION.find_one({'_id':d._id})
        self.assertTrue(d2['myJaws'] == how_big)

    def test_ne(self):
        how_big = 'So big.'
        d = D3.from_dict({'myJaws':how_big})
        
        d2 = D3.find({'myJaws':{'$ne':'small'}})
        self.assertTrue(d in list(d2))
        
    def test_invalid_field_raises_error(self):
        try:
            d1 = DInvalid()
        except InvalidFieldNameException:
            pass
        else:
            raise InvalidFieldNameException("invalid field names should raise an error")

    def test_save(self):
        d1 = D3({'some_prop':'prop', 'some_dict':{'hey':'heyhey', 'um':{'yeah':'thats right'}}, 'some_list':['a', 'b', 'c']})
        self.assertTrue(d1._diff_dict(d1._to_dict()) or d1._dirty)
        with mock.patch('mongomock.Collection.save') as save_mock:
            d1.save()
            #print 'should save'
            self.assertTrue(save_mock.call_count == 1)

        self.assertFalse(d1._diff_dict(d1._to_dict()) or d1._dirty)
        with mock.patch('mongomock.Collection.save') as save_mock:
            d1.save()
            #print 'should not save'
            self.assertTrue(save_mock.call_count == 0)
        
        d1.myJaws = 'Big.'
        self.assertTrue(d1._diff_dict(d1._to_dict()) or d1._dirty)
        with mock.patch('mongomock.Collection.save') as save_mock:
            d1.save()
            #print 'should save'
            self.assertTrue(save_mock.call_count == 1)

        #print 'should not save'
        d = d1._to_dict()
        d1 = D3.from_dict(d)
        self.assertFalse(d1._diff_dict(d1._to_dict()) or d1._dirty)
        with mock.patch('mongomock.Collection.save') as save_mock:
            d1.save()
            #print 'should not save'
            self.assertTrue(save_mock.call_count == 0)

        #print 'should save'
        d1.lastModified = datetime.now()
        self.assertTrue(d1._diff_dict(d1._to_dict()) or d1._dirty)
        with mock.patch('mongomock.Collection.save') as save_mock:
            d1.save()
            #print 'should save'
            self.assertTrue(save_mock.call_count == 1)

        d1.some_dict['hey'] = 'heyheyhey'
        self.assertTrue(d1._diff_dict(d1._to_dict()) or d1._dirty)
        with mock.patch('mongomock.Collection.save') as save_mock:
            d1.save()
            #print 'should save'
            self.assertTrue(save_mock.call_count == 1)

        d1.some_dict['um']['yeah'] = 'what you say?'
        self.assertTrue(d1._diff_dict(d1._to_dict()) or d1._dirty)
        with mock.patch('mongomock.Collection.save') as save_mock:
            d1.save()
            #print 'should save'
            self.assertTrue(save_mock.call_count == 1)


        d1.some_list.append('f')
        self.assertTrue(d1._diff_dict(d1._to_dict()) or d1._dirty)
        with mock.patch('mongomock.Collection.save') as save_mock:
            d1.save()
            #print 'should save'
            self.assertTrue(save_mock.call_count == 1)


    def test_find(self):
        D3.COLLECTION.drop()
        d1 = D3()
        d1.save()
        d2 = D3()
        d2.save()
        d3 = D3()
        d3.save()
        d4 = D3()
        d4.save()
        result = list(D3.find())
        #print "result: "+ str(len(result))
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) == 4)
        self.assertIsInstance(result[0], D3)

        result2 = list(D3.find({'_id':{'$in':[d1._id, d2._id, d3._id]}}))
        self.assertTrue(len(result2) == 3)

    def test_whiskeycursor_next(self):
        D3.COLLECTION.drop()

        dees = [D3(), D3(), D3()]
        for d in dees:
            d.save()

        whiskeycache.clear_cache()

        whiskey_cursor = D3.find()
        nexted = whiskey_cursor.next()
        self.assertTrue(nexted._id == dees[2]._id)
        self.assertTrue(len(whiskey_cursor)==len(dees)-1)
        
        whiskey_cursor = D3.find()
        for i,d in enumerate(whiskey_cursor):
            index = len(dees) - i - 1
            self.assertTrue(d._id == dees[index]._id)




    def test_from_db_ref(self):
        #create a doc, tell it how big my balls are
        how_big = 'So big.'
        d = D5()
        d.myJaws = how_big
        d.save()

        #create a db ref, these save natively in the db, but they are about as usefull as a whole in a piece of toast
        dbref = DBRef(d.COLLECTION_NAME, d._id)

        whiskeycache.clear_cache()

        class A(WhiskeyNode):pass
        from_ref = A.from_dbref(dbref.collection, dbref.id)
        self.assertTrue(from_ref.get_field('myJaws') == how_big)
        #test that i can save a property on this generic document,
        even_bigger = 'even bigger...'

        from_ref.add_field('myJaws', unicode)
        self.assertTrue(from_ref.myJaws == how_big)
        from_ref.myJaws = even_bigger
        from_ref.save()

        whiskeycache.clear_cache()

        #make sure we saved
        from_ref3 = A.from_dbref(dbref.collection, dbref.id)
        self.assertTrue(from_ref3.get_field('myJaws') == even_bigger)


        whiskeycache.clear_cache()

        #retreving the doc with the proper class should make things happy
        from_ref2 = D5.from_dbref(dbref.collection, dbref.id)
        self.assertTrue(from_ref2.get_field('myJaws') == even_bigger)
        self.assertFalse(from_ref2.myJaws == how_big)
        self.assertTrue(from_ref2.myJaws == even_bigger)


    def test_or_query(self):
        D3.COLLECTION.drop()
        whiskeycache.clear_cache()
        theese_dees = [D3({'myJaws':'big'}),D3({'myJaws':'small'}),D3({'myJaws':'just right'})]
        self.assertTrue(
                D3.find(
                        {'myJaws':'big'}
                    ).count() == 1
            )
        self.assertTrue(
                D3.find(
                        {
                            '$or':[
                                    {'myJaws':'big'},
                                    {'myJaws':'small'},
                                ]
                        }
                    ).count() == 2
            )
        self.assertTrue(
                D3.find(
                        {
                            '$or':[
                                    {'myJaws':'big'},
                                    {'myJaws':'small'},
                                    {'myJaws':'just right'},
                                ]
                        }
                    ).count() == 3
            )
        
        self.assertTrue(
                D3.find(
                        {
                            'myJaws':'big',
                            'someOtherVal':None,
                            '$or':[
                                    
                                    {'myJaws':'small'},
                                    {'myJaws':'just right'},
                                ]
                        }
                    ).count() == 3
            )
        
        
    def test_skip(self):
        D3.COLLECTION.drop()
        whiskeycache.clear_cache()
        theese_dees = [D3({'myJaws':'1'}),D3({'myJaws':'2'}),D3({'myJaws':'3'})]
        self.assertEqual(D3.find({}, skip=2).count(), 1)
        self.assertEqual(D3.find({}, sort=[('myJaws',1)], skip=2).next().myJaws, '3')
        self.assertEqual(D3.find({}, skip=4).count(), 0)
        
    def test_dequeue(self):
        D3.drop()
        dees = []
        D_COUNT = 100
        for i in range(D_COUNT):
            d = D3({'myJaws':'so sweaty'})
            d.save()
            dees.append(d)

        cursor = D3.find({}, sort=[('myJaws', 1)]) 
        count = 0
        for x in cursor:
            count += 1

        self.assertEqual(count, D_COUNT)





