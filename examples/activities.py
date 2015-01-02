
'''
to run in python terminal:
python -c "execfile('examples/activities.py')"
'''
from bson.code import Code
from examples.helpers import Nameable, make_list
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
    COLLECTION_NAME =   'example_activities_users'
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
    COLLECTION_NAME =   'example_activities_activities'
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
    

    print '\nACTIVITIES\n'

    print 'PART 1: A User Named John and an Activity Called Dancing'

    #init a user and an activity
    john = User.from_name('John')
    dancing = Activity.from_name('dancing')
    
    print 'John starts dancing.'

    john.activities.append(dancing)

    if john in dancing.users:
        print 'John is dancing.'
    else:
        print 'John is not dancing'

    print '\nPART 2: Users Participate in Activities'

    users = [
        john,
        User.from_name('George Carlin'),
        User.from_name('Tom Waits'),
        User.from_name('Bubba'),
    ]

    print 'Our users are', make_list(users)

    activities = [
        dancing,
        Activity.from_name('flying'),
        Activity.from_name('comedy'),
        Activity.from_name('enormous jaws'),
        Activity.from_name('karate'),
        Activity.from_name('hula hooping'),
        Activity.from_name('knitting'),
        Activity.from_name('x-ray vision'),
    ]

    print 'Our activities are', make_list(activities)

    #give each person a few activities at random
    print 'Users are (randomly) starting to do activities...'
    for user in users:
        index = len(activities)-1
        while(True):
            index = int(round(float(index) - random() * len(activities) /2.0 ))
            if index >= 0: 
                user.activities.append(activities[index])
            else:
                break
        print user.name, 'started', make_list(user.activities)


    #do some exploration
    print 'Look at who is doing activities together.'
    for user in users:
        for activity in user.activities:
            print user.name, 'does', activity.name, 'with', make_list([x for x in activity.users if x != user])


    print '\nPART 3: Use edge queries to find users'
    users = map(lambda x: x.save(), users)
    activities = map(lambda x: x.save(), activities)

    for activity in activities:
        user_ids = Edge.COLLECTION.find(
                                    {
                                        'name':'activities', 
                                        'outboundCollection':User.COLLECTION_NAME,
                                        'inboundCollection':Activity.COLLECTION_NAME,
                                        'inboundId':activity._id
                                    }
                                ).distinct('outboundId')
        print 'Who is %s?' % activity.name, make_list(User.from_ids(user_ids))
    

    print '\nPART 4: Establish (Random) Activity Relationships, Find Related Activities Partners'

    #give each activity some related activities
    print 'Establishing activity relationships...'
    for activity in activities:
        for a2 in activities:
            if activity != a2 and random() > .75:
                activity.relatedAbilities.append(a2)
        activity.save()
        print activity.name.capitalize(), 'is now related to', make_list(activity.relatedAbilities)
    print 'Done...'

    print '\nPart 5: Using Silly Slow Way to Find Related Users...'
    #search for related activities in the traditional way (lots of database queries here, lots of loops)
    for user in users:
        print 'Looking for users with activities related to %s\'s activities' % user.name, make_list(user.activities)
        for activity in user.activities:
            print activity.name.capitalize() ,'is related to', make_list(activity.relatedAbilities)
            for related_ability in activity.relatedAbilities:
                if related_ability not in user.activities:
                    print user.name, 'should do', related_ability.name, 'with', make_list(filter(lambda x: x != user, related_ability.users))
                else:
                    print user.name, 'is already doing', related_ability.name, 'with', make_list(filter(lambda x: x != user, related_ability.users))


    #instead use the graph, lets see if we can reduce the number of queries and loops
    print '\nPart 6: Using Edge queries to find related users...'
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
        print 'Who has activities related to %s\'s  activities?' % user.name, \
            make_list(['%s does %s' % (User.from_id(x['outboundId']).name, Activity.from_id(x['inboundId']).name) for x in edge_cursor])


    print '\nPart 7: Using MongoDB Group aggregation to find users with common activites.'
    comp_user = User.find_one() 
    print "Finding users with activites in common with %s. \n%s's activities are: %s" %(comp_user.name, comp_user.name, str(make_list(comp_user.activities)))

    #Hark! Javascript?! Tell the database to tally results; we initialize the count to zero when we make our group call.
    reducer=Code("function(obj, result) {result.count+=1 }")
    query = {

                        'inboundId':{'$in':[act._id for act in list(comp_user.activities)]},
                        'name':'activities',
                        'outboundCollection':User.COLLECTION_NAME,
                        'outboundId': {'$ne':comp_user._id},
                    }

    common_activities_users = Edge.COLLECTION.group(key=['outboundId'], 
                                            condition=query,
                                            initial={"count": 0},
                                            reduce=reducer)

    print common_activities_users

    for cau in common_activities_users:
        print '%s has %s activities in common with %s'%(comp_user.name, cau['count'], User.from_id(cau['outboundId']).name)

