'''
Created on 20.04.2012

:author: tobiasweigel
'''
from random import Random
import string
from dkrz.digitalobjects.model.do import DigitalObject

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
            identifier.
        :raises PIDAlreadyExistsError: If the given identifier already exists. No new PID will be allocated and no DO 
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
            self._acquire_pid(id)
        # we have an id, now we can create the DO object
        pid = DigitalObject(self, id)
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
        :raises PIDAlreadyExistsError: if the identifier is already taken.
        :return: The acquired identifier. This may slightly differ from the given identifier (special pre-/suffixes).
        """
        raise NotImplementedError()
    
    def lookup_pid(self, identifier):
        """
        Resolves the given identifier string to a Digital Object.
        :param identifier: the full identifier string to resolve.
        :return: a Digital Object or None if the identifier is still unassigned.
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
    
    def _write_resource_location(self, identifier, resource_location, resource_type=None):
        """
        Sets the resource location for the Digital Object with given identifier, i.e. sets the data of the Digital 
        Object to an external resource.
        :param resource_location: the resource location (string).
        :param resource_type: the type of resource existing at the location. Defaults to None for unspecified resource
          type. 
        """
        raise NotImplementedError()
    
    def delete_do(self, identifier):
        """
        Deletes the Digital Object with given identifier. Be careful, this operation cannot be undone!
        """
        raise NotImplementedError()
    
    
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
        
        def __init__(self, do):
            """
            Takes the given DO instance and stores its content in special attributes. Will not store the DO instance 
            itself!
            """
            self._annotations = {}
            for k,v in do.iter_annotations():
                self._annotations[k] = v 
            self._resource_location = do.resource_location
            self._resource_type = do.resource_type
            
        def build_do_instance(self, do_infra, identifier):
            """
            Generates a PID instance from the information stored in this memory element object.
            """
            dobj = DigitalObject(do_infra, identifier)
            dobj._resource_location = self._resource_location
            dobj._resource_type = self._resource_type
            dobj.set_annotations(self._annotations)
            return dobj
    
    def __init__(self):
        super(InMemoryInfrastructure, self).__init__()
        # self._storage is a dict mapping identifier strings to real PID instances 
        self._storage = dict()
        
    def create_do(self, identifier=None, do_class=None):
        # calling superclass method here will also cause _acquire_pid to be called
        dobj = DOInfrastructure.create_do(self, identifier, do_class)
        # store new InMemoryElement in storage
        self._storage[dobj.identifier] = InMemoryInfrastructure.InMemoryElement(dobj)
        return dobj
    
    def delete_do(self, identifier):
        del self._storage[identifier]
        
    def _acquire_pid(self, identifier):
        if identifier in self._storage:
            raise PIDAlreadyExistsError()
        self._storage[identifier] = 0 # dummy value to reserve key
        
    def lookup_pid(self, identifier):
        ele = self._storage.get(identifier)
        if not ele:
            return None
        return ele.build_do_instance(self, identifier)
    
    def _write_annotation(self, identifier, key, value):
        ele = self._storage.get(identifier)
        if not ele:
            raise KeyError
        ele._annotations[key] = value

    def _write_annotations(self, identifier, annotations):
        ele = self._storage.get(identifier)
        if not ele:
            raise KeyError
        ele._annotations.update(annotations)
        
    def _write_resource_location(self, identifier, resource_location, resource_type=None):
        ele = self._storage.get(identifier)
        if not ele:
            raise KeyError
        ele._resource_location = resource_location
        ele._resource_type = resource_type

    def _write_all_annotations(self, identifier, annotations):
        ele = self._storage.get(identifier)
        if not ele:
            raise KeyError
        ele.a_annotations = annotations
        
    
class PIDAlreadyExistsError(Exception):
    pass
