'''
Created on 17.05.2013

@author: tobiasweigel

:author: tobiasweigel

Copyright (c) 2013, Tobias Weigel, Deutsches Klimarechenzentrum GmbH
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met: 

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer. 
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution. 

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those
of the authors.
'''
from lapis.model.do import DigitalObject, PAYLOAD_BITS, MAX_PAYLOAD

class DigitalObjectArray(DigitalObject):
    '''
    A list (sorted collection) of Digital Objects, realized as an indexed array.
    '''

    RESOURCE_TYPE = "DIGITAL_OBJECT_ARRAY"
    CATEGORY_MASK_VALUE = 2 << PAYLOAD_BITS
    INDEX_ARRAY_SIZE = 2000
    VALUETYPE_ARRAY_SIZE = "ARRAY_SIZE"
    VALUETYPE_ARRAY_ELEMENT = "ARRAY_ELEMENT"

    def __init__(self, do_infrastructure, identifier, references = None, alias_identifiers = None):
        super(DigitalObjectArray, self).__init__(do_infrastructure, identifier, references=references, alias_identifiers=alias_identifiers)
        self.resource_type = DigitalObjectArray.RESOURCE_TYPE
        # check and init array size
        if not self._do_infra._read_pid_value(self._id, self.INDEX_ARRAY_SIZE):
            self._do_infra._write_pid_value(self._id, self.INDEX_ARRAY_SIZE, self.VALUETYPE_ARRAY_SIZE, 0)
        
    def __modify_size(self, a):
        """
        Modifies the size information.
        """
        s = self._do_infra._read_pid_value(self._id, self.INDEX_ARRAY_SIZE)[1]
        newsize = int(s)+a
        self._do_infra._write_pid_value(self._id, self.INDEX_ARRAY_SIZE, self.VALUETYPE_ARRAY_SIZE, newsize)

    def append_do(self, dobj):
        """
        Appends a new element to the end of the list.
        """
        newindex = self.num_elements()
        if newindex > MAX_PAYLOAD:
            raise IndexError("Arrays cannot have more than %s elements!" % MAX_PAYLOAD)
        self._do_infra._write_pid_value(self._id, newindex+self.CATEGORY_MASK_VALUE, self.VALUETYPE_ARRAY_ELEMENT, dobj._id)
        self.__modify_size(1)
    
    def insert_do(self, dobj, index):
        """
        Inserts a new element at the given index. All current elements with an equal or higher index are shifted. 
        """
        highest_index = self.num_elements()
        # shift all higher entries
        for i in range(highest_index, index, -1):
            v = self._do_infra._read_pid_value(self._id, self.CATEGORY_MASK_VALUE+i-1)
            self._do_infra._write_pid_value(self._id, self.CATEGORY_MASK_VALUE+i, v[0], v[1])
        # now overwrite at given index
        self._do_infra._write_pid_value(self._id, self.CATEGORY_MASK_VALUE+index, self.VALUETYPE_ARRAY_ELEMENT, dobj._id)
        self.__modify_size(1)
            
    def remove_do(self, index):
        """
        Removes the element at the given index. 
        """
        highest_index = self.num_elements()
        # shift all higher entries
        for i in range(highest_index-1, index, -1):
            v = self._do_infra._read_pid_value(self._id, self.CATEGORY_MASK_VALUE+i)
            self._do_infra._write_pid_value(self._id, self.CATEGORY_MASK_VALUE+i-1, v[0], v[1])
        # clear highest index
        self._do_infra._remove_pid_value(self._id, self.CATEGORY_MASK_VALUE+highest_index-1)
        self.__modify_size(-1)
        
    def get_do(self, index):
        """
        Returns the element at the given index.
        """
        v = self._do_infra._read_pid_value(self._id, self.CATEGORY_MASK_VALUE+index)
        if v[0] != self.VALUETYPE_ARRAY_ELEMENT:
            raise Exception("Irregular type for an array element: %s" % v[0])
        dobj = self._do_infra.lookup_pid(v[1])
        return dobj

    def num_elements(self):
        """
        Returns the number of elements in the list.
        Does so by looking at a value at a special index.
        """
        n = int(self._do_infra._read_pid_value(self._id, self.INDEX_ARRAY_SIZE)[1])
        return n
        
    
    def index_of(self, dobj):
        """
        Returns the index of the given dobj. If it is not in this list, raises a ValueError.
        """
        maxindex = self.num_elements()-1
        for i in range(0, maxindex):
            v = self._do_infra._read_pid_value(self._id, self.CATEGORY_MASK_VALUE+i)
            if v[1] == dobj._id:
                return i
        raise ValueError("%s is not in this list." % dobj)
        
    def contains(self, dobj):
        """
        Returns True or False indicating whether the given object is in this list.
        """
        maxindex = self.num_elements()-1
        for i in range(0, maxindex):
            v = self._do_infra._read_pid_value(self._id, self.CATEGORY_MASK_VALUE+i)
            if v[1] == dobj._id:
                return True
        return False
        
    
    
    
class DigitalObjectLinkedListElement(DigitalObject):
    pass

class DigitalObjectLinkedList(DigitalObject):
    pass
