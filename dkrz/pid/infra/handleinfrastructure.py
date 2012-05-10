'''
Created on 03.05.2012

@author: tobiasweigel
'''
from dkrz.pid.infra.infrastructure import PIDInfrastructure
from httplib import HTTPConnection
import json
from dkrz.pid.model.pid import PID, PID_TYPE_BASE

INDEX_RESOURCE_LOCATION = 1
INDEX_PID_TYPE = 2


class IllegalHandleStructureError(Exception):
    pass


class HandleInfrastructure(PIDInfrastructure):
    """
    Specialization of the general PID infrastructure based on the Handle System.
    Connects to the Handle System via a RESTful interface.
    """ 
    
    _PID_TYPE_HANDLES = {PID_TYPE_BASE: "10876/__PID_TYPE/BASE"}

    def __init__(self, host, port, path):
        '''
        Constructor
        '''
        super(HandleInfrastructure, self).__init__()
        self.host = host
        self.port = port
        self.path = path
        if not self.path.endswith("/"):
            self.path = self.path + "/"
            
    @classmethod
    def determine_pid_type_handle(cls, pid_type):
        """
        Determines the Handle for the given PID type constant (which should be an int).
        @param pid_type: The pid_type constant value to convert. Constants are given in :module:pid.py.
        @return a valid Handle identifier representing the given type 
        """
        return cls._PID_TYPE_HANDLES[pid_type]
        
    def _acquire_pid(self, identifier):
        http = HTTPConnection(self.host, self.port)
        http.request("POST", self.path+identifier, None)
        resp = http.getresponse()
        if not(200 <= resp.status <= 299):
            raise IOError("Could not create Handle %s: %s" % (identifier, resp.reason))
        return identifier
        
    def _pid_from_json(self, piddata, identifier):
        # piddata is an array of dicts, where each dict has keys: index, type, data
        annotations = {}
        res_loc = None
        pid_type = self.determine_pid_type_handle(PID_TYPE_BASE)
        for ele in piddata:
            if ele["index"] == INDEX_RESOURCE_LOCATION:
                res_loc = ele["data"]
                continue
            if ele["index"] == INDEX_PID_TYPE:
                pid_type = ele["data"]
                continue
            if ele["type"] in annotations:
                # multiple data for one key.. allowed in Handles, but not in our PIDs. --> Construct a list.
                if isinstance(annotations[ele["type"]], list):
                    annotations[ele["type"]].append(ele["data"])
                else:
                    annotations[ele["type"]] = [annotations[ele["type"]], ele["data"]]
                continue
            # no special circumstances --> assign to annotations
            annotations[ele["type"]] = ele["data"]
        return PID(self, identifier, annotations, res_loc, pid_type)
        
    def lookup_pid(self, identifier):
        http = HTTPConnection(self.host, self.port)
        http.request("GET", self.path+self.identifier, None)
        resp = http.getresponse()
        if resp.status == 404:
            # Handle not found
            return None
        elif not(200 <= resp.status <= 299):
            raise IOError("Failed to look up Handle %s due to the following reason (HTTP Code %s): %s" % (identifier, resp.status, resp.reason))
        else:
            pid = self._pid_from_json(json.load(resp), identifier)
            return pid            
        
    def _write_annotation(self, identifier, key, value):
        http = HTTPConnection(self.host, self.port)
        # first, we need to determine the index to use by looking at the key
        http.request("GET", self.path+self.identifier)
        resp = http.getresponse()
        if not(200 <= resp.status <= 299):
            raise IOError("Unknown Handle: %s" % identifier)
        piddata = json.load(resp)
        matching_values = []
        free_index = 101
        for ele in piddata:
            if ele["type"] == key:
                matching_values.append(ele)
            if ele["index"] >= free_index:
                free_index = ele["index"]+1
        if len(matching_values) > 1:
            raise IllegalHandleStructureError("Handle %s contains more than one entry of type %s!" % (identifier, key))
        elif len(matching_values) == 1:
            index = matching_values[0]["index"]
        else:
            # key not present in Handle; must assign a new index
            index = free_index
        # now we can write the annotation
        data = json.dumps([{"index": index, "type": key, "data": value}])
        http.request("PUT", self.path+self.identifier, data)
        resp = http.getresponse()
        if not(200 <= resp.status <= 299):
            raise IOError("Could not write annotations to Handle %s: %s" % (identifier, resp.reason))
        
