"""
Created on 20.04.2012

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
"""

import re

VALUETYPE_DATA = 0

REGEX_PID = re.compile(r'^\d\w*(\.?\w+)*/.+')

REFERENCE_SUBELEMENT = "subelement"
REFERENCE_SUBELEMENT_OF = "subelement-of"

PAYLOAD_BITS = 24
MAX_PAYLOAD = 2 ** PAYLOAD_BITS - 1
SEGMENT_PARENTS_MASK_VALUE = 1 << PAYLOAD_BITS
SEGMENT_PARENTS_TARGET_MASK_BITS = 17
MAX_PARENTS = 2 ** SEGMENT_PARENTS_TARGET_MASK_BITS - 1
VALUETYPE_PARENT_OBJECT = "PARENT_OBJECT"


class DigitalObject(object):
    """
    Digital Object representation in native Python.
    Changes to the object cause changes in the underlying Digital Object infrastructure.
    
    A Digital Object consists of data and key-metadata. The key-metadata consists of a globally unique, resolvable 
    identifier, provided by the DO infrastructure, a resource location for digital material, and associated metadata, 
    called annotations. Annotations have the form of key-value pairs. Keys are strings, the value is not specifically 
    typed (octet-stream). Keys are unique. If more than one value should be assigned to one key, use a list as the key 
    value.
    
    The data of a Digital Object is also typed. The type may be either enforced by a particular structure or role of the
    Digital Object, e.g. in the case of a collection, set or alias for another Digital Object. Such Digital Objects do
    not have a resource location, but their data is held in native Python class instances within this software space. 
    On the other hand, if the Digital Object holds domain data, it will always provide an external resource location 
    and a resource type, which serves as the type of the Digital Object. External resources are held and accessed
    outside of this particular Python implementation (e.g. in a data archive). Thus, one might well state that class
    instances do not fully represent Digital Objects - the discussion about terminology and concepts is certainly still
    very much open.
    """

    def __init__(self, do_infrastructure, identifier, references=None, alias_identifiers=None):
        """
        Constructor. Only called by the factory or other infrastructure methods that construct/reconstruct KeyMD 
        instances.

        :param do_infrastructure: The DO infrastructure interface to use.
        :param identifier: The already acquired identifier to associate the object with.
        :param annotations: The annotations to initialize the metadata with. Note that independent of the particular 
        infrastructure, no resource location or object-type entries should be given in the annotations dict. Also note
        that the annotations dict is assigned directly, not copied.
        :param resource_location: The resource location of the Digital Object's data, in case of external data.
        :param resource_type: The resource type for external data. Note that resource_location and resource_type are not
          checked for consistency by the constructor. It is the caller's task to provide meaningful values.
        :param references: The references of this instance to other Digital Objects. As with annotations, this is a dict
          that is assigned directly, not copied.
        :param alias_identifiers: The alias PIDs that lead to this Digital Object. Only available if the DO was resolved through 
          an alias PID. This should be a list of identifier strings. The process which lead to the DO started at the 
          first list entry. The list will be assigned directly, not copied.
        """
        self._id = identifier
        self._do_infra = do_infrastructure
        if references:
            self._references = references
        else:
            self._references = {}
        if alias_identifiers:
            self._alias_identifiers = alias_identifiers
        else:
            self._alias_identifiers = []
    
    def _get_do_infrastructure(self):
        return self._do_infra        
    
    infrastructure = property(_get_do_infrastructure, doc="The infrastructure this instance is using.")
        
    def _set_resource_location(self, location):
        """
        Sets the resource location of this DO.
        
        :param location: A string which provides domain-relevant information about the location of the referenced
            resource.
        """
        self._do_infra._write_pid_value(self._id, 1, "URL", location)
        
    def _get_resource_location(self):
        v = self._do_infra._read_pid_value(self._id, 1)
        if not v:
            return None
        return v[1]

    resource_location = property(_get_resource_location, _set_resource_location, doc="The location of the resource this DO refers to.")
        
    def _get_resource_type(self):
        v = self._do_infra._read_pid_value(self._id, 2)
        if not v:
            return None
        return v[1]
    
    def _set_resource_type(self, resource_type):
        self._do_infra._write_pid_value(self._id, 2, "RESOURCE_TYPE", resource_type)

    _resource_type = property(_get_resource_type, _set_resource_type, doc="The type of this Digital Object's external data. The type of this Digital Object may also be implicit through its class; then, the resource type should be None.")

    def __get_id(self):
        return self._id
    
    identifier = property(__get_id, doc="The full identifier of this Digital Object (read-only).")

    def __str__(self, *args, **kwargs):
        return self._id
    
    def __hash__(self, *args, **kwargs):
        return hash(self._id)
    
    def __eq__(self, other):
        if isinstance(other, DigitalObject):
            return self._id == other._id
        else:
            return False
    
    def add_do_reference(self, semantics, reference):
        """
        Adds a reference to another Digital Object.
        
        :param semantics: A string or Digital Object describing the semantics of this relation. In case of a string, the
          semantics are only interpretable by humans or specialized user code. Using a Digital Object provides a safe 
          method to formalize semantics.
        :param reference: The referenced entity. Must be either a PID string or (preferably) a Digital Object.
        """
        # resolve reference to a native DO
        if isinstance(reference, DigitalObject):
            ref = reference.identifier
        else:
            if DigitalObject.is_PID_name(reference):
                # lookup PID to check for valid object, then use its identifier (which should be equal to reference)
                ref = self._do_infra.lookup_pid(reference)
                if not ref:
                    raise ValueError("Unable to resolve: %s" % reference)
                ref = ref.identifier
            else:
                raise ValueError("Invalid reference: %s" % reference)
        # analyze semantics parameter
        if isinstance(semantics, DigitalObject):
            ref_key = semantics.identfier
        else:
            ref_key = semantics
        # now store in list, create a new list if necessary
        if not ref_key in self._references:
            self._references[ref_key] = [ref]
        else:
            self._references[ref_key].append(ref)
        # write to do-infra
        self._do_infra._write_reference(self._id, ref_key, self._references[ref_key])
        
    def remove_do_reference(self, semantics, reference):
        """
        Removes the given reference to the given object.
        
        :param semantics: Indicates the relationship that should be removed. Can be either an arbitrary string or a 
          Digital Object instance. It is not safe to use a PID string here, although it might work occasionally.
        :param reference: The referenced object whose relationship should be removed. Can be a Digital Object or a PID.
        :returns: True on success, False if the specified reference did not exist
        """
        # resolve reference to a native DO
        if isinstance(reference, DigitalObject):
            ref = reference.identifier
        else:
            if DigitalObject.is_PID_name(reference):
                # lookup PID to check for valid object, then use its identifier (which should be equal to reference)
                ref = self._do_infra.lookup_pid(reference)
                ref = ref.identifier
            else:
                raise ValueError("Invalid reference: %s" % reference)
        # analyze semantics parameter
        if isinstance(semantics, DigitalObject):
            ref_key = semantics.identfier
        else:
            ref_key = semantics
        # now remove from list
        if ref_key in self._references:
            self._references[ref_key].remove(ref)
            self._do_infra._write_reference(self._id, ref_key, self._references[ref_key])
            return True
        else:
            return False
        

    def remove_do_references(self, semantics):
        """
        Removes all references of given semantics to any object.
        
        :param semantics: Indicates the relationship that should be removed. Can be either an arbitrary string or a 
          Digital Object instance. It is not safe to use a PID string here, although it might work occasionally.
        :returns: True if references of given semantics existed and all of them were removed, False if no references with given semantics 
          existed
        """
        # analyze semantics parameter
        if isinstance(semantics, DigitalObject):
            ref_key = semantics.identfier
        else:
            ref_key = semantics
        # now remove whole list
        if ref_key in self._references:
            del self._references[ref_key]
            self._do_infra._write_references(self._id, ref_key, None)
            return True
        else:
            return False
        
    def get_references(self, semantics):
        """
        Retrieves all referenced objects where the relationship type is the given semantics.
        
        :param semantics: Indicates the relationship that is to be resolved. Can either be an arbitrary string or a
          Digital Object instance. It is not safe to use a PID string here, although it might work occasionally.
        :returns: A list of Digital Objects that matches the given relationship. The list will be empty if no such 
          relationships exist.
        """
        refs = self.get_reference_pids(semantics)
        res = []
        for r in refs:
            # assume r is a string PID
            dobj = self._do_infra.lookup_pid(r)
            res.append(dobj)
        return res
    
    def get_reference_pids(self, semantics):
        """
        Returns all PIDs of referenced objects where the relationship type is the given semantics.

        :param semantics: Indicates the relationship that is to be resolved. Can either be an arbitrary string or a
          Digital Object instance. It is not safe to use a PID string here, although it might work occasionally.
        :returns: A list of strings that are PIDs. The list will be empty if no references with given relationship 
          semantics exist.
        """
        # analyze semantics parameter
        if isinstance(semantics, DigitalObject):
            ref_key = semantics.identfier
        else:
            ref_key = semantics
        # early exit if no such reference exists
        if not ref_key in self._references:
            return []
        # otherwise, assemble list of pids
        refs = self._references[ref_key]
        return refs
        
    
    def iter_reference_keys(self):
        """
        Returns an iterator over all reference keys.
        """
        return self._references.iterkeys()
         

    @staticmethod
    def is_PID_name(s):
        """
        Checks whether the given string looks like a syntactically valid PID name.
        
        Syntactically valid PIDs are described as::
        
            PID := Prefix, '/', Suffix;
            Suffix := { ? any character ? }
            Prefix := ? digit ?, { PrefixChar }, [ { Subprefix } ]
            Subprefix := '.', PrefixChar, { PrefixChar }
            PrefixChar := 'a'-'z' | 'A'-'Z' | '0'-'9' | '_'
        
        :returns: True or False
        """
        if REGEX_PID.match(s):
            return True
        else:
            return False 
        
    def get_alias_identifiers(self):
        """
        Returns a list of alias identifier strings that this Digital Object was resolved through. 
        
        Note that this does in no way contain all alias identifiers that lead to this object.
        
        If the list has more than one entry, the elements have to be seen as pointers from one to the next.
        
        :returns: A list (may be empty).
        """
        return list(self._alias_identifiers)

    def set_property_value(self, property_index, property_name, property_value):
        """
        Sets a property value (key-metadata). Properties can be freely defined by any method or user and do not have
         particular semantics within LAPIS.
        
        :param property_index: Index number for the property. Currently, only indices between 2 and 999 are defined to be freely available
          (100 excluded), though the method will not enforce this. If the index is already in use, the method will overwrite it only if the property names are identical.
          This is designed to prevent accidental overwrites of important internal properties (e.g. hash map length).
        :param property_name: Name of the property.
        :param property_value: Value of the property. This can be any type, which will however be converted to a String. 
          The value may also be empty or None, in which case the property has a flag-type behaviour.
        """
        current = self.infrastructure._read_pid_value(self.identifier, property_index)
        if current and current[0] != property_name:
            raise PropertyNameMismatchError("Tried to assign value %s to a property with new type %s to existing type %s at index %s of identifier %s" 
                                            % (property_value, property_name, current[0], property_index, self.identifier))            
        self.infrastructure._write_pid_value(self.identifier, property_index, "%s" % property_name, "%s" % property_value)
    
    def get_property_value(self, property_index):
        """
        Reads a property value (key-metadata).
        
        :param property_name: Name of the property.
        :returns: Tuple with (name, value) of the property. The value will always be a string, except that it may be 
          empty/None, indicating a flag-type property.
        :raises: :exc:`KeyError` if the property has not been set.
        """
        r = self.infrastructure._read_pid_value(self.identifier, property_index)
        if not r:
            raise KeyError("Could not get property value: Index %s unassigned on identifier %s!" % (property_index, self.identifier))
        return r
    
    def is_property_assigned(self, property_index):
        """
        Checks whether the property at given index has been assigned.
        
        :param property_index: Index of the property.
        :returns: True or False.
        """
        r = self.infrastructure._read_pid_value(self.identifier, property_index)
        return r != None
        
    def _write_parent_info(self, parent_dobj):
        """
        Writes a reference to a parent object.
        
        :param: parent_dobj: The parent digital object.
        :returns: the slot number (starting at 0, specific to the type of collection of parent_dobj)
        """
        freeslot = 0
        parent_segment_target_mask = (parent_dobj.CHARACTERISTIC_SEGMENT_NUMBER << SEGMENT_PARENTS_TARGET_MASK_BITS) + SEGMENT_PARENTS_MASK_VALUE 
        while True:
            v = self._do_infra._read_pid_value(self.identifier, parent_segment_target_mask + freeslot)
            if v:
                freeslot += 1
                if v == MAX_PARENTS:
                    raise Exception("No more free parent slots in %s (starting at Index %s)!" % (self.identifier, parent_segment_target_mask))
                continue
            break
        # now write to freeslot
        self._do_infra._write_pid_value(self.identifier, parent_segment_target_mask + freeslot, VALUETYPE_PARENT_OBJECT, parent_dobj.identifier)
        return freeslot
    
    def _remove_parent_info(self, parent_dobj):
        """
        Removes a reference to the given parent object.
        
        :param: parent_dobj: The parent digital object.
        :returns: the slot number (starting at 0, specific to the type of collection of parent_dobj)
        """
        dobj_slot = 0
        parent_segment_target_mask = (parent_dobj.CHARACTERISTIC_SEGMENT_NUMBER << SEGMENT_PARENTS_TARGET_MASK_BITS) + SEGMENT_PARENTS_MASK_VALUE
        while True:
            v = self._do_infra._read_pid_value(self.identifier, parent_segment_target_mask + dobj_slot)
            if not v or dobj_slot == MAX_PARENTS:
                raise ValueError("Object %s is not part of given parent collection %s!" % (self.identifier, parent_dobj.identifier))
            if v[1] == parent_dobj.identifier:
                break
            dobj_slot += 1
        # now remove info from slot
        self._do_infra._remove_pid_value(self.identifier, parent_segment_target_mask + dobj_slot)
        result = dobj_slot
        # must also shift all higher entries so that there are no gaps - if there were gaps, the 'if not v' in the loop
        # above will not work as expected
        while dobj_slot < MAX_PARENTS:
            dobj_slot += 1
            v = self._do_infra._read_pid_value(self.identifier, parent_segment_target_mask + dobj_slot)
            if not v: 
                break
            self._do_infra._write_pid_value(self.identifier, parent_segment_target_mask + dobj_slot - 1, v[0], v[1])
        return result
    
    def get_parent_pids(self, characteristic_segment_number):
        """
        Returns a set of all parent PIDs who are of given collection type.
        
        :param: characteristic_segment_number: designates the type of collection to filter.
        """
        offset = (characteristic_segment_number << SEGMENT_PARENTS_TARGET_MASK_BITS) + SEGMENT_PARENTS_MASK_VALUE
        i = 0
        parents = set()
        while i < MAX_PARENTS:
            v = self._do_infra._read_pid_value(self.identifier, offset + i)
            if not v:
                break
            parents.add(v[1])
            i += 1 
        return parents
                    

class PropertyNameMismatchError(Exception):
    """
    Exception thrown when trying to assign a value to a property at an index where an existing property of different
    name is already stored.
    """   
    pass

