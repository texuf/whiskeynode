
'''
to run in python terminal:
python -c "execfile('examples/activities.py')"
'''
from examples.helpers import Nameable
from random import random
from whiskeynode import WhiskeyNode
from whiskeynode.db import db
from whiskeynode.edges import Edge
from whiskeynode.terminals import outbound_node, outbound_list, inbound_list, bidirectional_list


#
# User
# - User object, contains a list of activities
#
class User(WhiskeyNode, Nameable):
    COLLECTION_NAME =   'users'
    COLLECTION =        db[COLLECTION_NAME]
    FIELDS =            {
                            'name':unicode,
                        }
    @classmethod
    def init_terminals(cls):
        cls.TERMINALS = {
                            'activities':    outbound_list(Activity),
                        }

#
# Activity
# - Activity Object, contans a list of users that have this activity
#
class Activity(WhiskeyNode, Nameable):
    COLLECTION_NAME =   'activities'
    COLLECTION =        db[COLLECTION_NAME]
    FIELDS =            {
                            'name':unicode,
                        }
    @classmethod
    def init_terminals(cls):
        cls.TERMINALS = {
                            'users':        inbound_list(User, 'activities'),
                            'relatedAbilities':      outbound_list(Activity),
                        }


if __name__ == '__main__':
    

    print '\n===Activities Example===\n'

    print '\nPART 1:\n\nCreating a user named \'John\' and an activity named \'dancing\''

    #init a user and an activity
    john = User.from_name('John')
    dancing = Activity.from_name('dancing')
    
    print 'Adding dancing to John\'s activities'

    john.activities.append(dancing)

    if john in dancing.users:
        print 'John is in dancing\'s users.'
    else:
        print 'John is not in dancing\'s users'

    print '\nPART 2:\n\nCreating a bunch of users and a bunch of activities\n'

    users = [
        User.from_name('George Carlin'),
        User.from_name('Tom Waits'),
        User.from_name('Bubba'),
    ]

    print 'users:\n', [x.name for x in users], '\n'

    activities = [
        Activity.from_name('flying'),
        Activity.from_name('comedy'),
        Activity.from_name('enormous jaws'),
        Activity.from_name('karate'),
        Activity.from_name('hula hooping'),
        Activity.from_name('knitting'),
        Activity.from_name('x-ray vision'),
    ]

    print 'activities:\n', [x.name for x in activities], '\n'

    #give each person a few activities at random
    for user in users:
        index = len(activities)-1
        while(True):
            index = int(round(float(index) - random() * len(activities) /2.0 ))
            if index < 0: break #mid statement break for 'cleanliness'
            user.activities.append(activities[index])
        print '%s has been assigned the activities: ' % user.name, [x.name for x in user.activities]


    #do some exploration
    for user in users:
        print '\nLets look at %s\'s activities...' % user.name
        for activity in user.activities:
            print '%s shares the activity \'%s\' with: ' % (user.name, activity.name), [x.name for x in activity.users if x.name != user.name]


    print '\nPART 3:\n\nUse edge queries to find users'
    map(lambda x: x.save(), users)
    map(lambda x: x.save(), activities)

    for activity in activities:
        user_ids = Edge.COLLECTION.find(
                                    {
                                        'name':'activities', 
                                        'outboundCollection':User.COLLECTION_NAME,
                                        'inboundCollection':Activity.COLLECTION_NAME,
                                        'inboundId':activity._id
                                    }
                                ).distinct('outboundId')
        print 'Users who have the activity \'%s\': ' % activity.name, [x.name for x in User.from_ids(user_ids)]
    

    print '\nPART 4:\n\nFind users with activities that are related to your activities.'

    #give each activity some related activities
    print '\nEstablishing activity relationships...\n'
    for activity in activities:
        for a2 in activities:
            if activity != a2 and random() > .75:
                activity.relatedAbilities.append(a2)
        activity.save()
        print '\'%s\' is related to ' % activity.name, [x.name for x in activity.relatedAbilities]


    print '\nUsing silly slow way to find related users...'
    #search for related activities in the traditional way (lots of database queries here, lots of loops)
    for user in users:
        print '\nLooking for users with activities related to %s\'s activities ' % user.name, [x.name for x in user.activities]
        for activity in user.activities:
            for related_ability in activity.relatedAbilities:
                if related_ability not in user.activities and len(related_ability.users) > 0:
                    print '\'%s\' is related to \'%s\', %s like \'%s\'' % (
                                                related_ability.name, 
                                                activity.name, 
                                                str([x.name for x in related_ability.users if x is not user]), 
                                                related_ability.name
                                            )


    #instead use the graph, lets see if we can reduce the number of queries and loops
    print '\nUsing Edge queries to find related users...\n'
    for user in users:
        #get this user's activity ids
        ability_ids =       Edge.COLLECTION.find(
                                    {
                                        'name':'activities',
                                        'outboundId':user._id
                                    }
                                ).distinct('inboundId')
        #get activities related to this users activities
        related_ability_ids = Edge.COLLECTION.find(
                                    {
                                        'name':'relatedAbilities',
                                        'outboundId':{'$in':ability_ids},
                                        'inboundId':{'$nin':ability_ids}
                                    }
                                ).distinct('inboundId')
        #get users who have those activities
        edge_cursor =          Edge.COLLECTION.find(
                                    {
                                        'name':'activities',
                                        'outboundCollection':user.COLLECTION_NAME,
                                        'outboundId':{'$ne':user._id},
                                        'inboundId':{'$in':related_ability_ids},
                                    }
                                )
        #print the result
        print 'Users who have activities related to %s\'s  activities ' % user.name, \
            [(User.from_id(x['outboundId']).name, Activity.from_id(x['inboundId']).name) for x in edge_cursor]









