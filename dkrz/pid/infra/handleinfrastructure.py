'''
Created on 03.05.2012

@author: tobiasweigel
'''
from dkrz.pid.infra.infrastructure import PIDInfrastructure, RESOURCE_LOCATION_TYPE_URL
from httplib import HTTPConnection
import json
from dkrz.pid.model.pid import PID, PID_TYPE_BASE

INDEX_RESOURCE_LOCATION = 1
INDEX_PID_TYPE = 2

"""
At which Handle value index do we begin with annotation information?
"""
FREE_INDEX_START = 1000

TYPE_PID_TYPE = "10876/__TYPES/PID_TYPE"

DEFAULT_JSON_HEADERS = {"Content-Type": "application/json"}

class IllegalHandleStructureError(Exception):
    pass


class HandleInfrastructure(PIDInfrastructure):
    """
    Specialization of the general PID infrastructure based on the Handle System.
    Connects to the Handle System via a RESTful interface.
    """ 
    
    
    def __init__(self, host, port, path, prefix = None, additional_identifier_element = None):
        '''
        Constructor.
        
        @param prefix: The Handle prefix to use (without trailing slash). If not given, all operations will work
          nonetheless, except for random handle creation. Note that setting a prefix does not mean that identifier 
          strings can omit it - all identifiers must ALWAYS include the prefix, no matter what.
        @param additional_identifier_element: A string that is inserted inbetween Handle prefix and suffix, e.g. if set
          to "test-", 10876/identifier becomes 10876/test-identifier.
        '''
        super(HandleInfrastructure, self).__init__()
        self.host = host
        self.port = port
        self.path = path
        self.prefix = prefix
        if not self.path.endswith("/"):
            self.path = self.path + "/"
        self.additional_identifier_element = additional_identifier_element
            
    
    def _generate_random_identifier(self):
        if not self.prefix:
            raise ValueError("Cannot generate random Handles if no prefix is provided!")
        rid = super(HandleInfrastructure, self)._generate_random_identifier()
        return self.prefix+"/"+rid

    def _prepare_identifier(self, identifier):
        if (self.additional_identifier_element):
            # split identifier into prefix and suffix, insert additional element inbetween 
            parts = identifier.split("/", 1)
            if len(parts) != 2:
                raise ValueError("Invalid identifier - no separating slash between prefix and suffix: %s" % identifier)
            if (parts[1].startswith(self.additional_identifier_element)):
                return self.path+identifier, identifier
            newident = parts[0]+"/"+self.additional_identifier_element+parts[1]
            return self.path+newident, newident
        else:
            return self.path+identifier, identifier
    
    
    def _acquire_pid(self, identifier):
        http = HTTPConnection(self.host, self.port)
        path, identifier = self._prepare_identifier(identifier)
        # check for existing Handle
        http.request("GET", path, None)
        resp = http.getresponse()
        if (resp.status == 200):
            # Handle already exists
            raise IOError("Handle already exists: %s" % identifier)
        if (resp.status != 404):
            raise IOError("Failed to check for existing Handle %s (HTTP Code %s): %s" % (identifier, resp.status, resp.reason))
        # Handle does not exist, so we can safely create it
        http = HTTPConnection(self.host, self.port)
        http.request("PUT", path, "[]", DEFAULT_JSON_HEADERS)
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
        path, identifier = self._prepare_identifier(identifier)
        http.request("GET", path, None)
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
        path, identifier = self._prepare_identifier(identifier)
        # first, we need to determine the index to use by looking at the key
        http.request("GET", path)
        resp = http.getresponse()
        if not(200 <= resp.status <= 299):
            raise IOError("Unknown Handle: %s" % identifier)
        piddata = json.load(resp)
        matching_values = []
        free_index = FREE_INDEX_START
        for ele in piddata:
            if ele["type"] == key:
                matching_values.append(ele)
            if ele["index"] >= free_index:
                free_index = int(ele["index"])+1
        if len(matching_values) > 1:
            raise IllegalHandleStructureError("Handle %s contains more than one entry of type %s!" % (identifier, key))
        elif len(matching_values) == 1:
            index = matching_values[0]["index"]
        else:
            # key not present in Handle; must assign a new index
            index = free_index
        # now we can write the annotation
        http = HTTPConnection(self.host, self.port)
        data = json.dumps([{"index": index, "type": key, "data": value}])
        http.request("POST", path, data, DEFAULT_JSON_HEADERS)
        resp = http.getresponse()
        if not(200 <= resp.status <= 299):
            raise IOError("Could not write annotations to Handle %s: %s" % (identifier, resp.reason))
        
    def _write_all_annotations(self, identifier, annotations):
        http = HTTPConnection(self.host, self.port)
        path, identifier = self._prepare_identifier(identifier)
        # must retrieve current Handle data to maintain the resource location and pid type
        http.request("GET", path)
        resp = http.getresponse()
        if not(200 <= resp.status <= 299):
            raise IOError("Unknown Handle: %s" % identifier)
        piddata = json.load(resp)
        pid_type = PID_TYPE_BASE
        resource_location = ""
        for ele in piddata:
            if ele["index"] == INDEX_PID_TYPE:
                pid_type = ele["data"]
            elif ele["index"] == INDEX_RESOURCE_LOCATION:
                resource_location = ele["data"]
        # convert annotations to Handle values
        handle_values = [{"index": INDEX_PID_TYPE, "type": TYPE_PID_TYPE, "data": pid_type},
                           {"index": INDEX_RESOURCE_LOCATION, "type": "", "data": resource_location}]
        current_index = FREE_INDEX_START
        for k, v in annotations.iter_items():
            handle_values.append({"index": current_index, "type": k, "data": v})
            current_index += 1
        # now store new Handle values, replacing ALL old ones
        http = HTTPConnection(self.host, self.port)
        data = json.dumps(handle_values)
        http.request("PUT", path, data, DEFAULT_JSON_HEADERS)
        resp = http.getresponse()
        if not(200 <= resp.status <= 299):
            raise IOError("Could not write annotations to Handle %s: %s" % (identifier, resp.reason))

    def _write_resource_location(self, identifier, resource_location, resource_location_type=RESOURCE_LOCATION_TYPE_URL):
        http = HTTPConnection(self.host, self.port)
        path, identifier = self._prepare_identifier(identifier)
        handle_values = [{"index": INDEX_RESOURCE_LOCATION, "type": resource_location_type, "data": resource_location}]
        data = json.dumps(handle_values)
        http.request("POST", path, data, DEFAULT_JSON_HEADERS)
        resp = http.getresponse()
        if not(200 <= resp.status <= 299):
            raise IOError("Could not write resource location to Handle %s: %s" % (identifier, resp.reason))

    def delete_pid(self, identifier):
        http = HTTPConnection(self.host, self.port)
        path, identifier = self._prepare_identifier(identifier)
        http.request("DELETE", path)
        resp = http.getresponse()
        if not(200 <= resp.status <= 299):
            raise IOError("Could not delete Handle %s: %s" % (identifier, resp.reason))
