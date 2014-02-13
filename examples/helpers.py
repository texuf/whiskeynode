

#
# Nameable
# - little mixin to pull records by name
#
class Nameable():
    @classmethod
    def from_name(cls, name):
        c = cls.find_one({'name':name})
        return c if c else cls({'name':name})
