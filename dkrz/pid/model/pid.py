"""
Created on 20.04.2012

@author: tobiasweigel
"""

PID_TYPE_BASE = 0
PID_TYPE_ALIAS = 1
PID_TYPE_SET = 10

VALUETYPE_DATA = 0

class PID(object):
    """
    Persistent Identifier representation in native Python.
    Changes to the object cause changes in the underlying PID infrastructure.
    
    A PID consists of a globally unique, resolvable identifier, provided by the PID infrastructure, a resource location
    for digital material and associated metadata, called annotations. Annotations have the form of key-value pairs. 
    Keys are strings, the value is not specifically typed (octet-stream). Keys are unique. If more than one value should
    be assigned to one key, use a list as the key value.
    """

    def __init__(self, pid_infrastructure, identifier, annotations = {}, resource_location = None, pid_type = PID_TYPE_BASE):
        """
        Constructor. Only called by the factory.

        @param pid_infrastructure: The PID infrastructure interface to use.
        @param identifier: The already acquired identifier to associate the object with.
        @param annotations: The annotations to initialize this PID with. Note that the given dict is not copied, but
          assigned directly.
        @param resource_location: The resource location to set this PID to.
        @param pid_type: the PID type.         

        """
        self._annotations = annotations
        self._id = identifier
        self._pid_infra = pid_infrastructure
        self._resource_location = resource_location
        self._pid_type = pid_type
        
    def __hash__(self, *args, **kwargs):
        return self._id
      

    def set_annotations(self, annotations):
        """
        Overwrites all annotations for this PID with the new ones given in a dictionary.
        
        @param annotations: New annotations to replace the old ones (if any). Must be a dictionary.  
        """
        self._annotations = annotations.copy()
        self._pid_infra._write_all_annotations(self._id, annotations)
        
    def set_annotation(self, key, value):
        """
        Sets the annotation with given key to a new value.
        
        @param key: A string key. A key may also be seen as a type, but note that this is not a data type in the strict 
          sense, but rather a semantic specification (i.e. 'e-mail' or 'url', where the data type is both String).
        @param value: An arbitrarily typed value.
        """
        key_s = str(key)
        self._annotations[key_s] = value
        self._pid_infra._write_annotation(self._id, key_s, value)
        
    def get_annotation(self, key):
        """
        Returns the annotation value for the given key.
        
        @param key: A string key.
        @return: The value associated with the key or None if key did not exist
        """
        key_s = str(key)
        return self._annotations.get(key_s)
        
    def iter_annotations(self):
        """
        Returns an iterator over all annotations
        """
        return iter(self._annotations)
        
    def clear_annotations(self):
        """
        Clears all annotations. This does not affect the resource location and similar informations.
        """
        self._annotations = {}
        self._pid_infra._write_all_annotations(self._id, {})

    def _set_resource_location(self, location):
        """
        Sets the resource location of this PID.
        @param location: A string which provides domain-relevant information about the location of the referenced
            resource.
        """
        self._resource_location = location
        self._pid_infra._write_resource_location(self._id, self._resource_location)
        
    def _get_resource_location(self):
        return self._resource_location

    resource_location = property(_get_resource_location, _set_resource_location, doc="The location of the resource this PID refers to.")
        
    def __get_pid_type(self):
        return self._pid_type    

    pid_type = property(__get_pid_type, doc="The PID type of this instance (read-only). Not to be confused with the resource type.")

    def __get_id(self):
        return self._id
    
    identifier = property(__get_id, doc="The full identifier of this PID (read-only).")
    

class TypedPID(PID):
    """
        Typed Persistent Identifier.
        
        This PID bears also a resource type description in the form of an arbitrary string.
    """
    
    def __init__(self, pid_infrastructure, identifier):
        super(TypedPID, self).__init__(pid_infrastructure, identifier)
        self.resource_type = None
        
    def set_resource_type(self, resource_type):
        """
        Sets the resource type of this PID.
        @param resource_type: A string which provides domain-relevant information about the type of the referenced
            resource.
        """
        self.resource_type = resource_type
        self.pid_infra.write_resource_type(self.id, self.resource_type)
        
    def set_resource(self, res_type, location):
        """
        Sets resource type and location of this PID,
        @param res_type: Resource type.
        @param location: Resource location.
        """
        self.set_resource_location(location)
        self.set_resource_type(res_type)
        
        
