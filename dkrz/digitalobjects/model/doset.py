'''
Created on 02.05.2012

@author: tobiasweigel
'''
from dkrz.digitalobjects.model.do import DigitalObject

class DigitalObjectSet(DigitalObject):
    '''
    A set (unsorted collection) of PIDs (or further sub-PID-sets).
    
    The set does not impose specific semantics. It may be used both for arbitrary collections of largely
    unrelated objects as well as hierarchical structures of data objects that are strongly connected.
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.elements = set()
        self._resource_type = None
        
    def add_do(self, dobj):
        """
        Adds one or more Digital Objects to the set.
        @param dobj: Either a DO instance or a list of DO instances.  
        """
        if isinstance(dobj, list):
            for x in dobj:
                if not isinstance(x, DigitalObject):
                    raise ValueError("The given list contains objects that are no Digital Object instances!")
            self.elements.update(dobj)
        else:
            if not isinstance(dobj, DigitalObject):
                raise ValueError("The given object is not a Digital Object instance: %s" % dobj)
            self.elements.add(dobj)
    
    def remove_do(self, dobj):
        """
        Removes the given PID object(s) from the set.
        @param dobj: Either a PID instance or a list of PID instances.
        """
        if isinstance(dobj, list):
            for x in dobj:
                if not isinstance(x, DigitalObject):
                    raise ValueError("The given list contains objects that are no Digital Object instances!")
            self.elements.difference_update(dobj)
        else:
            if not isinstance(dobj, DigitalObject):
                raise ValueError("The given object is not a Digital Object instance: %s" % dobj)
            self.elements.remove(dobj)

    def contains_do(self, dobj):
        """
        Check if the set contains the given PID(s).
        @param dobj: A DO instance or a list of DO instances.
        @return: True if all given Digital Objects are contained in this set.
        """
        if isinstance(dobj, list):
            for x in dobj:
                if not isinstance(x, DigitalObject):
                    raise ValueError("The given list contains objects that are no Digital Object instances!")
                if not x in self.elements:
                    return False
            return True
        else:
            if not isinstance(dobj, DigitalObject):
                raise ValueError("The given object is not a Digital Object instance: %s" % dobj)
            return dobj in self.elements
        
    def iterate(self):
        """
        Iterate over the elements in the Digital Object set.
        @return: an iterator object
        """
        return iter(self.elements)
    
    