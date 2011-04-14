
class TupleDict(dict):
    '''Stores additional info, but removes it on __getitem__().'''
    
    def __setitem__(self, key, value):
        print('setting', key, value)
        super(TupleDict, self).__setitem__(key, (value, 'secret'))
        
    def __getitem__(self, key):
        value = super(TupleDict, self).__getitem__(key)
        print('getting', key, value[0])
        return value[0]


#class TupleMeta(type):
#    
#    @classmethod
#    def __prepare__(metacls, name, bases, **kargs):
#        print('in prepare')
#        return TupleDict()
#    
#    def __new__(cls, name, bases, classdict):
#        print('in new')
#        return type.__new__(cls, name, bases, classdict)
#    
#    
#class C(metaclass=TupleMeta):
#    
#    def __init__(self):
#        self.a = 1
        
        
class TupleSuper:
    
    def __new__(cls):
        print('in new')
        instance = object.__new__(cls)
        instance.__dict__ = TupleDict(instance.__dict__)
        return instance
    
    def __getattribute__(self, name):
        return object.__getattribute__(self, name)
    
    def __setattr__(self, name, value):
        object.__dict__[name] = value
    
    
class D(TupleSuper):
    
    def __init__(self):
        self.a = 1
        
        
if __name__ == '__main__':
    q = TupleDict()
    q['direct'] = 1
    print(q)
    d = D()
    print(type(d.__dict__))
    assert d.a == 1
    print(list(d.__dict__.items()))
    d.a = 2
    print(list(d.__dict__.items()))
    d.b = 3
    print(list(d.__dict__.items()))
    