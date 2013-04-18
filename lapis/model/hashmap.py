'''
Created on 17.04.2013

@author: tobiasweigel
'''
import sys
from lapis.infra.handleinfrastructure import HandleInfrastructure

HASHMASK = 2**31-1

class Hashmap(object):
    '''
    Abstract hashmap base class. Acts as a factory for actual hashmap implementations which depend on a particular 
    infrastructure type.
    '''


    def __init__(self, infrastructure):
        '''
        Constructor
        '''
        self._infra = infrastructure
    
    def __create(self, infrastructure, identifier):
        """
        Factory method.
        """
        if isinstance(infrastructure, HandleInfrastructure):
            return HandleHashmapImpl(infrastructure, identifier)
        raise TypeError("Unknown/unsupported infrastructure type: %s" % type(infrastructure))
    
    create = staticmethod(__create)
    
    def set(self, key, value):
        raise NotImplementedError()
    
    def get(self, key):
        raise NotImplementedError()
    
    def contains(self, key):
        raise NotImplementedError()
    
    def remove(self, key):
        raise NotImplementedError()
    
    
class HandleHashmapImpl(Hashmap):
    
    def __init__(self, infrastructure, identifier):
        """
        Constructor.
        """
        super(HandleHashmapImpl, self).__init__(infrastructure)
        self._id = identifier
        
    def __prepare_hash(self, key):
        return max(hash(key) & HASHMASK, 100)
    
    def set(self, key, value):
        # hash key and truncate to positive 32 bit int
        h = self.__prepare_hash(key)
        # look at bucket
        bucket = self._infra.read_handle_value(self._id, h)
        while not bucket or bucket[0] is not key:
            # simple linear probing
            h += 1
            if h > sys.maxint:
                h = 100
            bucket = self._infra.read_handle_value(self._id, h)
        self._infra.write_handle_value(self._id, h, key, value)
        
    def get(self, key):
        # hash key and truncate to positive 32 bit int
        h = self.__prepare_hash(key)
        # look at bucket
        bucket = None
        while not bucket:
            bucket = self._infra.read_handle_value(self._id, h)
            if not bucket:
                return None
            if bucket[0] is key:
                return bucket[1]
            h += 1
            if h > sys.maxint:
                h = 100
    
    def contains(self, key):
        return self.get(key) is not None
    
    def remove(self, key):
        # hash key and truncate to positive 32 bit int
        h = self.__prepare_hash(key)
        # look at bucket
        bucket = None
        while not bucket:
            bucket = self._infra.read_handle_value(self._id, h)
            if not bucket:
                return 
            if bucket[0] is key:
                # found it; now remove handle value
                self._infra.remove_handle_value(self._id, h)
                return 
            h += 1
            if h > sys.maxint:
                h = 100
