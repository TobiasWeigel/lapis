'''
Created on 02.05.2012

@author: tobiasweigel
'''
from pid import PID
from pid import PID_TYPE_SET

class PIDSet(PID):
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
        self._pid_type = PID_TYPE_SET
        
    def add_pid(self, pid):
        """
        Adds one or more PID objects to the set.
        @param pid: Either a PID instance or a list of PID instances.  
        """
        if isinstance(pid, list):
            for x in pid:
                if not isinstance(x, PID):
                    raise ValueError("The given list contains objects that are no PID instances!")
            self.elements.update(pid)
        else:
            if not isinstance(pid, PID):
                raise ValueError("The given object is not a PID instance: %s" % pid)
            self.elements.add(pid)
    
    def remove_pid(self, pid):
        """
        Removes the given PID object(s) from the set.
        @param pid: Either a PID instance or a list of PID instances.
        """
        if isinstance(pid, list):
            for x in pid:
                if not isinstance(x, PID):
                    raise ValueError("The given list contains objects that are no PID instances!")
            self.elements.difference_update(pid)
        else:
            if not isinstance(pid, PID):
                raise ValueError("The given object is not a PID instance: %s" % pid)
            self.elements.remove(pid)

    def contains_pid(self, pid):
        """
        Check if the set contains the given PID(s).
        @param pid: A PID instance or a list of PID instances.
        @return: True if all given PIDs are contained in this set.
        """
        if isinstance(pid, list):
            for x in pid:
                if not isinstance(x, PID):
                    raise ValueError("The given list contains objects that are no PID instances!")
                if not x in self.elements:
                    return False
            return True
        else:
            if not isinstance(pid, PID):
                raise ValueError("The given object is not a PID instance: %s" % pid)
            return pid in self.elements
        
    def iterate(self):
        """
        Iterate over the elements in the PID set.
        @return: an iterator object
        """
        return iter(self.elements)
    
    