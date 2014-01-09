'''
Created on 17.04.2013

@author: tobiasweigel
'''
import sys
import logging
from lapis.model.do import PAYLOAD_BITS

logger = logging.getLogger(__name__)

HASHMASK = 2**PAYLOAD_BITS-1
VALUETYPE_HASHMAP_SIZE = "HASHMAP_SIZE"
BASE_INDEX_HASHMAP_SIZE = 4000

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
    
    def __init__(self, infrastructure, identifier, segment_number):
        """
        Constructor.
        
        :param: segment_number: This hash map implementation is designed so that one Handle Record can contain several
          independent hash maps. The segment number is used to separate the corresponding Index segments from each other. 
          Typically, this is the "characteristic segment number" of a collection type.          
        """
        super(HandleHashmapImpl, self).__init__(infrastructure)
        self._id = identifier
        self._segment_number = segment_number
        self._index_hashmap_size = BASE_INDEX_HASHMAP_SIZE+segment_number
        if not self._infra._read_pid_value(self._id, self._index_hashmap_size):
            self._infra._write_pid_value(self._id, self._index_hashmap_size, VALUETYPE_HASHMAP_SIZE, 0)
        
    def __prepare_hash(self, key):
        return (hash(key) & HASHMASK) + (self._segment_number << PAYLOAD_BITS)
    
    def set(self, key, value):
        # hash key and truncate to positive 32 bit int
        h = self.__prepare_hash(key)
        # look at bucket
        bucket = self._infra._read_pid_value(self._id, h)
        while bucket and bucket[0] is not key:
            # simple linear probing
            h += 1
            if h > ((self._segment_number+1) << PAYLOAD_BITS) - 1:
                # set to beginning of hash block
                h = self._segment_number << PAYLOAD_BITS
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
            if h > ((self._segment_number+1) << PAYLOAD_BITS) - 1:
                h = self._segment_number << PAYLOAD_BITS
    
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
            if h > ((self._segment_number+1) << PAYLOAD_BITS) - 1:
                h = self._segment_number << PAYLOAD_BITS
                
    def is_map_index(self, index):
        """
        Verifies whether a given Handle record Index is part of this hash map.            
        """
        return (self._segment_number << PAYLOAD_BITS) <= index < ((self._segment_number+1) << PAYLOAD_BITS)  
    
    def __iter__(self):
        cached_values = self._infra._read_all_pid_values(self._id)
        for idx, v in cached_values.iteritems():
            if self.is_map_index(idx):
                yield (idx, v)
            
    def __modify_size(self, a):
        s = int(self._infra._read_pid_value(self._id, self._index_hashmap_size)[1])
        s += a
        self._infra._write_pid_value(self._id, self._index_hashmap_size, VALUETYPE_HASHMAP_SIZE, s)

    def size(self):
        return int(self._infra._read_pid_value(self._id, self._index_hashmap_size)[1])
