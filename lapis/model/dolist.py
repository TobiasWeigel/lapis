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
from lapis.model.do import DigitalObject, PAYLOAD_BITS, MAX_PAYLOAD, SEGMENT_PARENTS_TARGET_MASK_BITS, VALUETYPE_PARENT_OBJECT,\
    MAX_PARENTS, SEGMENT_PARENTS_MASK_VALUE

def split_handle(handle):
    """
    Splits a Handle identifier conforming to the syntax index:prefix/suffix (index: is optional).
    Returns a tuple of (main, index), where main is prefix/suffix and index will be None if there is no index given.
    """
    i = handle.find(":")
    j = handle.find("/")
    if i == -1 or i > j:
        return (handle, None)
    return (handle[i+1:], int(handle[:i]))

class DigitalObjectArray(DigitalObject):
    '''
    A list (sorted collection) of Digital Objects, realized as an indexed array.
    '''

    CHARACTERISTIC_SEGMENT_NUMBER = 2
    RESOURCE_TYPE = "DIGITAL_OBJECT_ARRAY"
    CATEGORY_MASK_VALUE = CHARACTERISTIC_SEGMENT_NUMBER << PAYLOAD_BITS
    INDEX_ARRAY_SIZE = 2000
    VALUETYPE_ARRAY_SIZE = "ARRAY_SIZE"
    VALUETYPE_ARRAY_ELEMENT = "ARRAY_ELEMENT"
    MY_PARENT_SEGMENT_TARGET_MASK = (CHARACTERISTIC_SEGMENT_NUMBER << SEGMENT_PARENTS_TARGET_MASK_BITS) + SEGMENT_PARENTS_MASK_VALUE

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
        # add info that self is parent of dobj
        dobj._write_parent_info(self)
        self.__modify_size(1)
    
    def insert_do(self, dobj, index):
        """
        Inserts a new element at the given index. All current elements with an equal or higher index are shifted. 
        """
        arraysize = self.num_elements()
        if index < 0 or index > arraysize-1:
            raise IndexError("Index too high: %s (array size is only %s)" % (index, arraysize))
        # shift all higher entries
        for i in range(arraysize, index, -1):
            v = self._do_infra._read_pid_value(self._id, self.CATEGORY_MASK_VALUE+i-1)
            self._do_infra._write_pid_value(self._id, self.CATEGORY_MASK_VALUE+i, v[0], v[1])
        # now overwrite at given index
        self._do_infra._write_pid_value(self._id, self.CATEGORY_MASK_VALUE+index, self.VALUETYPE_ARRAY_ELEMENT, dobj._id)
        # add info that self is parent of dobj
        dobj._write_parent_info(self)
        self.__modify_size(1)
            
    def remove_do(self, dobj_or_index):
        """
        Removes the element at the given index or if a Digital Object instance is given, removes the given element
        if it is part of this array. 
        
        :param: dobj_or_index: The Digital Object to remove or an index. 
        """
        arraysize = self.num_elements()
        if isinstance(dobj_or_index, DigitalObject):
            index = self.index_of(dobj_or_index)
            dobj = dobj_or_index
        else:
            index = dobj_or_index 
            dobj = self.get_do(index)
        if index < 0 or index > arraysize-1:
            raise IndexError("Index out of range: %s (array size is only %s)" % (index, arraysize))
        # shift all higher entries
        for i in range(index, arraysize-1):
            v = self._do_infra._read_pid_value(self._id, self.CATEGORY_MASK_VALUE+i+1)
            self._do_infra._write_pid_value(self._id, self.CATEGORY_MASK_VALUE+i, v[0], v[1])
        # clear highest index
        self._do_infra._remove_pid_value(self._id, self.CATEGORY_MASK_VALUE+arraysize-1)
        # remove info that self is parent of dobj_or_index
        dobj._remove_parent_info(self)
        self.__modify_size(-1)
        
    def get_do(self, index):
        """
        Returns the element at the given index.
        """
        v = self._do_infra._read_pid_value(self._id, self.CATEGORY_MASK_VALUE+index)
        if not v:
            raise IndexError("Index out of range or corrupt Array Handle record! (index: %s, ID: %s)" % (index, self._id))
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
        
        :param dobj: A Digital Object instance or a PID.
        """
        if isinstance(dobj, DigitalObject):
            target_id = dobj.identifier
        else:
            target_id = dobj
        arraysize = self.num_elements()
        for i in range(0, arraysize):
            v = self._do_infra._read_pid_value(self._id, self.CATEGORY_MASK_VALUE+i)
            if v[1] == target_id:
                return i
        raise ValueError("%s is not in this list." % dobj)
        
    def contains(self, dobj):
        """
        Returns True or False indicating whether the given object is in this list.
        
        :param dobj: A Digital Object instance or a PID. 
        """
        if isinstance(dobj, DigitalObject):
            target_id = dobj.identifier
        else:
            target_id = dobj
        arraysize = self.num_elements()
        for i in range(0, arraysize):
            v = self._do_infra._read_pid_value(self._id, self.CATEGORY_MASK_VALUE+i)
            if v[1] == target_id:
                return True
        return False
        
    def __iter__(self):
        raise NotImplementedError()



class DigitalObjectLinkedList(DigitalObject):

    CHARACTERISTIC_SEGMENT_NUMBER = 4
    RESOURCE_TYPE = "DIGITAL_OBJECT_LINKED_LIST"
    CATEGORY_MASK_VALUE = CHARACTERISTIC_SEGMENT_NUMBER << PAYLOAD_BITS
    INDEX_LINKED_LIST_SIZE = 2001
    VALUETYPE_LINKED_LIST_SIZE = "LINKED_LIST_SIZE"
    INDEX_LINKED_LIST_FIRST_ELEMENT = 2002
    VALUETYPE_LINKED_LIST_FIRST_ELEMENT = "LINKED_LIST_FIRST_ELEMENT"
    INDEX_LINKED_LIST_LAST_ELEMENT = 2003
    VALUETYPE_LINKED_LIST_LAST_ELEMENT = "LINKED_LIST_LAST_ELEMENT"
    MY_PARENT_SEGMENT_TARGET_MASK = (CHARACTERISTIC_SEGMENT_NUMBER << SEGMENT_PARENTS_TARGET_MASK_BITS) + SEGMENT_PARENTS_MASK_VALUE
    
    VALUETYPE_PREV_OBJECT = "PREVIOUS_OBJECT"
    VALUETYPE_NEXT_OBJECT = "NEXT_OBJECT"
    
    def __init__(self, do_infrastructure, identifier, references = None, alias_identifiers = None):
        super(DigitalObjectLinkedList, self).__init__(do_infrastructure, identifier, references=references, alias_identifiers=alias_identifiers)
        self.resource_type = self.RESOURCE_TYPE
        # check and init array size
        if not self._do_infra._read_pid_value(self._id, self.INDEX_LINKED_LIST_SIZE):
            self._do_infra._write_pid_value(self._id, self.INDEX_LINKED_LIST_SIZE, self.VALUETYPE_LINKED_LIST_SIZE, 0)
        
    def __modify_size(self, a):
        """
        Modifies the size information.
        """
        s = self._do_infra._read_pid_value(self._id, self.INDEX_LINKED_LIST_SIZE)[1]
        newsize = int(s)+a
        self._do_infra._write_pid_value(self._id, self.INDEX_LINKED_LIST_SIZE, self.VALUETYPE_LINKED_LIST_SIZE, newsize)
        
    def __find_free_slot(self, dobj):
        freeslot = 0 
        while True:
            v = self._do_infra._read_pid_value(dobj.identifier, self.MY_PARENT_SEGMENT_TARGET_MASK+freeslot)
            if v:
                freeslot += 1
                if v == MAX_PARENTS:
                    raise Exception("No more free parent slots in %s!" % dobj.identifier)
                continue
            break
        return freeslot

    def append_do(self, dobj):
        """
        Appends the given object to the end of the list.
        """
        # determine last element and its index
        p = self._do_infra._read_pid_value(self.identifier, self.INDEX_LINKED_LIST_LAST_ELEMENT)
        if p:
            last_id, last_index = split_handle(p[1])
            last_id_and_index = p[1]
        else:
            last_id = None
            last_id_and_index = ""
        # fill in parent info and use free slot to write prev/next references
        freeslot = dobj._write_parent_info(self)
        # cat4: write two entries (previous and next)
        self._do_infra._write_pid_value(dobj.identifier, self.CATEGORY_MASK_VALUE+freeslot*2,   self.VALUETYPE_PREV_OBJECT, last_id_and_index)
        self._do_infra._write_pid_value(dobj.identifier, self.CATEGORY_MASK_VALUE+freeslot*2+1, self.VALUETYPE_NEXT_OBJECT, "")
        # cat4: update NEXT entry at former last object
        if last_id:
            self._do_infra._write_pid_value(last_id, last_index+1, self.VALUETYPE_NEXT_OBJECT, "%s:%s" % (self.CATEGORY_MASK_VALUE+freeslot*2+1, dobj.identifier))
        else:
            # set first element
            self._do_infra._write_pid_value(self.identifier, self.INDEX_LINKED_LIST_FIRST_ELEMENT, self.VALUETYPE_LINKED_LIST_FIRST_ELEMENT, "%s:%s" % (self.CATEGORY_MASK_VALUE+freeslot*2+1, dobj.identifier))
        # update last identifier entry and size
        self._do_infra._write_pid_value(self.identifier, self.INDEX_LINKED_LIST_LAST_ELEMENT, self.VALUETYPE_LINKED_LIST_LAST_ELEMENT, "%s:%s" % (self.CATEGORY_MASK_VALUE+freeslot*2, dobj.identifier))
        self.__modify_size(1)
    
    def insert_do(self, dobj, index_or_dobj):
        """
        Inserts the given object at the given index. Alternatively accepts an object instead of the index; then the new
        object will be inserted before the first occurrence of the index object. Using an index instead of an object 
        will cause an inefficient lookup operation to find the object.
        """
        # ***** Insert before given object *****
        if not isinstance(index_or_dobj, DigitalObject):
            # only index given; so iterate and find object, also determining the slot index
            d, i = self.get_do_and_slotindex(index_or_dobj)
            if not d:
                raise ValueError("Given object %s is not part of this list %s!" % (index_or_dobj.identifier, self.identifier))
            index_or_dobj = d
        # 1a. determine previous element (and at the same time also verify membership in this list)
        currentindex = self.__determine_first_slot(index_or_dobj.identifier)
        poentry = self._do_infra._read_pid_value(index_or_dobj.identifier, self.CATEGORY_MASK_VALUE+currentindex*2)
        if poentry[0] != self.VALUETYPE_PREV_OBJECT:
            raise Exception("Corrupt Linked List element record at %s:%s!" % (self.CATEGORY_MASK_VALUE+currentindex*2, index_or_dobj.identifier))
        prev_dobj_id_and_index = poentry[1]
        # fill in parent info and use free slot to write prev/next references
        dobj_freeslot = dobj._write_parent_info(self)
        # now fill in stuff! 
        if prev_dobj_id_and_index:
            # 2a. pred.succ = new_element
            pred_id, pred_index = split_handle(prev_dobj_id_and_index)
            self._do_infra._write_pid_value(pred_id, pred_index+1, self.VALUETYPE_NEXT_OBJECT, "%s:%s" % (self.CATEGORY_MASK_VALUE+dobj_freeslot*2+1, dobj.identifier))
        else:
            # 2b. no predecessor --> first element!
            self._do_infra._write_pid_value(self.identifier, self.INDEX_LINKED_LIST_FIRST_ELEMENT, self.VALUETYPE_LINKED_LIST_FIRST_ELEMENT, "%s:%s" % (self.CATEGORY_MASK_VALUE+dobj_freeslot*2+1, dobj.identifier))
            prev_dobj_id_and_index = ""
        # 3. index_or_dobj.pred = new_element
        self._do_infra._write_pid_value(index_or_dobj.identifier, self.CATEGORY_MASK_VALUE+currentindex*2, self.VALUETYPE_PREV_OBJECT, "%s:%s" % (self.CATEGORY_MASK_VALUE+dobj_freeslot*2, dobj.identifier))
        # 4. new_element.parent = self
        self._do_infra._write_pid_value(dobj.identifier, self.MY_PARENT_SEGMENT_TARGET_MASK+dobj_freeslot, VALUETYPE_PARENT_OBJECT, self.identifier)
        # 5. new_element.pred = pred
        self._do_infra._write_pid_value(dobj.identifier, self.CATEGORY_MASK_VALUE+dobj_freeslot*2, self.VALUETYPE_PREV_OBJECT, prev_dobj_id_and_index)
        # 6. new_element.succ = index_or_dobj
        self._do_infra._write_pid_value(dobj.identifier, self.CATEGORY_MASK_VALUE+dobj_freeslot*2+1, self.VALUETYPE_NEXT_OBJECT, "%s:%s" % (self.CATEGORY_MASK_VALUE+currentindex*2+1, index_or_dobj.identifier))
        self.__modify_size(1)
    
    def remove_do(self, index_or_dobj):
        """
        Removes the given Digital Object from this list. The method also accepts an index, which will however cause an 
        inefficient lookup operation to determine the object to remove. Raises an exception if the given object is
        not in this list or the index is out of range.
        """
        if isinstance(index_or_dobj, DigitalObject):
            # determine first slot with self as parent
            dobj = index_or_dobj
            dobj_slot = self.__determine_first_slot(dobj.identifier)
        else:
            # find object by given index
            dobj, dobj_slot = self.get_do_and_slotindex(index_or_dobj)
            if not dobj:
                raise ValueError("Given object %s is not part of this list %s!" % (index_or_dobj.identifier, self.identifier))
        # determine all pred, succ and slots
        pred_dobj, pred_dobj_slot = split_handle(self._do_infra._read_pid_value(dobj.identifier, self.CATEGORY_MASK_VALUE+dobj_slot*2)[1])
        succ_dobj, succ_dobj_slot = split_handle(self._do_infra._read_pid_value(dobj.identifier, self.CATEGORY_MASK_VALUE+dobj_slot*2+1)[1])
        if not pred_dobj:
            if not succ_dobj:
                # special case: removed first and last element, i.e. clearing the list
                self._do_infra._write_pid_value(self.identifier, self.INDEX_LINKED_LIST_FIRST_ELEMENT, self.VALUETYPE_LINKED_LIST_FIRST_ELEMENT, "")
                self._do_infra._write_pid_value(self.identifier, self.INDEX_LINKED_LIST_LAST_ELEMENT, self.VALUETYPE_LINKED_LIST_LAST_ELEMENT, "")
            else:
                # special case: remove first element
                self._do_infra._write_pid_value(self.identifier, self.INDEX_LINKED_LIST_FIRST_ELEMENT, self.VALUETYPE_LINKED_LIST_FIRST_ELEMENT, "%s:%s" % (succ_dobj_slot, succ_dobj))
                self._do_infra._write_pid_value(succ_dobj, succ_dobj_slot-1, self.VALUETYPE_PREV_OBJECT, "")
        elif not succ_dobj:
            # special case: remove last element
            self._do_infra._write_pid_value(self.identifier, self.INDEX_LINKED_LIST_LAST_ELEMENT, self.VALUETYPE_LINKED_LIST_LAST_ELEMENT, "%s:%s" % (pred_dobj_slot, pred_dobj))
            self._do_infra._write_pid_value(pred_dobj, pred_dobj_slot+1, self.VALUETYPE_NEXT_OBJECT, "")
        else:
            # 1. pred.succ = dobj.succ
            self._do_infra._write_pid_value(pred_dobj, pred_dobj_slot+1, self.VALUETYPE_NEXT_OBJECT, "%s:%s" % (succ_dobj_slot, succ_dobj))
            # 2. succ.pred = dobj.pred
            self._do_infra._write_pid_value(succ_dobj, succ_dobj_slot-1, self.VALUETYPE_PREV_OBJECT, "%s:%s" % (pred_dobj_slot, pred_dobj))
        # 3. dobj.parent = None
        self._do_infra._remove_pid_value(dobj.identifier, self.MY_PARENT_SEGMENT_TARGET_MASK+dobj_slot)
        # 4. dobj.pred = None
        self._do_infra._remove_pid_value(dobj.identifier, self.CATEGORY_MASK_VALUE+dobj_slot*2)
        # 5. dobj.succ = None
        self._do_infra._remove_pid_value(dobj.identifier, self.CATEGORY_MASK_VALUE+dobj_slot*2+1)
        self.__modify_size(-1)
        
    def __determine_first_slot(self, identifier):
        """
        Goes through the parent slots on the object with given PID and finds the first one which lists self as the parent.
        :returns: the slot index (not to be confused with the actual Index in the Handle)
        """                    
        dobj_slot = 0
        while True:
            v = self._do_infra._read_pid_value(identifier, self.MY_PARENT_SEGMENT_TARGET_MASK+dobj_slot)
            if not v or dobj_slot == MAX_PARENTS:
                raise ValueError("Given object %s is not part of this list %s!" % (identifier, self.identifier))
            if v[1] == self.identifier:
                return dobj_slot
            dobj_slot += 1
            
    def get_do_and_slotindex(self, index):
        """
        Finds the element of given index and also determines its slot index. Raises an Exception if the index is out of range. 
        :returns: a tuple of (digital object, slot index), where the slot index is not to be confused with an actual Handle Index!
        """
        # follow NEXT elements
        curr_dobj, curr_slot = split_handle(self._do_infra._read_pid_value(self.identifier, self.INDEX_LINKED_LIST_FIRST_ELEMENT)[1])
        i = 0
        while curr_dobj:
            if i == index:
                return self._do_infra.lookup_pid(curr_dobj), int((curr_slot-self.CATEGORY_MASK_VALUE)/2)
            curr_dobj, curr_slot = split_handle(self._do_infra._read_pid_value(curr_dobj, curr_slot)[1])
            i += 1
        raise IndexError("Index out of range (index at %s, LinkedList PID: %s)!" % (i, self.identifier))
    
    def get_do(self, index):
        """
        Returns the Digital Object at the given index. Raises an exception if the index is out of range.
        :returns: a DigitalObject instance
        """
        return self.get_do_and_slotindex(index)[0]
        
    def contains(self, dobj):
        """
        Checks whether the given Digital Object is in this list.
        
        :param dobj: A DigitalObject instance or a PID string.
        """
        if isinstance(dobj, DigitalObject):
            dobj_id = dobj.identifier
        else:
            dobj_id = dobj
        i = 0
        while True:
            v = self._do_infra._read_pid_value(dobj_id, self.MY_PARENT_SEGMENT_TARGET_MASK+i)
            if not v:
                return False
            if v[1] == self.identifier:
                return True
            i += 1
            if i == MAX_PARENTS:
                return False
    
    def index_of(self, dobj):
        """
        Returns the index of the first occurrence of the given dobj. If it is not in this list, raises a ValueError.
        
        :param dobj: A Digital Object instance or a PID.
        """
        if isinstance(dobj, DigitalObject):
            dobj_id = dobj.identifier
        else:
            dobj_id = dobj
        dobj_index = self.__determine_first_slot(dobj_id)
        dobj_index = self.CATEGORY_MASK_VALUE+dobj_index*2   # previous elements
        # follow PREV elements, i.e. walk backwards to first list element and count
        n = 0
        while dobj_id:
            dobj_id, dobj_index = split_handle(self._do_infra._read_pid_value(dobj_id, dobj_index)[1])
            n += 1
        return n-1
    
    @staticmethod
    def next_element(current_dobj, current_occurrence):
        """
        Returns the next element in the list after the given element or None if the given element is the last one.
        As the method is static, it will use the given object's infrastructure to determine the next element.
        
        :param current_dobj: A DigitalObject instance
        :param current_occurrence: Only providing the PID/DO of the current object is not sufficient, because it may be 
          part of the same list multiple times. Thus, we also need a reference to the current occurrence index of this 
          particular object. This is a valid Handle Value index and not to be confused with the list index of the item.
          
        :returns: a tuple of (next_dobj, occurrence), where both are None if there is no next element
        """
        # occurrence index should be in cat 4; however, we need to check and tolerate also cat 1 indices
        cat = current_occurrence >> PAYLOAD_BITS
        if cat == 4:
            if current_occurrence % 2 == 0:
                # even number: must add 1 to have it point to the NEXT instead of the PREV
                index = current_occurrence+1
            else:
                # odd number: okay, can use it rightaway
                index = current_occurrence
        elif cat == 1:
            # cat 1 (i.e. points to containing list) - determine proper NEXT index
            index = (current_occurrence & MAX_PAYLOAD)*2 + DigitalObjectLinkedList.CATEGORY_MASK_VALUE+1
        else:
            raise ValueError("Invalid occurrence index: %s!" % current_occurrence)            
        v = current_dobj._do_infra._read_pid_value(current_dobj.identifier, index)
        if not v:
            return (None, None)
        res_id, res_occ = split_handle(v[1])
        if not res_id:
            return (None, None)
        return (current_dobj._do_infra.lookup_pid(res_id), res_occ)
    
    def num_elements(self):
        """
        Returns the number of elements currently in this list.
        """
        n = int(self._do_infra._read_pid_value(self.identifier, self.INDEX_LINKED_LIST_SIZE)[1])
        return n        
    
    def last_element(self):
        """
        Return the last element in this list.
        
        :returns: a tuple (dobj, occurrence) where dobj is a DigitalObject instance and occurrence is the occurrence
          index. The tuple will be (None, None) if the list is empty.
        """
        p = self._do_infra._read_pid_value(self.identifier, self.INDEX_LINKED_LIST_LAST_ELEMENT)[1]
        if not p:
            return (None, None)
        p, i = split_handle(p)
        return self._do_infra.lookup_pid(p), i
    
    def first_element(self):
        """
        Return the first element in this list.
        
        :returns: a tuple (dobj, occurrence) where dobj is a DigitalObject instance and occurrence is the occurrence
          index. The tuple will be (None, None) if the list is empty.
        """
        p = self._do_infra._read_pid_value(self.identifier, self.INDEX_LINKED_LIST_FIRST_ELEMENT)[1]
        if not p:
            return (None, None)
        p, i = split_handle(p)
        return self._do_infra.lookup_pid(p), i
    
    def __iter__(self):
        raise NotImplementedError()
        
        