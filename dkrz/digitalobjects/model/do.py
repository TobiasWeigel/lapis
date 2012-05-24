"""
Created on 20.04.2012

:author: tobiasweigel
"""

VALUETYPE_DATA = 0

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
    outside of this particular Python implementation (e.g. in a data archive).
    """

    def __init__(self, do_infrastructure, identifier, annotations = {}, resource_location = None, resource_type = None):
        """
        Constructor. Only called by the factory or other infrastructure methods that construct/reconstruct KeyMD 
        instances.

        :param do_infrastructure: The DO infrastructure interface to use.
        :param identifier: The already acquired identifier to associate the object with.
        :param annotations: The annotations to initialize the metadata with. Note that independent of the particular 
        infrastructure, no resource location or object-type entries should be given in the annotations dict.
        :param resource_location: The resource location of the Digital Object's data, in case of external data.
        :param resource_type: The resource type for external data. Note that resource_location and resource_type are not
          checked for consistency by the constructor. It is the caller's task to provide meaningful values.
        """
        if not isinstance(annotations, dict):
            raise TypeError("Invalid type for annotations of a Digital Object: %s; contents: %s" % (type(annotations), repr(annotations)))
        self._id = identifier
        self._do_infra = do_infrastructure
        if resource_type and not resource_location:
            raise ValueError("You cannot provide a resource type, but no resource location!")
        # call private methods to forward values to the DO infra
        self._set_annotations(annotations)
        self._set_resource_location(resource_location)
        self._set_resource_type(resource_type)
        
    def __hash__(self, *args, **kwargs):
        return self._id
      

    def _set_annotations(self, annotations):
        """
        Overwrites all annotations for this DO with the new ones given in a dictionary.
        
        Remember that, in theory, annotations are not supposed to change after a DO has been created.
        
        :param annotations: New annotations to replace the old ones (if any). Must be a dictionary.  
        """
        self._annotations = annotations.copy()
        self._do_infra._write_all_annotations(self._id, annotations)
        
    def _set_annotation(self, key, value):
        """
        Sets the annotation with given key to a new value.

        Remember that, in theory, annotations are not supposed to change after a DO has been created.
        
        :param key: A string key. A key may also be seen as a type, but note that this is not a data type in the strict 
          sense, but rather a semantic specification (i.e. 'e-mail' or 'url', where the data type is both String).
        :param value: An arbitrarily typed value.
        """
        key_s = str(key)
        self._annotations[key_s] = value
        self._do_infra._write_annotation(self._id, key_s, value)
        
    def get_annotation(self, key):
        """
        Returns the annotation value for the given key.
        
        :param key: A string key.
        :returns: The value associated with the key or None if key did not exist
        """
        key_s = str(key)
        return self._annotations.get(key_s)
        
    def iter_annotations(self):
        """
        Returns an iterator over all annotations
        """
        return self._annotations.iteritems()
        
    def _clear_annotations(self):
        """
        Clears all annotations. This does not affect the resource location and similar informations.

        Remember that, in theory, annotations are not supposed to change after a DO has been created.
        """
        self._annotations = {}
        self._do_infra._write_all_annotations(self._id, {})

    def _set_resource_location(self, location):
        """
        Sets the resource location of this DO.
        
        :param location: A string which provides domain-relevant information about the location of the referenced
            resource.
        """
        self._resource_location = location
        self._do_infra._write_resource_location(self._id, self._resource_location, self._resource_type)
        
    def _get_resource_location(self):
        return self._resource_location

    resource_location = property(_get_resource_location, _set_resource_location, doc="The location of the resource this DO refers to.")
        
    def _get_resource_type(self):
        return self._resource_type
    
    def _set_resource_type(self, resource_type):
        self._resource_type = resource_type
        self._do_infra._write_resource_location(self._id, self._resource_location, self._resource_type)

    resource_type = property(_get_resource_type, _set_resource_type, doc="The type of this Digital Object's external data. The type of this Digital Object may also be implicit through its class; then, the resource type should be None.")

    def __get_id(self):
        return self._id
    
    identifier = property(__get_id, doc="The full identifier of this Digital Object (read-only).")

    

