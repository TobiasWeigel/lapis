'''
Created on 03.05.2012

:author: tobiasweigel
'''
from dkrz.digitalobjects.infra.infrastructure import DOInfrastructure, PIDAlreadyExistsError
from httplib import HTTPConnection
import json
from dkrz.digitalobjects.model.do import DigitalObject

INDEX_RESOURCE_LOCATION = 1
INDEX_RESOURCE_TYPE = 2

"""
At which Handle value index do we begin with reference information?
"""
REFERENCE_INDEX_START = 1000

"""
The highest Handle value index for reference information
"""
REFERENCE_INDEX_END = 1999

"""
At which Handle value index do we begin with annotation information?
"""
ANNOTATION_INDEX_START = 2000

TYPE_RESOURCE_TYPE = "10876/__TYPES/RESOURCE_TYPE"

DEFAULT_JSON_HEADERS = {"Content-Type": "application/json"}

class IllegalHandleStructureError(Exception):
    pass


class HandleInfrastructure(DOInfrastructure):
    """
    Specialization of the general Digital Object Infrastructure based on the Handle System.
    Connects to the Handle System via a RESTful interface.
    """ 
    
    
    def __init__(self, host, port, path, prefix = None, additional_identifier_element = None):
        '''
        Constructor.
        
        :param prefix: The Handle prefix to use (without trailing slash). If not given, all operations will work
          nonetheless, except for random handle creation. Note that setting a prefix does not mean that identifier 
          strings can omit it - all identifiers must ALWAYS include the prefix, no matter what.
        :param additional_identifier_element: A string that is inserted inbetween Handle prefix and suffix, e.g. if set
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
        path, identifier_prep = self._prepare_identifier(identifier)
        # check for existing Handle
        http.request("GET", path, None)
        resp = http.getresponse()
        if (resp.status == 200):
            # Handle already exists
            raise PIDAlreadyExistsError("Handle already exists: %s" % identifier_prep)
        if (resp.status != 404):
            raise IOError("Failed to check for existing Handle %s (HTTP Code %s): %s" % (identifier_prep, resp.status, resp.reason))
        # Handle does not exist, so we can safely create it
        http = HTTPConnection(self.host, self.port)
        http.request("PUT", path, "[]", DEFAULT_JSON_HEADERS)
        resp = http.getresponse()
        if not(200 <= resp.status <= 299):
            raise IOError("Could not create Handle %s: %s" % (identifier_prep, resp.reason))
        return identifier_prep
    
    def _do_from_json(self, piddata, identifier):
        # piddata is an array of dicts, where each dict has keys: index, type, data
        annotations = {}
        references = {}
        res_loc = None
        res_type = None
        for ele in piddata:
            idx = int(ele["index"])
            if idx == INDEX_RESOURCE_LOCATION:
                res_loc = ele["data"]
                continue
            if idx == INDEX_RESOURCE_TYPE:
                res_type = ele["data"]
                continue
            if ele["type"] == "HS_ADMIN":
                # ignore HS_ADMIN values; these are taken care of by the REST service server-side
                continue
            if ele["type"] in annotations and idx >= ANNOTATION_INDEX_START:
                # multiple data for one key.. allowed in Handles, but not in our PIDs. --> Construct a list.
                if isinstance(annotations[ele["type"]], list):
                    annotations[ele["type"]].append(ele["data"])
                else:
                    annotations[ele["type"]] = [annotations[ele["type"]], ele["data"]]
                continue
            # no special circumstances --> assign to annotations or references
            if REFERENCE_INDEX_END >= idx >= REFERENCE_INDEX_START:
                # reference; first, parse element data using json to a list
                list_data = json.loads(ele["data"])
                if not isinstance(list_data, list):
                    raise IOError("Illegal format of JSON response from Handle services: Cannot load reference list! Input: %s" % ele["data"])
                if ele["type"] not in references:
                    references[ele["type"]] = list_data
                else:
                    references[ele["type"]].extend(list_data)
                continue
            annotations[ele["type"]] = ele["data"]
        return DigitalObject(self, identifier, annotations, res_loc, res_type, references)
        
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
            dobj = self._do_from_json(json.load(resp), identifier)
            return dobj            
        
    def _determine_index(self, identifier, handledata, key, index_start, index_end=None):
        """
        Finds an index in the Handle key-metadata record to store a value for the given key. If the key is already
        present, its index will be reused. If it is not present, a free index will be determined. 
        
        :param identifier: The current Handle.
        :param key: The key that will be assigned.
        :param index_start: At which index the search should start.
        :param index_end: Where should the search end? Use None to search all indices greater than the start index.
        :raises: :exc:`IndexError` if all possible indices are already taken by other keys.
        :returns: an index value. 
        """
        matching_values = []
        free_index = index_start
        taken_indices = []        
        for ele in handledata:
            idx = int(ele["index"])
            if (index_end and (index_start <= idx <= index_end))\
            or (not index_end and (index_start <= idx)):
                taken_indices.append(idx)
            if ele["type"] == key:
                matching_values.append(ele)
        if len(matching_values) > 1:
            raise IllegalHandleStructureError("Handle %s contains more than one entry of type %s!" % (identifier, key))
        elif len(matching_values) == 1:
            return int(matching_values[0]["index"])
        else:
            # key not present in Handle; must assign a new index
            # check for free index within bounds
            if taken_indices == []:
                return index_start
            m = min(taken_indices)
            if m == index_end:
                raise IllegalHandleStructureError("Handle %s does not have any more available index slots between %s and %s!" % (index_start, index_end))
            return m
        
        
    def _write_annotation(self, identifier, key, value):
        http = HTTPConnection(self.host, self.port)
        path, identifier = self._prepare_identifier(identifier)
        # first, we need to determine the index to use by looking at the key
        http.request("GET", path)
        resp = http.getresponse()
        if not(200 <= resp.status <= 299):
            raise IOError("Unknown Handle: %s" % identifier)
        dodata = json.load(resp)
        index = self._determine_index(identifier, dodata, key, ANNOTATION_INDEX_START)
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
        # must retrieve current Handle data to maintain the resource location and resource type
        http.request("GET", path)
        resp = http.getresponse()
        if not(200 <= resp.status <= 299):
            raise IOError("Unknown Handle: %s" % identifier)
        piddata = json.load(resp)
        res_type = None
        resource_location = ""
        for ele in piddata:
            if ele["index"] == INDEX_RESOURCE_TYPE:
                res_type = ele["data"]
            elif ele["index"] == INDEX_RESOURCE_LOCATION:
                resource_location = ele["data"]
        # convert annotations to Handle values
        handle_values = [{"index": INDEX_RESOURCE_TYPE, "type": TYPE_RESOURCE_TYPE, "data": res_type},
                           {"index": INDEX_RESOURCE_LOCATION, "type": "", "data": resource_location}]
        current_index = ANNOTATION_INDEX_START
        for k, v in annotations.iteritems():
            handle_values.append({"index": current_index, "type": k, "data": v})
            current_index += 1
        # now store new Handle values, replacing ALL old ones
        http = HTTPConnection(self.host, self.port)
        data = json.dumps(handle_values)
        http.request("PUT", path, data, DEFAULT_JSON_HEADERS)
        resp = http.getresponse()
        if not(200 <= resp.status <= 299):
            raise IOError("Could not write annotations to Handle %s: %s" % (identifier, resp.reason))

    def _write_resource_location(self, identifier, resource_location, resource_type=None):
        http = HTTPConnection(self.host, self.port)
        path, identifier = self._prepare_identifier(identifier)
        handle_values = [{"index": INDEX_RESOURCE_LOCATION, "type": "URL", "data": resource_location}]
        if resource_type:
            handle_values.append({"index": INDEX_RESOURCE_TYPE, "type": "", "data": resource_type})
        data = json.dumps(handle_values)
        http.request("POST", path, data, DEFAULT_JSON_HEADERS)
        resp = http.getresponse()
        if not(200 <= resp.status <= 299):
            raise IOError("Could not write resource location to Handle %s: %s" % (identifier, resp.reason))

    def delete_do(self, identifier):
        http = HTTPConnection(self.host, self.port)
        path, identifier = self._prepare_identifier(identifier)
        http.request("DELETE", path)
        resp = http.getresponse()
        if not(200 <= resp.status <= 299):
            raise IOError("Could not delete Handle %s: %s" % (identifier, resp.reason))

    def _write_reference(self, identifier, key, reference):
        http = HTTPConnection(self.host, self.port)
        path, identifier = self._prepare_identifier(identifier)
        # first, we need to determine the index to use by looking at the key
        http.request("GET", path)
        resp = http.getresponse()
        if not(200 <= resp.status <= 299):
            raise IOError("Unknown Handle: %s" % identifier)
        dodata = json.load(resp)
        index = self._determine_index(identifier, dodata, key, REFERENCE_INDEX_START, REFERENCE_INDEX_END)
        # now we can write the reference; note that reference may be a list. But this is okay, we
        # convert it to a string and take care of reconversion in the JSON-to-DO method
        http = HTTPConnection(self.host, self.port)
        reference_s = json.dumps(reference)
        data = json.dumps([{"index": index, "type": key, "data": reference_s}])
        http.request("POST", path, data, DEFAULT_JSON_HEADERS)
        resp = http.getresponse()
        if not(200 <= resp.status <= 299):
            raise IOError("Could not write references to Handle %s: %s" % (identifier, resp.reason))
            