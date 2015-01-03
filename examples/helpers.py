
class Nameable():
    '''little mixin to pull records by name'''
    @classmethod
    def from_name(cls, name):
        c = cls.find_one({'name':name})
        return c if c else cls({'name':name})

def make_list(items):
    ''' takes list of Nameable or string, returns punctiated string - any library version shouldn't include a period '''
    if len(items) > 1:
        if isinstance(items[0], Nameable):
            return '%s and %s.' % (
                                    ', '.join([x.name for x in items[0:len(items)-1]]), 
                                    items[-1].name
                                  )
        else:
            return '%s and %s.' % (
                                    ', '.join([x for x in items[0:len(items)-1]]), 
                                    items[-1]
                                  )
    elif len(items) > 0:
        if isinstance(items[0], Nameable):
            return '%s.' % items[0].name
        else:
            return '%s.' % items[0]
    else:
        return 'none.'

