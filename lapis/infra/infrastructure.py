'''
Created on 20.04.2012

:author: tobiasweigel

Copyright 2012 Tobias Weigel

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''
from random import Random
import string
from lapis.model.do import DigitalObject
from lapis.model.doset import DigitalObjectSet

class DOInfrastructure(object):
    """
    A Digital Object Infrastructure (factory for Digital Object instances).
    
    This is the main interface class for higher-level services that use Digital Objects. The infrastructure class must 
    be specialized to work on an underlying 'real-world' DO infrastructure (e.g. the Handle System).
    """


    def __init__(self):
        """
        Constructor
        """
        self._random = Random()
        
    def set_random_seed(self, seed):
        """
        Sets the random seed for the random identifier name generator.
        
        :param seed: the seed to use. 
        """
        self._random.seed(seed)
        
    def create_do(self, identifier=None, do_class=None):
        """
        Factory method. Creates a new DO and returns the instance.
        
        :param do_class: The class of DO to manufacture. Defaults to None, which will generate this infrastructure's
            default PID class. Not every infrastructure will support different classes of objects.
        :param identifier: The identifier string to use for the new instance. If None, the method will use a random 
            identifier (example: ``o9f9-oimx-7o8v-d0zt``)
        :return: A new :class:`.DigitalObject` instance. Note that the identifier of this instance may differ from the
          given identifier.
        :raises: :exc:`.PIDAlreadyExistsError` if the given identifier already exists. No new PID will be allocated and no DO 
          will be created. 
        """
        id = identifier
        if not id:
            success = False
            while not success:
                id = self._generate_random_identifier()
                try:
                    self._acquire_pid(id)
                    success = True
                except PIDAlreadyExistsError:
                    success = False # re-generate random PID and retry
                except:
                    raise # escalate
        else:
            id = self._acquire_pid(id)
        # we have an id, now we can create the DO object
        if do_class:
            return do_class(self, id)            
        return DigitalObject(self, id)
    
    def _generate_random_identifier(self):
        """
        Generates a random identifier string. The uniqueness of the identifier is likely but cannot be guaranteed.
        Any code using this function must synchronously check for the existence of the generated identifier before
        acquiring it for a new object.
        
        The random identifier is currently composed of 4 blocks of 4 alphanumeric characters. 
        Example: ``o9f9-oimx-7o8v-d0zt``
        
        :return: A random String
        """
        # generate a 16 character long random hash
        allowed = "abcdefghkmnpqrstuvwxyz"+string.digits
        return "-".join("".join([self._random.choice(allowed) for i in range(0, 4)]) for j in range(0, 4))
    
    def _acquire_pid(self, identifier):
        """
        Tries to acquire the given identifier. May fail if the identifier is already taken.
        
        :raises PIDAlreadyExistsError: if the identifier is already taken.
        :return: The acquired identifier. This may slightly differ from the given identifier (special pre-/suffixes).
        """
        raise NotImplementedError()
    
    def lookup_pid(self, identifier):
        """
        Resolves the given identifier string to a Digital Object.
        
        :param identifier: the full identifier string to resolve.
        :return: a :py:class:`.DigitalObject` or None if the identifier is still unassigned.
        :raises: :exc:`.PIDAliasBrokenError` if the given identifier is an alias, but the target object does not exist
          (has been deleted). Also thrown if a chain of multiple aliases fails to resolve. 
        """
        raise NotImplementedError()
    
    def _write_all_annotations(self, identifier, annotations):
        """
        Writes the annotations for the object with the given identifier. All existing annotations, even for keys not 
        in the given annotations dict, are cleared prior to rewrite, i.e. the method performs a full replacement 
        operation. Thus, you can also use this method to clear all annotations.
        
        :param identifier: string identifier, i.e. the Digital Object's PID.
        :param annotations: a dict with string keys and arbitrarily typed values.
        """
        raise NotImplementedError()
    
    def _write_annotation(self, identifier, key, value):
        """
        Sets the annotation of the object with given identifier and key to the given value. Annotations of other 
        keys remain unchanged.
        
        :param identifier: string identifier, i.e. the Digital Object's PID.
        :param key: string key.
        :param value: arbitrarily typed value.
        """
        raise NotImplementedError()
    
    def _write_resource_information(self, identifier, resource_location=None, resource_type=None):
        """
        Sets the resource location and type for the Digital Object with given identifier, i.e. sets the data of the 
        Digital Object to an external resource.
        
        Either resource_type or resource_location may be None. If the resource_type is None, the given external resource
        is of undefined or unknown type. If the resource_location is None, the resource is not an external entity, but
        a conceptual construct such as e.g. a composite or set of other Digital Objects. 
        
        :param resource_location: the resource location (string). May be None for special cases.
        :param resource_type: the type of resource existing at the location. Defaults to None for unspecified resource
          type. 
        """
        raise NotImplementedError()
    
    def delete_do(self, identifier):
        """
        Deletes the Digital Object with given identifier. Be careful, this operation cannot be undone!
        
        :raises: :exc:`KeyError` if no object exists with the given identifier 
        """
        raise NotImplementedError()
    
    def _write_reference(self, identifier, key, reference):
        """
        Sets the reference of the object with given identifier and key to the given value. Other reference entries
        remain unchanged.
        
        :param identifier: string identifier, i.e. the Digital Object's PID.
        :param key: string key.
        :param value: arbitrarily typed value. Can be a list. If value is None, 0, empty list etc., the method will
          try to remove the entry.        
        """
        raise NotImplementedError()
    
    def create_alias(self, original, alias_identifier):
        """
        Creates an alias PIDs for the given Digital Object or alias identifier.
        
        :param original: The Digital Object that should be pointed to or a PID string, which may reference an original
          DO or can be an alias PID itself.
        :alias_identifier: An identifier string for the alias.
        :returns: The identifier string of the created alias. The returned identifier may differ slightly from the given
          one, depending on the actual infrastructure implementation.
        :raises: :exc:`.PIDAlreadyExistsError` if any of the given identifier is already occupied. No alias will have
          been created.
        """
        raise NotImplementedError()
    
    def delete_alias(self, alias_identifier):
        """
        Deletes the given alias PID.
        
        If the given identifier does not exist, the method will raise a :exc:`KeyError`. If it resolves to an original 
        Digital Object, the method will return False.
        
        :param alias_identifier: Identifier string to remove.
        :returns: True if the identifier was successfully removed, False if the identifier existed, but pointed to an
          original Digital Object.
        :raises: :exc:`KeyError` if no alias exists with the given identifier.
        """
        raise NotImplementedError()
    
    def is_alias(self, alias_identifier):
        """
        Checks if the given identifier is an alias identifier.
        
        :returns: True if the identifier exists and is an alias, false if it exists and points to an original object.
        :raises: :exc:`KeyError` if the given identifier is unacquired.
        """
        raise NotImplementedError()
    
    def clean_identifier_string(self, s):
        """
        Removes special characters from the given string so it can be safely used
        as part of a PID identifier.
        
        :param s: The raw string
        :returns: A string that contains mostly only letters and numbers.
        """
        res = ""
        allowed = string.ascii_letters+string.digits+"_-+.,;#~!$()[]{}"
        for c in s:
            if c in allowed:
                res += c
        return res
    
    staticmethod(clean_identifier_string)
    
    
class InMemoryInfrastructure(DOInfrastructure):
    """
    A DO infrastructure that only exists in memory and is thus not persistent per se. Use only for testing purposes,
    since performance may be low - the way this class is implemented is targeted at testing and thus it does not
    store real DO instances (as would be very suitable) but rather proxy objects that are 'written to'.
    """
    
    class InMemoryElement(object):
        """
        Helper class that stores the data of a specific DO. Though it would be simpler to store DO instances directly,
        by way of rewriting the data to the instances of this helper class, the storage procedure is closer to real
        DO infrastructures and thus better suited for testing.
        """
        
        def __init__(self):
            self._annotations = {}
            self._resource_location = None
            self._resource_type = None
            self._references = {}
            self._identifier = None
        
        def read_from_do(self, do):
            """
            Takes the given DO instance and stores its content in special attributes. Will not store the DO instance 
            itself!
            """
            self._annotations = {}
            for k,v in do.iter_annotations():
                self._annotations[k] = v 
            self._resource_location = do.resource_location
            self._resource_type = do.resource_type
            self._references = {}
            for k in do.iter_reference_keys():
                self._references[k] = do.get_references(k)
            
        def build_do_instance(self, do_infra, identifier, aliases=None):
            """
            Generates a PID instance from the information stored in this memory element object.
            """
            if self._resource_type == DigitalObjectSet.RESOURCE_TYPE:
                dobj = DigitalObjectSet(do_infra, identifier, annotations=self._annotations, references=self._references, alias_identifiers=aliases)
            else:
                dobj = DigitalObject(do_infra, identifier, self._annotations, self._resource_location, self._resource_type, self._references, aliases)
            return dobj
        
    class InMemoryElementAlias(object):
        """
        Helper class that simply points to another InMemoryElement instance.
        """
        
        def __init__(self, original_id):
            if not original_id:
                raise ValueError()
            self._original_id = original_id
            
        def build_do_instance(self, do_infra, identifier, aliases=None):
            if aliases:
                al = aliases+[identifier]
            else:
                al = [identifier]
            oele = do_infra._storage.get(self._original_id)
            if not oele:
                raise PIDAliasBrokenError("Alias %s has broken target %s!" % (identifier, self._original_id))
            return oele.build_do_instance(do_infra, self._original_id, aliases=al)
            
    
    def __init__(self):
        super(InMemoryInfrastructure, self).__init__()
        # self._storage is a dict mapping identifier strings to real PID instances 
        self._storage = dict()
        
    def create_do(self, identifier=None, do_class=None):
        # calling superclass method here will also cause _acquire_pid to be called
        dobj = DOInfrastructure.create_do(self, identifier, do_class)
        # store new InMemoryElement in storage
        self._storage[dobj.identifier].read_from_do(dobj)
        self._storage[dobj.identifier]._identifier = dobj.identifier
        return dobj
    
    def delete_do(self, identifier):
        # aliases!
        ele = self._storage_resolve(identifier)
        del self._storage[ele._identifier]
        
    def _acquire_pid(self, identifier):
        if identifier in self._storage:
            raise PIDAlreadyExistsError()
        self._storage[identifier] = InMemoryInfrastructure.InMemoryElement() # empty object to reserve key
        return identifier
        
    def lookup_pid(self, identifier):
        ele = self._storage.get(identifier)
        if not ele:
            return None
        return ele.build_do_instance(self, identifier)
    
    def _storage_resolve(self, identifier):
        """
        Resolves the given identifier in the internal storage. Will follow aliases.
        """
        ele = self._storage.get(identifier)
        if not ele:
            return None
        if isinstance(ele, InMemoryInfrastructure.InMemoryElementAlias):
            return self._storage_resolve(ele._original_id)
        return ele
    
    def _write_annotation(self, identifier, key, value):
        ele = self._storage_resolve(identifier)
        if not ele:
            raise KeyError
        ele._annotations[key] = value

    def _write_annotations(self, identifier, annotations):
        ele = self._storage_resolve(identifier)
        if not ele:
            raise KeyError
        ele._annotations.update(annotations)
        
    def _write_resource_information(self, identifier, resource_location=None, resource_type=None):
        ele = self._storage_resolve(identifier)
        if not ele:
            raise KeyError
        ele._resource_location = resource_location
        ele._resource_type = resource_type

    def _write_all_annotations(self, identifier, annotations):
        ele = self._storage_resolve(identifier)
        if not ele:
            raise KeyError
        ele._annotations = annotations
        
    def _write_reference(self, identifier, key, reference):
        ele = self._storage_resolve(identifier)
        if not ele:
            raise KeyError
        ele._references[key] = reference
        
    def create_alias(self, original, alias_identifier):
        # check for existing PID
        ele = self._storage.get(alias_identifier)
        if ele:
            raise PIDAlreadyExistsError()
        # create alias
        if isinstance(original, DigitalObject):
            orig_id = original.identifier
        else:
            orig_id = original
        alele = InMemoryInfrastructure.InMemoryElementAlias(orig_id) 
        self._storage[alias_identifier] = alele
        return alias_identifier
        
    def delete_alias(self, alias_identifier):
        ele = self._storage.get(alias_identifier)
        if not ele:
            raise KeyError()
        if isinstance(ele, InMemoryInfrastructure.InMemoryElement):
            return False        
        del self._storage[alias_identifier]
        return True
    
    def is_alias(self, alias_identifier):
        ele = self._storage.get(alias_identifier)
        if not ele:
            raise KeyError()
        return isinstance(ele, InMemoryInfrastructure.InMemoryElementAlias)
            
    
class PIDAlreadyExistsError(Exception):
    """
    Exception thrown when trying to acquire an already existing PID. 
    """
    pass

class PIDAliasBrokenError(Exception):
    """
    Exception thrown when trying to resolve a PID that is an alias whose target object is lost.
    """
    pass