'''
Created on 20.04.2012

@author: tobiasweigel
'''
from random import Random
import string
from dkrz.pid.model.pid import PID

class PIDInfrastructure(object):
    """
    A PID Infrastructure (factory for PID instances).
    """


    def __init__(self):
        """
        Constructor
        """
        self.random = Random()
        
    def create_pid(self, pid_class=None, identifier=None):
        """
        Factory method. Creates a new PID and returns the instance.
        
        @param pid_class: The class of PID to manufacture. Defaults to None, which will generate this infrastructure's
            default PID class.
        @param identifier: The identifier string to use for the new instance. If None, the method will use a random 
            identifier.
        @raise PIDAlreadyExistsError: If the given identifier already exists. No new PID will be created. 
        """
        id = identifier
        if not id:
            success = False
            while not success:
                id = self.generate_random_identifier()
                try:
                    self.__acquire_pid(id)
                    success = True
                except PIDAlreadyExistsError:
                    success = False # re-generate random PID and retry
                except:
                    raise # escalate
        # we have an id, now we can create the PID object
        pid = PID(self, id)
        return pid
    
    def generate_random_identifier(self):
        """
        Generates a random identifier string. The uniqueness of the identifier cannot be guaranteed.
        """
        # generate a 16 character long random hash
        allowed = string.ascii_lowercase+string.digits
        return "".join([self.choice(allowed) for i in range(1, 4)]) 

    
    def __acquire_pid(self, identifier):
        """
        Tries to acquire the given identifier. May fail if the identifier is already taken.
        @raises PIDAlreadyExistsError: if the identifier is already taken.
        @return: The acquired identifier. This may slightly differ from the given identifier (special pre-/suffixes).
        """
        raise NotImplementedError()
    
    def lookup_pid(self, identifier):
        """
        Resolves the given identifier string to a PID object.
        @param identifier: the full identifier string to resolve.
        @return: a PID object or None if the identifier is still unassigned.
        """
        raise NotImplementedError()
    
    def write_annotations(self, identifier, annotations):
        """
        Writes the annotations for the given identifier. Existing annotations are replaced/overwritten.
        @param identifier: string identifier.
        @param annotations: a dict with string keys and arbitrarily typed values.
        """
        raise NotImplementedError()
    
    def write_annotation(self, identifier, key, value):
        """
        Sets the annotation of the given identifier and key to the given value.
        @param identifier: string identifier.
        @param key: string key.
        @param value: arbitrarily typed value.
        """
        raise NotImplementedError()
    
    def write_resource_location(self, identifier, resource_location):
        """
        Sets the resource location for the given identifier.
        @param resource_location: the resource location (string).
        """
        raise NotImplementedError()
    
class HandleInfrastructure(PIDInfrastructure):
    """
    Specialization of the general PID infrastructure based on the Handle System.
    """ 
    
    
class PIDAlreadyExistsError(Exception):
    pass