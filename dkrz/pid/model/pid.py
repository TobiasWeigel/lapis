"""
Created on 20.04.2012

@author: tobiasweigel
"""
from dkrz.pid.infra.infrastructure import PIDAlreadyExistsError

class PID(object):
    """
    Persistent Identifier representation in native Python.
    Changes to the object cause changes in the underlying PID infrastructure.
    
    A PID consists of a globally unique, resolvable identifier, provided by the PID infrastructure, a resource location
    for digital materual and associated metadata, called annotations. Annotations have the form of key-value pairs. 
    Keys are strings, the value is not specifically typed (octet-stream).
    """

    def __init__(self, pid_infrastructure, identifier):
        """
        Constructor. Only called by the factory.

        @param pid_infrastructure: The PID infrastructure interface to use.
        @param identifier: The already acquired identifier to associate the object with. 

        """
        self.annotations = {}
        self.resource = None
        self.id = identifier
        self.pid_infra = pid_infrastructure
        self.resource_location = None

    def set_annotations(self, annotations):
        """
        Overwrites all annotations for this PID with the new ones given in a dictionary.
        
        @param annotations: New annotations to replace the old ones (if any). Must be a dictionary.  
        """
        self.annotations = annotations.copy()
        self.pid_infra.write_annotations(self.id, annotations)
        
    def set_annotation(self, key, value):
        """
        Sets the annotation with given key to a new value.
        
        @param key: A string key.
        @param value: An arbitrarily typed value.
        """
        key_s = str(key)
        self.annotations[key_s] = value
        self.pid_infra.write_annotation(self.id, key_s, value)
        
    def clear_annotations(self):
        """
        Clears all annotations. This does not affect the resource location and similar informations.
        """
        self.annotations = {}
        self.pid_infra.write_annotations(self.id, {})
        
    def set_resource_location(self, location):
        """
        Sets the resource location of this PID.
        @param location: A string which provides domain-relevant information about the location of the referenced
            resource.
        """
        self.resource_location = location
        self.pid_infra.write_resource_location(self.id, self.resource_location)  
        
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
        