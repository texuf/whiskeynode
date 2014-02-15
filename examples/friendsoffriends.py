
'''
to run in python terminal:
python -c "execfile('examples/friendsoffriends.py')"
'''
from examples.helpers import Nameable
from random import random
from whiskeynode import WhiskeyNode
from whiskeynode.db import db
from whiskeynode.edges import Edge
from whiskeynode.terminals import outbound_node, bidirectional_list, inbound_list, bidirectional_list


'''

this is an example of finding friends of friends. The query is pretty borked because our 
bidirectional friends terminal isn't directed, so we have to search for inbound and outbound relationsships

'''


class User(WhiskeyNode, Nameable):
    COLLECTION_NAME =   'example_friendsoffriends_users'
    COLLECTION =        db[COLLECTION_NAME]
    FIELDS =            {
                            'name':unicode,
                        }
    @classmethod
    def init_terminals(cls):
        cls.TERMINALS = {
                            'friends':    bidirectional_list(User),
                        }





if __name__ == '__main__':
    print '\n===Friends of Friends Example===\n'

    users = [
        User.from_name('George Carlin'),
        User.from_name('Tom Waits'),
        User.from_name('Bubba'),
        User.from_name('George Harison'),
        User.from_name('Montell Williams'),
        User.from_name('George Clooney'),
        User.from_name('Kevin Bacon'),
    ]

    previous_user = None
    for user in users:
        if previous_user:
            previous_user.friends.append(user)
        previous_user = user

    for user in users:
        print '%s is friends with: ' % user.name, [x.name for x in user.friends]


    map(lambda x:x.save(), users)

    user_a = users[0]
    user_b = users[-1]

    friend_ids = [user_a._id]

    count = 0

    #look at all george's friends, then look at all of their friends, then look at all of their friends, until kevin's id is returned

    while(True):
        #get friends
        friends_of_friend_ids = Edge.COLLECTION.find({
                '$or':[
                    {
                        '$and':[
                            {
                                'name':'friends',
                                'outboundCollection':User.COLLECTION_NAME,
                                'outboundId':{'$in':friend_ids},
                            },
                            {
                                'name':'friends',
                                'outboundCollection':User.COLLECTION_NAME,
                                'inboundId':{'$nin':friend_ids},
                            }
                        
                        ]
                    },
                    {
                        '$and':[
                            {
                                'name':'friends',
                                'outboundCollection':User.COLLECTION_NAME,
                                'inboundId':{'$in':friend_ids},
                            },
                            {
                                'name':'friends',
                                'outboundCollection':User.COLLECTION_NAME,
                                'outboundId':{'$nin':friend_ids},
                            }
                        
                        ]
                    }
                ]
                
                    
            }).distinct('inboundId')

        if len(friends_of_friend_ids) == 0:
            print '%s and %s are not connected' % (user_a.name, user_b.name)
            break
        if user_b._id in friends_of_friend_ids: 
            print 'Found %s and %s are seperated by %d relationships' % (user_a.name, user_b.name, count + 1)
            break
        else:
            count = count + 1
            friend_ids = friend_ids + friends_of_friend_ids

