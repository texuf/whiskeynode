whiskeynode
===========

A graph ORM for MongoDB with a weak-reference cache.

##Philosophy

Whiskeynode forces you to strictly define your models and the relationships between them, and stores relationships in a graph like way. It is good for rapidly prototyping a project with nebulious or changing specifications and it's quick enough to run in a production environment. It should also ease the pain of migrating to another database, if the decision is made to go with something other than MongoDb

##Usage

*To follow this example, first run the steps in the Installation section of this readme, then type 'python' to open a python terminal in your directory.*

####Setup: Declare your models much like you would in any other MongoDB ORM

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
                                'abilities':    outbound_list(Ability),
                            }

    class Ability(WhiskeyNode, Nameable):
        COLLECTION_NAME =   'abilities'
        COLLECTION =        db[COLLECTION_NAME]
        FIELDS =            {
                                'name':unicode,
                            }
        @classmethod
        def init_terminals(cls):
            cls.TERMINALS = {
                                'users':        inbound_list(User, 'abilities'),
                                'relatedAbilities':      outbound_list(Ability),
                            }


###Part 1: Create a user named 'John' and and ability named 'dancing'

    john = User.from_name('John')
    dancing = Ability.from_name('dancing')
    
Add 'dancing' to John's abilities

    john.abilities.append(dancing)
    print dancing in john.abilities
    >>>True

So, now John has 'dancing' in his abilities, but let's check to see if john is in dancing's users

    print john in dancing.users
    >>>True

What's going on here? John is an instance of a User, which has an outbound list of Ability's. When we append dancing to John's abilities, an edge is created that references both objects. 


###Part 2: Create a bunch of users and a bunch of abilities

    users = [
        User.from_name('George Carlin'),
        User.from_name('Tom Waits'),
        User.from_name('Bubba'),
    ]

    abilities = [
        Ability.from_name('flying'),
        Ability.from_name('comedy'),
        Ability.from_name('enormous jaws'),
        Ability.from_name('karate'),
        Ability.from_name('hula hooping'),
        Ability.from_name('knitting'),
        Ability.from_name('x-ray vision'),
    ]

    print [x.name for x in users]
    print [x.name for x in abilities]
    >>>['George Carlin', 'Tom Waits', 'Bubba']
    >>>['flying', 'comedy', 'enormous jaws', 'karate', 'hula hooping', 'knitting', 'x-ray vision']

Now give each users a few abilities at random (randomizing makes testing less boring, wouldn't you say?)

    for user in users:
        index = len(abilities)-1
        while(True):
            index = int(round(float(index) - random() * len(abilities) /2.0 ))
            if index < 0: break #mid statement break... ugh
            user.abilities.append(abilities[index])
        print '%s has been assigned the abilities: ' % user.name, [x.name for x in user.abilities]

        >>>George Carlin has been assigned the abilities:  ['flying', 'enormous jaws', 'karate', 'knitting']
        >>>Tom Waits has been assigned the abilities:  ['flying', 'karate', 'hula hooping']
        >>>Bubba has been assigned the abilities:  ['enormous jaws', 'knitting']

So, let's explore the users abilities and see who has what in common

    for user in users:
        print '\nLets look at %s\'s abilities...' % user.name
        for ability in user.abilities:
            print '%s shares the ability \'%s\' with: ' % (user.name, ability.name), [x.name for x in ability.users if x.name != user.name]

    >>Lets look at George Carlin's abilities...
    >>George Carlin shares the ability 'flying' with:  ['Tom Waits']
    >>George Carlin shares the ability 'enormous jaws' with:  ['Bubba']
    >>George Carlin shares the ability 'karate' with:  ['Tom Waits']
    >>George Carlin shares the ability 'knitting' with:  ['Bubba']
    >>
    >>Lets look at Tom Waits's abilities...
    >>Tom Waits shares the ability 'flying' with:  ['George Carlin']
    >>Tom Waits shares the ability 'karate' with:  ['George Carlin']
    >>Tom Waits shares the ability 'hula hooping' with:  []
    >>
    >>Lets look at Bubba's abilities...
    >>Bubba shares the ability 'enormous jaws' with:  ['George Carlin']
    >>Bubba shares the ability 'knitting' with:  ['George Carlin']


###Part 3: Use the Edge node to find users with the same ability
    #first lets save all of our models
    tmp = map(lambda x: x.save(), users)
    tmp = map(lambda x: x.save(), abilities)
    #then find all users with each ability in just two db queries
    for ability in abilities:
        user_ids = Edge.COLLECTION.find(
                                    {
                                        'name':'abilities', 
                                        'outboundCollection':User.COLLECTION_NAME,
                                        'inboundCollection':Ability.COLLECTION_NAME,
                                        'inboundId':ability._id
                                    }
                                ).distinct('outboundId')
        print 'Users who have the ability \'%s\': ' % ability.name, \
                [x.name for x in User.from_ids(user_ids)]

    >>>Users who have the ability 'flying':  ['Tom Waits', 'George Carlin']
    >>>Users who have the ability 'comedy':  []
    >>>Users who have the ability 'enormous jaws':  ['Bubba', 'George Carlin']
    >>>Users who have the ability 'karate':  ['Tom Waits', 'George Carlin']
    >>>Users who have the ability 'hula hooping':  ['Tom Waits']
    >>>Users who have the ability 'knitting':  ['Bubba', 'George Carlin']
    >>>Users who have the ability 'x-ray vision':  []

This is exactly what WhiskeyNode is doing behind the scenes when you loop through over ability.users. With proper indexing this is a very efficient query. 

###Part 4: Find users with abilities that are related to your abilities.

This is fun right? Create some directed relationships between abilities...

    for ability in abilities:
        for a2 in abilities:
            if ability != a2 and random() > .75:
                ability.relatedAbilities.append(a2)
        ability.save()
        print '\'%s\' is related to ' % ability.name, [x.name for x in ability.relatedAbilities]

    >>>'flying' is related to  ['x-ray vision', 'knitting', 'karate', 'enormous jaws']
    >>>'comedy' is related to  ['karate']
    >>>'enormous jaws' is related to  []
    >>>'karate' is related to  ['comedy']
    >>>'hula hooping' is related to  ['enormous jaws', 'flying']
    >>>'knitting' is related to  ['hula hooping', 'enormous jaws', 'flying']
    >>>'x-ray vision' is related to  ['hula hooping', 'comedy']

Now find related users the slow way

    for user in users:
        print '\nLooking for users with abilities related to %s\'s abilities ' % user.name, [x.name for x in user.abilities]
        for ability in user.abilities:
            for related_ability in ability.relatedAbilities:
                if related_ability not in user.abilities and len(related_ability.users) > 0:
                    print '\'%s\' is related to \'%s\', %s like(s) \'%s\'' % (
                                                ability.name, 
                                                related_ability.name, 
                                                str([x.name for x in related_ability.users if x is not user]), 
                                                related_ability.name
                                            )
    >>>Looking for users with abilities related to George Carlin's abilities  ['flying', 'enormous jaws', 'karate', 'knitting']
    >>>'knitting' is related to 'hula hooping', ['Tom Waits'] like(s) 'hula hooping'

    >>>Looking for users with abilities related to Tom Waits's abilities  ['flying', 'karate', 'hula hooping']
    >>>'flying' is related to 'knitting', ['Bubba', 'George Carlin'] like(s) 'knitting'
    >>>'flying' is related to 'enormous jaws', ['Bubba', 'George Carlin'] like(s) 'enormous jaws'
    >>>'hula hooping' is related to 'enormous jaws', ['Bubba', 'George Carlin'] like(s) 'enormous jaws'

    >>>Looking for users with abilities related to Bubba's abilities  ['enormous jaws', 'knitting']
    >>>'knitting' is related to 'hula hooping', ['Tom Waits'] like(s) 'hula hooping'
    >>>'knitting' is related to 'flying', ['Tom Waits', 'George Carlin'] like(s) 'flying'


Woah! Three nested for loops? Loads of db calls that probably won't be cached in your application... lets see if we can do better

    for user in users:
        #get this user's ability ids
        ability_ids =       Edge.COLLECTION.find(
                                    {
                                        'name':'abilities',
                                        'outboundId':user._id
                                    }
                                ).distinct('inboundId')
        #get abilities related to this users abilities
        related_ability_ids = Edge.COLLECTION.find(
                                    {
                                        'name':'relatedAbilities',
                                        'outboundId':{'$in':ability_ids},
                                        'inboundId':{'$nin':ability_ids}
                                    }
                                ).distinct('inboundId')
        #get users who have those abilities
        edge_cursor =          Edge.COLLECTION.find(
                                    {
                                        'name':'abilities',
                                        'outboundCollection':user.COLLECTION_NAME,
                                        'outboundId':{'$ne':user._id},
                                        'inboundId':{'$in':related_ability_ids},
                                    }
                                )
        #print the result
        print 'Users who have abilities related to %s\'s  abilities ' % user.name, \
                [(User.from_id(x['outboundId']).name, Ability.from_id(x['inboundId']).name) for x in edge_cursor]

    >>>Users who have abilities related to George Carlin's  abilities  [('Tom Waits', 'hula hooping')]
    >>>Users who have abilities related to Tom Waits's  abilities  [('George Carlin', 'knitting'), ('Bubba', 'knitting'), ('Bubba', 'enormous jaws'), ('George Carlin', 'enormous jaws')]
    >>>Users who have abilities related to Bubba's  abilities  [('Tom Waits', 'flying'), ('George Carlin', 'flying'), ('Tom Waits', 'hula hooping')]

That's better, hit the db 3 times for the graph traversal, then lookup the users and abilities that are returned (this last line could be optimized to grab the objects in two calls over the wire)

Well, that's all for now... Let me know what you think.


##Examples

Check out [whiskeynode-login](https://github.com/texuf/whiskeynode-login) for a full example




##Installation

To use in your python project::

    pip install -e git://github.com/texuf/whiskeynode.git#egg=whiskeynode
        test

To download, setup and perfom tests, run the following commands on Mac / Linux::

    get clone <repo>
    cd <reponame>
    virtualenv venv --distribute
    source venv/bin/activate
    python setup.py install
    pip install nose mock
    python run_tests.py

Acknowledgements
 * Zach Carter (zcarter)




##[mightyspring.com](www.mightyspring.com)

       __  ____      __   __         ____         _          
      /  |/  (_)__ _/ /  / /___ __  / __/__  ____(_)__  ___ _
     / /|_/ / / _ `/ _ \/ __/ // / _\ \/ _ \/ __/ / _ \/ _ `/
    /_/  /_/_/\_, /_//_/\__/\_, / /___/ .__/_/ /_/_//_/\_, / 
             /___/         /___/     /_/              /___/  


