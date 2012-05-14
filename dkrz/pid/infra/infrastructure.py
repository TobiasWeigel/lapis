'''
Created on 20.04.2012

@author: tobiasweigel
'''
from random import Random
import string
from dkrz.pid.model.pid import PID

RESOURCE_LOCATION_TYPE_URL = "URL"

class PIDInfrastructure(object):
    """
    A PID Infrastructure (factory for PID instances).
    
    This is the main interface class for higher-level services that use PIDs. The infrastructure class must be
    specialized to work on an underlying 'real-world' PID infrastructure (e.g. the Handle System).
    """


    def __init__(self):
        """
        Constructor
        """
        self._random = Random()
        
    def set_random_seed(self, seed):
        """
        Sets the random seed for the random identifier name generator.
        @param seed: the seed to use. 
        """
        self._random.seed(seed)
        
    def create_pid(self, identifier=None, pid_class=None):
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
                id = self._generate_random_identifier()
                try:
                    self._acquire_pid(id)
                    success = True
                except PIDAlreadyExistsError:
                    success = False # re-generate random PID and retry
                except:
                    raise # escalate
        else:
            self._acquire_pid(id)
        # we have an id, now we can create the PID object
        pid = PID(self, id)
        return pid
    
    def _generate_random_identifier(self):
        """
        Generates a random identifier string. The uniqueness of the identifier is likely but cannot be guaranteed.
        Any code using this function must synchronously check for the existence of the generated identifier before
        acquiring it for a new object.
        """
        # generate a 16 character long random hash
        allowed = string.ascii_lowercase+string.digits
        return "-".join("".join([self._random.choice(allowed) for i in range(0, 4)]) for j in range(0, 4))
    
    def _acquire_pid(self, identifier):
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
    
    def _write_all_annotations(self, identifier, annotations):
        """
        Writes the annotations for the given identifier. All existing annotations, even for keys not in the given
        annotations dict, are cleared prior to rewrite, i.e. the method performs a full replacement operation. Thus,
        you can also use this method to clear all annotations.
        @param identifier: string identifier.
        @param annotations: a dict with string keys and arbitrarily typed values.
        """
        raise NotImplementedError()
    
    def _write_annotation(self, identifier, key, value):
        """
        Sets the annotation of the given identifier and key to the given value. Annotations of different keys remain
        unchanged.
        @param identifier: string identifier.
        @param key: string key.
        @param value: arbitrarily typed value.
        """
        raise NotImplementedError()
    
    def _write_resource_location(self, identifier, resource_location, resource_location_type=RESOURCE_LOCATION_TYPE_URL):
        """
        Sets the resource location for the given identifier.
        @param resource_location: the resource location (string).
        @param resource_location_type: how is the location reference? Typically, this will be through a URL (default), 
          but a caller may also specify any other type String. Note that the particular underlying infrastructure may
          assign meaning to specific types. 
        """
        raise NotImplementedError()
    
    def delete_pid(self, identifier):
        """
        Deletes the given identifier. Be careful, this operation cannot be undone!
        """
        raise NotImplementedError()
    
    
class InMemoryInfrastructure(PIDInfrastructure):
    """
    A PID infrastructure that only exists in memory and is thus not persistent per se. Use only for testing purposes,
    since performance may be low - the way this class is implemented is targeted at testing and thus it does not
    store real PID instances (as would be very suitable) but rather proxy objects that are 'written to'.
    """
    
    class InMemoryElement(object):
        """
        Helper class that stores the data of a specific PID. Though it would be simpler to store PID instances directly,
        by way of rewriting the data to the instances of this helper class, the storage procedure is closer to real
        PID infrastructures and thus better suited for testing.
        """
        
        def __init__(self, pid):
            """
            Takes the given PID instance and stores its content in special attributes. Will not store the PID instance 
            itself!
            """
            self._annotations = {}
            for k,v in pid.iter_annotations():
                self._annotations[k] = v 
            self._resource_location = pid.resource_location
            self._pid_type = pid.pid_type
            
        def build_pid_instance(self, pid_infra, identifier):
            """
            Generates a PID instance from the information stored in this memory element object.
            """
            pid = PID(pid_infra, identifier)
            pid._resource_location = self._resource_location
            pid._pid_type = self._pid_type
            pid.set_annotations(self._annotations)
            return pid
    
    def __init__(self):
        super(InMemoryInfrastructure, self).__init__()
        # self._storage is a dict mapping identifier strings to real PID instances 
        self._storage = dict()
        
    def create_pid(self, identifier=None, pid_class=None):
        # calling superclass method here will also cause _acquire_pid to be called
        pid = PIDInfrastructure.create_pid(self, identifier, pid_class)
        # store new InMemoryElement in storage
        self._storage[pid.identifier] = InMemoryInfrastructure.InMemoryElement(pid)
        return pid
        
    def _acquire_pid(self, identifier):
        if identifier in self._storage:
            raise PIDAlreadyExistsError()
        self._storage[identifier] = 0 # dummy value to reserve key
        
    def lookup_pid(self, identifier):
        ele = self._storage.get(identifier)
        if not ele:
            return None
        return ele.build_pid_instance(self, identifier)
    
    def _write_annotation(self, identifier, key, value):
        ele = self._storage.get(identifier)
        if not ele:
            raise KeyError
        ele._annotations[key] = value

    def _write_annotations(self, identifier, annotations):
        ele = self._storage.get(identifier)
        if not ele:
            raise KeyError
        ele._annotations = annotations
        
    def _write_resource_location(self, identifier, resource_location):
        ele = self._storage.get(identifier)
        if not ele:
            raise KeyError
        ele._resource_location = resource_location
        
    
class PIDAlreadyExistsError(Exception):
    pass
