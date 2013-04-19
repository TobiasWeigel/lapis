'''
Created on 02.05.2012

:author: tobiasweigel

Copyright (c) 2012, Tobias Weigel, Deutsches Klimarechenzentrum GmbH
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
from lapis.model.do import DigitalObject

class DigitalObjectSet(DigitalObject):
    '''
    A set (unsorted collection) of Digital Objects (or further sub-DO-sets), realized through a Hashmap.
    
    The set does not impose specific semantics. It may be used both for arbitrary collections of largely
    unrelated objects as well as hierarchical structures of data objects that are strongly connected.
    '''

    RESOURCE_TYPE = "DIGITAL_OBJECT_SET"
    
    class SetIterator(object):
        
        def __init__(self, doset):
            self._doset = doset
            self._index = 100
        
        def __iter__(self):
            return self
        
        def next(self):
            raise NotImplementedError()
        

    def __init__(self, do_infrastructure, identifier, references = None, alias_identifiers = None):
        super(DigitalObjectSet, self).__init__(do_infrastructure, identifier, references=references, alias_identifiers=alias_identifiers)
        self.resource_type = DigitalObjectSet.RESOURCE_TYPE
        self.__hashmap = self._do_infra.manufacture_hashmap(self._id)
                
    def add_do(self, dobj):
        """
        Adds one or more Digital Objects to the set.
        
        :param dobj: Either a DO instance or a list of DO instances.  
        """
        if isinstance(dobj, list):
            for x in dobj:
                if not isinstance(x, DigitalObject):
                    raise ValueError("The given list contains objects that are no Digital Object instances!")
                self.__hashmap.set(x.identifier, x.identifier)
        else:
            if not isinstance(dobj, DigitalObject):
                raise ValueError("The given object is not a Digital Object instance: %s" % dobj)
            self.__hashmap.set(dobj.identifier, dobj.identifier)
    
    def remove_do(self, dobj):
        """
        Removes the given Digital Object(s) from the set.
        
        :param dobj: Either a DO instance or a list of DO instances.
        """
        if isinstance(dobj, list):
            for x in dobj:
                if not isinstance(x, DigitalObject):
                    raise ValueError("The given list contains objects that are no Digital Object instances!")
                self.__hashmap.remove(x.identifier)
        else:
            if not isinstance(dobj, DigitalObject):
                raise ValueError("The given object is not a Digital Object instance: %s" % dobj)
            self.__hashmap.remove(dobj.identifier)
    
    def contains_do(self, dobj):
        """
        Check if the set contains the given Digital Object(s).
        
        :param dobj: A DO instance or a list of DO instances.
        :return: True if all given Digital Objects are contained in this set.
        """
        if isinstance(dobj, list):
            for x in dobj:
                if not isinstance(x, DigitalObject):
                    raise ValueError("The given list contains objects that are no Digital Object instances!")
                if not self.__hashmap.contains(x.identifier):
                    return False
            return True
        else:
            if not isinstance(dobj, DigitalObject):
                raise ValueError("The given object is not a Digital Object instance: %s" % dobj)
            return self.__hashmap.contains(dobj.identifier)

    def iter_set_elements(self):
        """
        Iterate over the _elements in the Digital Object set.
        
        :return: an iterator object
        """
        return DigitalObjectSet.SetIterator(self)
    
    def num_set_elements(self):
        """
        Returns the number of set member elements.
        
        :return: a non-negative int 
        """
        raise NotImplementedError()
    
    def __iter__(self):
        return self.iter_set_elements()    
    
    