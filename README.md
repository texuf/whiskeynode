whiskeynode
===========

A graph ORM for MongoDB with a weak-reference application cache.

##Philosophy

Whiskeynode forces you to strictly define your models and the relationships between them, and stores relationships in a graph like way. It is good for rapidly prototyping a project with nebulious or changing specifications and it's quick enough to run in a production environment. It should also ease the pain of migrating to another database, if the decision is made to go with something other than MongoDb

##Usage

*To follow this example, first run the steps in the [Installation](https://github.com/texuf/whiskeynode#installation) section of this readme, then type 'python' to open a python terminal in your directory.*

In this example we're going to create activities, create users, assign activities to users, and find users who have activites that are related to your own.

####Setup: Declare your models much like you would in any other MongoDB ORM

```

from examples.helpers import Nameable
from random import random
from whiskeynode import WhiskeyNode
from whiskeynode.db import db
from whiskeynode.edges import Edge
from whiskeynode.terminals import outbound_node, outbound_list, inbound_list

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
```


###Part 1: Create a user named 'John' and and activity named 'dancing'

```

john = User.from_name('John')
dancing = Activity.from_name('dancing')
```


Add 'dancing' to John's activities

```

john.activities.append(dancing)
print dancing in john.activities
>>>True
```


So, now John has 'dancing' in his activities, but let's check to see if john is in dancing's users

```

print john in dancing.users
>>>True
```


What's going on here? John is an instance of a User, which has an outbound list of Activity's. When we append dancing to John's activities, an edge is created that references both objects. 


###Part 2: Create a bunch of users and a bunch of activities

```

users = [
    User.from_name('George Carlin'),
    User.from_name('Tom Waits'),
    User.from_name('Bubba'),
]

activities = [
    Activity.from_name('flying'),
    Activity.from_name('comedy'),
    Activity.from_name('enormous jaws'),
    Activity.from_name('karate'),
    Activity.from_name('hula hooping'),
    Activity.from_name('knitting'),
    Activity.from_name('x-ray vision'),
]

print [x.name for x in users]
print [x.name for x in activities]
>>>['George Carlin', 'Tom Waits', 'Bubba']
>>>['flying', 'comedy', 'enormous jaws', 'karate', 'hula hooping', 'knitting', 'x-ray vision']
```


Now give each users a few activities at random (randomizing makes testing less boring, wouldn't you say?)

```

for user in users:
    index = len(activities)-1
    while(True):
        index = int(round(float(index) - random() * len(activities) /2.0 ))
        if index < 0: break #mid statement break... ugh
        user.activities.append(activities[index])
    print '%s has been assigned the activities: ' % user.name, [x.name for x in user.activities]

    >>>George Carlin has been assigned the activities:  ['flying', 'enormous jaws', 'karate', 'knitting']
    >>>Tom Waits has been assigned the activities:  ['flying', 'karate', 'hula hooping']
    >>>Bubba has been assigned the activities:  ['enormous jaws', 'knitting']
```


So, let's explore the users activities and see who has what in common

```

for user in users:
    print '\nLets look at %s\'s activities...' % user.name
    for activity in user.activities:
        print '%s shares the activity \'%s\' with: ' % (user.name, activity.name), [x.name for x in activity.users if x.name != user.name]

>>Lets look at George Carlin's activities...
>>George Carlin shares the activity 'flying' with:  ['Tom Waits']
>>George Carlin shares the activity 'enormous jaws' with:  ['Bubba']
>>George Carlin shares the activity 'karate' with:  ['Tom Waits']
>>George Carlin shares the activity 'knitting' with:  ['Bubba']
>>
>>Lets look at Tom Waits's activities...
>>Tom Waits shares the activity 'flying' with:  ['George Carlin']
>>Tom Waits shares the activity 'karate' with:  ['George Carlin']
>>Tom Waits shares the activity 'hula hooping' with:  []
>>
>>Lets look at Bubba's activities...
>>Bubba shares the activity 'enormous jaws' with:  ['George Carlin']
>>Bubba shares the activity 'knitting' with:  ['George Carlin']
```


###Part 3: Use the Edge node to find users with the same activity

```

#first lets save all of our models
tmp = map(lambda x: x.save(), users)
tmp = map(lambda x: x.save(), activities)
#then find all users with each activity in just two db queries
for activity in activities:
    user_ids = Edge.COLLECTION.find(
                                {
                                    'name':'activities', 
                                    'outboundCollection':User.COLLECTION_NAME,
                                    'inboundCollection':Activity.COLLECTION_NAME,
                                    'inboundId':activity._id
                                }
                            ).distinct('outboundId')
    print 'Users who have the activity \'%s\': ' % activity.name, \
            [x.name for x in User.from_ids(user_ids)]

>>>Users who have the activity 'flying':  ['Tom Waits', 'George Carlin']
>>>Users who have the activity 'comedy':  []
>>>Users who have the activity 'enormous jaws':  ['Bubba', 'George Carlin']
>>>Users who have the activity 'karate':  ['Tom Waits', 'George Carlin']
>>>Users who have the activity 'hula hooping':  ['Tom Waits']
>>>Users who have the activity 'knitting':  ['Bubba', 'George Carlin']
>>>Users who have the activity 'x-ray vision':  []
```


This is exactly what WhiskeyNode is doing behind the scenes when you loop through over activity.users. With proper indexing this is a very efficient query. 

###Part 4: Find users with activities that are related to your activities.

This is fun right? Create some directed relationships between activities...

```

for activity in activities:
    for a2 in activities:
        if activity != a2 and random() > .75:
            activity.relatedAbilities.append(a2)
    activity.save()
    print '\'%s\' is related to ' % activity.name, [x.name for x in activity.relatedAbilities]

>>>'flying' is related to  ['x-ray vision', 'knitting', 'karate', 'enormous jaws']
>>>'comedy' is related to  ['karate']
>>>'enormous jaws' is related to  []
>>>'karate' is related to  ['comedy']
>>>'hula hooping' is related to  ['enormous jaws', 'flying']
>>>'knitting' is related to  ['hula hooping', 'enormous jaws', 'flying']
>>>'x-ray vision' is related to  ['hula hooping', 'comedy']
```


Now find related users the slow way

```

for user in users:
    print '\nLooking for users with activities related to %s\'s activities ' % user.name, [x.name for x in user.activities]
    for activity in user.activities:
        for related_ability in activity.relatedAbilities:
            if related_ability not in user.activities and len(related_ability.users) > 0:
                print '\'%s\' is related to \'%s\', %s like(s) \'%s\'' % (
                                            activity.name, 
                                            related_ability.name, 
                                            str([x.name for x in related_ability.users if x is not user]), 
                                            related_ability.name
                                        )
>>>Looking for users with activities related to George Carlin's activities  ['flying', 'enormous jaws', 'karate', 'knitting']
>>>'knitting' is related to 'hula hooping', ['Tom Waits'] like(s) 'hula hooping'

>>>Looking for users with activities related to Tom Waits's activities  ['flying', 'karate', 'hula hooping']
>>>'flying' is related to 'knitting', ['Bubba', 'George Carlin'] like(s) 'knitting'
>>>'flying' is related to 'enormous jaws', ['Bubba', 'George Carlin'] like(s) 'enormous jaws'
>>>'hula hooping' is related to 'enormous jaws', ['Bubba', 'George Carlin'] like(s) 'enormous jaws'

>>>Looking for users with activities related to Bubba's activities  ['enormous jaws', 'knitting']
>>>'knitting' is related to 'hula hooping', ['Tom Waits'] like(s) 'hula hooping'
>>>'knitting' is related to 'flying', ['Tom Waits', 'George Carlin'] like(s) 'flying'
```


Woah! Three nested for loops? Loads of db calls that probably won't be cached in your application... lets see if we can do better

```

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

>>>Users who have activities related to George Carlin's  activities  [('Tom Waits', 'hula hooping')]
>>>Users who have activities related to Tom Waits's  activities  [('George Carlin', 'knitting'), ('Bubba', 'knitting'), ('Bubba', 'enormous jaws'), ('George Carlin', 'enormous jaws')]
>>>Users who have activities related to Bubba's  activities  [('Tom Waits', 'flying'), ('George Carlin', 'flying'), ('Tom Waits', 'hula hooping')]
```


That's better, hit the db 3 times for the graph traversal, then lookup the users and activities that are returned (this last line could be optimized to grab the objects in two calls over the wire)

Well, that's all for now... Let me know what you think.


##Examples

Check out [whiskeynode-login](https://github.com/texuf/whiskeynode-login) for a full example




##Installation

To use in your python project::

```

pip install -e git://github.com/texuf/whiskeynode.git#egg=whiskeynode
    test
```


To download, setup and perfom tests, run the following commands on Mac / Linux::

```

get clone <repo>
cd <reponame>
virtualenv venv --distribute
source venv/bin/activate
python setup.py install
pip install nose mock
python run_tests.py
```


##Acknowledgements
 * Zach Carter (zcarter)




created for [www.mightyspring.com](www.mightyspring.com)

```

   __  ____      __   __         ____         _          
  /  |/  (_)__ _/ /  / /___ __  / __/__  ____(_)__  ___ _
 / /|_/ / / _ `/ _ \/ __/ // / _\ \/ _ \/ __/ / _ \/ _ `/
/_/  /_/_/\_, /_//_/\__/\_, / /___/ .__/_/ /_/_//_/\_, / 
         /___/         /___/     /_/              /___/  
```


