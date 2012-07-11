'''
Created on 02.05.2012

:author: tobiasweigel
'''
from dkrz.digitalobjects.model.do import DigitalObject

REFERENCE_SUBELEMENT = "subelement"
REFERENCE_SUBELEMENT_OF = "subelement-of"

class DigitalObjectSet(DigitalObject):
    '''
    A set (unsorted collection) of Digital Objects (or further sub-DO-sets).
    
    The set does not impose specific semantics. It may be used both for arbitrary collections of largely
    unrelated objects as well as hierarchical structures of data objects that are strongly connected.
    
    This is what Kahn and Wilensky informally refer to as a meta-object - a digital object whose data is of type 
    "set-of-handles".

    Internally, the set is maintained through DO references. The underlying infrastructure may serialize this structure
    in a different form.
    '''
    
    RESOURCE_TYPE = "DIGITAL_OBJECT_SET"
    
    class LazySetIterator(object):
        """
        Special iterator that retrieves Digital Objects on access and through the set's object cache.
        """
        
        def __init__(self, doset):
            self._doset = doset
            self._set_iter = iter(doset._elements) 
        
        def __iter__(self):
            return self
        
        def next(self):
            n_id = self._set_iter.next()
            dobj = self._doset._object_cache.get(n_id, None)
            if not dobj:
                # retrieve through do_infra
                dobj = self._doset._do_infra.lookup_pid(n_id)
                self._doset._object_cache[n_id] = dobj
            return dobj

    def __init__(self, do_infrastructure, identifier, annotations = None, references = None, alias_identifiers = None):
        '''
        Constructor
        '''
        super(DigitalObjectSet, self).__init__(do_infrastructure, identifier, annotations, resource_location=None, resource_type=None, references=references, alias_identifiers=alias_identifiers)
        self._elements = set()
        self._object_cache = {}
        self._resource_type = DigitalObjectSet.RESOURCE_TYPE
        self._resource_location = None
        self._do_infra._write_resource_information(self._id, self._resource_location, self._resource_type)
        # parse given subelement references, if any
        ref = self._references.get(REFERENCE_SUBELEMENT)
        if ref:
            for r in ref:
                self._elements.add(r)
                
    def add_do(self, dobj):
        """
        Adds one or more Digital Objects to the set.
        
        :param dobj: Either a DO instance or a list of DO instances.  
        """
        if isinstance(dobj, list):
            for x in dobj:
                if not isinstance(x, DigitalObject):
                    raise ValueError("The given list contains objects that are no Digital Object instances!")
                self._elements.add(x.identifier)
                self._object_cache[x.identifier] = x
                self.add_do_reference(REFERENCE_SUBELEMENT, x)
                x.add_do_reference(REFERENCE_SUBELEMENT_OF, self)
        else:
            if not isinstance(dobj, DigitalObject):
                raise ValueError("The given object is not a Digital Object instance: %s" % dobj)
            self._elements.add(dobj.identifier)
            self._object_cache[dobj.identifier] = dobj
            self.add_do_reference(REFERENCE_SUBELEMENT, dobj)
            dobj.add_do_reference(REFERENCE_SUBELEMENT_OF, self)
    
    def remove_do(self, dobj):
        """
        Removes the given Digital Object(s) from the set.
        
        :param dobj: Either a DO instance or a list of DO instances.
        """
        if isinstance(dobj, list):
            for x in dobj:
                if not isinstance(x, DigitalObject):
                    raise ValueError("The given list contains objects that are no Digital Object instances!")
                self.remove_do_reference(REFERENCE_SUBELEMENT, x)
                x.remove_do_reference(REFERENCE_SUBELEMENT_OF, self)
                self._elements.remove(x.identifier)
                if x.identifier in self._object_cache:
                    del self._object_cache[x.identifier]
        else:
            if not isinstance(dobj, DigitalObject):
                raise ValueError("The given object is not a Digital Object instance: %s" % dobj)
            self.remove_do_reference(REFERENCE_SUBELEMENT, dobj)
            dobj.remove_do_reference(REFERENCE_SUBELEMENT_OF, self)
            self._elements.remove(dobj.identifier)
            if dobj.identifier in self._object_cache:
                del self._object_cache[dobj.identifier]

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
                if not x.identifier in self._elements:
                    return False
            return True
        else:
            if not isinstance(dobj, DigitalObject):
                raise ValueError("The given object is not a Digital Object instance: %s" % dobj)
            return dobj.identifier in self._elements
        
    def iter_set_elements(self):
        """
        Iterate over the _elements in the Digital Object set.
        
        :return: an iterator object
        """
        return DigitalObjectSet.LazySetIterator(self)
    
    def __iter__(self):
        return self.iter_set_elements()
    
    