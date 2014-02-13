
'''
to run in python terminal:
python -c "execfile('examples/abilities.py')"
'''
from examples.helpers import Nameable
from random import random
from whiskeynode import WhiskeyNode
from whiskeynode.db import db
from whiskeynode.edges import Edge
from whiskeynode.terminals import outbound_node, outbound_list, inbound_list, bidirectional_list


#
# User
# - User object, contains a list of abilities
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
                            'abilities':    outbound_list(Ability),
                        }

#
# Ability
# - Ability Object, contans a list of users that have this ability
#
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


if __name__ == '__main__':
    

    print '\n===Abilities Example===\n'

    print '\nPART 1:\n\nCreating a user named \'John\' and an ability named \'dancing\''

    #init a user and an ability
    john = User.from_name('John')
    dancing = Ability.from_name('dancing')
    
    print 'Adding dancing to John\'s abilities'

    john.abilities.append(dancing)

    if john in dancing.users:
        print 'John is in dancing\'s users.'
    else:
        print 'John is not in dancing\'s users'

    print '\nPART 2:\n\nCreating a bunch of users and a bunch of abilities\n'

    users = [
        User.from_name('George Carlin'),
        User.from_name('Tom Waits'),
        User.from_name('Bubba'),
    ]

    print 'users:\n', [x.name for x in users], '\n'

    abilities = [
        Ability.from_name('flying'),
        Ability.from_name('comedy'),
        Ability.from_name('enormous jaws'),
        Ability.from_name('karate'),
        Ability.from_name('hula hooping'),
        Ability.from_name('knitting'),
        Ability.from_name('x-ray vision'),
    ]

    print 'abilities:\n', [x.name for x in abilities], '\n'

    #give each person a few abilities at random
    for user in users:
        index = len(abilities)-1
        while(True):
            index = int(round(float(index) - random() * len(abilities) /2.0 ))
            if index < 0: break #mid statement break for 'cleanliness'
            user.abilities.append(abilities[index])
        print '%s has been assigned the abilities: ' % user.name, [x.name for x in user.abilities]


    #do some exploration
    for user in users:
        print '\nLets look at %s\'s abilities...' % user.name
        for ability in user.abilities:
            print '%s shares the ability \'%s\' with: ' % (user.name, ability.name), [x.name for x in ability.users if x.name != user.name]


    print '\nPART 3:\n\nUse edge queries to find users'
    map(lambda x: x.save(), users)
    map(lambda x: x.save(), abilities)

    for ability in abilities:
        user_ids = Edge.COLLECTION.find(
                                    {
                                        'name':'abilities', 
                                        'outboundCollection':User.COLLECTION_NAME,
                                        'inboundCollection':Ability.COLLECTION_NAME,
                                        'inboundId':ability._id
                                    }
                                ).distinct('outboundId')
        print 'Users who have the ability \'%s\': ' % ability.name, [x.name for x in User.from_ids(user_ids)]
    

    print '\nPART 4:\n\nFind users with abilities that are related to your abilities.'

    #give each ability some related abilities
    print '\nEstablishing ability relationships...\n'
    for ability in abilities:
        for a2 in abilities:
            if ability != a2 and random() > .75:
                ability.relatedAbilities.append(a2)
        ability.save()
        print '\'%s\' is related to ' % ability.name, [x.name for x in ability.relatedAbilities]


    print '\nUsing silly slow way to find related users...'
    #search for related abilities in the traditional way (lots of database queries here, lots of loops)
    for user in users:
        print '\nLooking for users with abilities related to %s\'s abilities ' % user.name, [x.name for x in user.abilities]
        for ability in user.abilities:
            for related_ability in ability.relatedAbilities:
                if related_ability not in user.abilities and len(related_ability.users) > 0:
                    print '\'%s\' is related to \'%s\', %s like \'%s\'' % (
                                                related_ability.name, 
                                                ability.name, 
                                                str([x.name for x in related_ability.users if x is not user]), 
                                                related_ability.name
                                            )


    #instead use the graph, lets see if we can reduce the number of queries and loops
    print '\nUsing Edge queries to find related users...\n'
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









