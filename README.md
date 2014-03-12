whiskeynode
===========

A graph ORM for MongoDB with a weak-reference application cache.

##Installation

To use in your python project::

```

pip install -e git://github.com/texuf/whiskeynode.git#egg=whiskeynode
```

Install locally::

```

pip install -e git://github.com/texuf/whiskeynode.git#egg=whiskeynode
```

To download, setup and perfom tests, run the following commands on Mac / Linux::

```

get clone <repo>
cd <reponame>
virtualenv venv --distribute
source venv/bin/activate
python setup.py install
pip install nose mock
```

To run tests:
```

python tests
```

To run this examples:

```

python -c "execfile('examples/activities.py')"
```

##Philosophy

Whiskeynode forces you to strictly define your models and the relationships between them, and stores relationships in a graph like way. It is good for rapidly prototyping a project with nebulious or changing specifications and it's quick enough to run in a production environment. It should also ease the pain of migrating to another database, if the decision is made to go with something other than MongoDb

##Usage

*To follow this example, first run the steps in the [Installation](https://github.com/texuf/whiskeynode#installation) section of this readme, then type 'python' to open a python terminal in your directory.*

In this example we're going to create activities, create users, assign activities to users, and find users who have activites that are related to your own.

####Setup: Declare your models much like you would in any other MongoDB ORM

```

from examples.helpers import Nameable, make_list
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
    john,
    User.from_name('George Carlin'),
    User.from_name('Tom Waits'),
    User.from_name('Bubba'),
]

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

print 'Our users are', make_list(users)
print 'Our activities are', make_list(activities)
>>>Our users are John, George Carlin, Tom Waits and Bubba.
>>>Our activities are dancing, flying, comedy, enormous jaws, karate, hula hooping, knitting and x-ray vision.
```


Now give each users a few activities at random (randomizing makes testing less boring, wouldn't you say?)

```

for user in users:
    index = len(activities)-1
    while(True):
        index = int(round(float(index) - random() * len(activities) /2.0 ))
        if index >= 0: 
            user.activities.append(activities[index])
        else:
            break
    print user.name, 'started', make_list(user.activities)

>>>John started enormous jaws, knitting and dancing.
>>>George Carlin started comedy and hula hooping.
>>>Tom Waits started dancing, flying and karate.
>>>Bubba started flying, karate and knitting.
```


So, let's explore the users activities and see who has what in common

```

for user in users:
    for activity in user.activities:
        print user.name, 'does', activity.name, 'with', make_list([x for x in activity.users if x != user])

>>>John does enormous jaws with none.
>>>John does knitting with Bubba.
>>>John does dancing with Tom Waits.
>>>George Carlin does comedy with none.
>>>George Carlin does hula hooping with none.
>>>Tom Waits does dancing with John.
>>>Tom Waits does flying with Bubba.
>>>Tom Waits does karate with Bubba.
>>>Bubba does flying with Tom Waits.
>>>Bubba does karate with Tom Waits.
>>>Bubba does knitting with John.

```


###Part 3: Use the Edge node to find users with the same activity

```

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

>>>Who is dancing? Tom Waits and John.
>>>Who is flying? Bubba and Tom Waits.
>>>Who is comedy? George Carlin.
>>>Who is enormous jaws? John.
>>>Who is karate? Bubba and Tom Waits.
>>>Who is hula hooping? George Carlin.
>>>Who is knitting? Bubba and John.
>>>Who is x-ray vision? none.

```


This is exactly what WhiskeyNode is doing behind the scenes when you loop through over activity.users. With proper indexing this is a very efficient query. 

###Part 4: Find users with activities that are related to your activities.

This is fun right? Create some directed relationships between activities...

```

for activity in activities:
    for a2 in activities:
        if activity != a2 and random() > .75:
            activity.relatedAbilities.append(a2)
    activity = activity.save()
    print activity.name.capitalize(), 'is now related to', make_list(activity.relatedAbilities)

>>>Dancing is now related to x-ray vision, hula hooping and enormous jaws.
>>>Flying is now related to none.
>>>Comedy is now related to knitting and enormous jaws.
>>>Enormous jaws is now related to hula hooping.
>>>Karate is now related to x-ray vision, knitting, hula hooping and enormous jaws.
>>>Hula hooping is now related to flying.
>>>Knitting is now related to hula hooping and dancing.
>>>X-ray vision is now related to karate and dancing.
```


Now find related users the slow way

```
for user in users:
    print 'Looking for users with activities related to %s\'s activities' % user.name, make_list(user.activities)
    for activity in user.activities:
        print activity.name.capitalize() ,'is related to', make_list(activity.relatedAbilities)
        for related_ability in activity.relatedAbilities:
            if related_ability not in user.activities:
                print user.name, 'should do', related_ability.name, 'with', make_list(filter(lambda x: x != user, related_ability.users))
            else:
                print user.name, 'is already doing', related_ability.name, 'with', make_list(filter(lambda x: x != user, related_ability.users))

>>>Looking for users with activities related to John's activities enormous jaws, knitting and dancing.
>>>Enormous jaws is related to hula hooping.
>>>John should do hula hooping with George Carlin.
>>>Knitting is related to hula hooping and dancing.
>>>John should do hula hooping with George Carlin.
>>>John is already doing dancing with Tom Waits.
>>>Dancing is related to x-ray vision, hula hooping and enormous jaws.
>>>John should do x-ray vision with none.
>>>John should do hula hooping with George Carlin.
>>>John is already doing enormous jaws with none.
>>>Looking for users with activities related to George Carlin's activities comedy and hula hooping.
>>>Comedy is related to knitting and enormous jaws.
>>>George Carlin should do knitting with Bubba and John.
>>>George Carlin should do enormous jaws with John.
>>>Hula hooping is related to flying.
>>>George Carlin should do flying with Bubba and Tom Waits.
>>>Looking for users with activities related to Tom Waits's activities dancing, flying and karate.
>>>Dancing is related to x-ray vision, hula hooping and enormous jaws.
>>>Tom Waits should do x-ray vision with none.
>>>Tom Waits should do hula hooping with George Carlin.
>>>Tom Waits should do enormous jaws with John.
>>>Flying is related to none.
>>>Karate is related to x-ray vision, knitting, hula hooping and enormous jaws.
>>>Tom Waits should do x-ray vision with none.
>>>Tom Waits should do knitting with Bubba and John.
>>>Tom Waits should do hula hooping with George Carlin.
>>>Tom Waits should do enormous jaws with John.
>>>Looking for users with activities related to Bubba's activities flying, karate and knitting.
>>>Flying is related to none.
>>>Karate is related to x-ray vision, knitting, hula hooping and enormous jaws.
>>>Bubba should do x-ray vision with none.
>>>Bubba is already doing knitting with John.
>>>Bubba should do hula hooping with George Carlin.
>>>Bubba should do enormous jaws with John.
>>>Knitting is related to hula hooping and dancing.
>>>Bubba should do hula hooping with George Carlin.
>>>Bubba should do dancing with Tom Waits and John.
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
    print 'Who has activities related to %s\'s  activities?' % user.name, \
        make_list(['%s does %s' % (User.from_id(x['outboundId']).name, Activity.from_id(x['inboundId']).name) for x in edge_cursor])


>>>Who has activities related to John's  activities? George Carlin does hula hooping.
>>>Who has activities related to George Carlin's  activities? John does enormous jaws, John does knitting, Tom Waits does flying, Bubba does flying and Bubba does knitting.
>>>Who has activities related to Tom Waits's  activities? George Carlin does hula hooping, John does enormous jaws, John does knitting and Bubba does knitting.
>>>Who has activities related to Bubba's  activities? John does dancing, George Carlin does hula hooping, John does enormous jaws and Tom Waits does dancing.
```


That's better, hit the db 3 times for the graph traversal, then lookup the users and activities that are returned (this last line could be optimized to grab the objects in two calls over the wire)

Well, that's all for now... Let me know what you think.


##Examples

Check out [whiskeynode-login](https://github.com/texuf/whiskeynode-login) for a full example




##Acknowledgements
 * Zach Carter ([zcarter](https://github.com/zcarter))




created for [www.mightyspring.com](www.mightyspring.com)

```

   __  ____      __   __         ____         _          
  /  |/  (_)__ _/ /  / /___ __  / __/__  ____(_)__  ___ _
 / /|_/ / / _ `/ _ \/ __/ // / _\ \/ _ \/ __/ / _ \/ _ `/
/_/  /_/_/\_, /_//_/\__/\_, / /___/ .__/_/ /_/_//_/\_, / 
         /___/         /___/     /_/              /___/  
```


