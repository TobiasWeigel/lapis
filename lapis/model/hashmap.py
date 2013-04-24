'''
Created on 17.04.2013

@author: tobiasweigel
'''
import sys
import logging

logger = logging.getLogger(__name__)

HASHMASK = 2**31-1
VALUETYPE_HASHMAP_SIZE = "HASHMAP_SIZE"
INDEX_HASHMAP_SIZE = 999

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
        self._infra._write_pid_value(self._id, INDEX_HASHMAP_SIZE, VALUETYPE_HASHMAP_SIZE, 0)
        
    def __prepare_hash(self, key):
        return max(hash(key) & HASHMASK, 1000)
    
    def set(self, key, value):
        # hash key and truncate to positive 32 bit int
        h = self.__prepare_hash(key)
        # look at bucket
        bucket = self._infra._read_pid_value(self._id, h)
        while bucket and bucket[0] is not key:
            # simple linear probing
            h += 1
            if h > sys.maxint:
                h = 1000
            bucket = self._infra._read_pid_value(self._id, h)
        self._infra._write_pid_value(self._id, h, key, value)
        if not bucket:
            self.__modify_size(1)
        
    def get(self, key):
        # hash key and truncate to positive 32 bit int
        h = self.__prepare_hash(key)
        # look at bucket
        bucket = None
        while True:
            bucket = self._infra._read_pid_value(self._id, h)
            if not bucket:
                return None
            if bucket[0] == key:
                return bucket[1]
            h += 1
            if h > sys.maxint:
                h = 1000
    
    def contains(self, key):
        return self.get(key) is not None
    
    def remove(self, key):
        # hash key and truncate to positive 32 bit int
        h = self.__prepare_hash(key)
        # look at bucket
        bucket = None
        while True:
            bucket = self._infra._read_pid_value(self._id, h)
            if not bucket:
                return 
            if bucket[0] == key:
                # found it; now remove handle value
                self._infra._remove_pid_value(self._id, h)
                self.__modify_size(-1)
                return 
            h += 1
            if h > sys.maxint:
                h = 1000
                
    def __iter__(self):
        cached_values = self._infra._read_all_pid_values(self._id)
        return cached_values.iteritems()
            
    def __modify_size(self, a):
        s = int(self._infra._read_pid_value(self._id, INDEX_HASHMAP_SIZE))
        s += a
        self._infra._write_pid_value(self._id, INDEX_HASHMAP_SIZE, VALUETYPE_HASHMAP_SIZE, s)

    def size(self):
        return int(self._infra._read_pid_value(self._id, INDEX_HASHMAP_SIZE))
