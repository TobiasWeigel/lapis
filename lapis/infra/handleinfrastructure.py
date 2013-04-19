'''
Created on 03.05.2012

:author: tobiasweigel

Copyright (c) 2012, Tobias Weigel, Deutsches Klimarechenzentrum GmbH
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met: 

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer. 
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution. 

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those
of the authors.
'''
from lapis.infra.infrastructure import DOInfrastructure, PIDAlreadyExistsError, PIDAliasBrokenError
from httplib import HTTPConnection
from lapis.model.do import DigitalObject
from lapis.model.doset import DigitalObjectSet
from lapis.model.hashmap import HandleHashmapImpl

try:
    import json
except ImportError:
    import simplejson as json

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
        # check identifier string for validity
        if " " in identifier:
            raise ValueError("Illegal Handle identifier string character; spaces are not supported! (identifier: %s)" % identifier)
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
    
    def _do_from_json(self, piddata, identifier, aliases):
        """
        Construct a DO instance from given JSON data.
        
        :param piddata: JSON loaded data.
        :param identifier: Identifier of the DO.
        :param aliases: A list of aliases that were used to get to this identifier (may be empty). The list must be
          ordered in the order of alias resolution, i.e. aliases[0] pointed to aliases[1] etc. The last entry pointed 
          to the actual identifier. 
        :returns: A fully fledged DigitalObject instance
        """
        # piddata is an array of dicts, where each dict has keys: index, type, data
        references = {}
        for ele in piddata:
            idx = int(ele["idx"])
            if idx == 2:
                res_type = ele["data"]
                continue
            if ele["type"] == "HS_ADMIN":
                # ignore HS_ADMIN values; these are taken care of by the REST service server-side
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
        # create special instances for special resource types
        if res_type == DigitalObjectSet.RESOURCE_TYPE:
            return DigitalObjectSet(self, identifier, references=references, alias_identifiers=aliases)
        return DigitalObject(self, identifier, references, alias_identifiers=aliases)
        
    def lookup_pid(self, identifier):
        aliases = []
        while True:
            http = HTTPConnection(self.host, self.port)
            path, identifier = self._prepare_identifier(identifier)
            http.request("GET", path, None)
            resp = http.getresponse()
            if resp.status == 404:
                # Handle not found
                if len(aliases) > 0:
                    raise PIDAliasBrokenError("Alias %s does not exist. Already resolved aliases: %s" % (identifier, aliases))
                return None
            elif not(200 <= resp.status <= 299):
                raise IOError("Failed to look up Handle %s due to the following reason (HTTP Code %s): %s" % (identifier, resp.status, resp.reason))
            else:
                # check for HS_ALIAS redirect
                piddata = json.load(resp)
                isa, alias_id = self._check_json_for_alias(piddata)
                if isa:
                    # write down alias identifier and redo lookup with target identifier
                    aliases.append(identifier)
                    identifier = alias_id
                    continue                    
                dobj = self._do_from_json(piddata, identifier, aliases)
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
            idx = int(ele["idx"])
            if (index_end and (index_start <= idx <= index_end))\
            or (not index_end and (index_start <= idx)):
                taken_indices.append(idx)
            if ele["type"] == key:
                matching_values.append(ele)
        if len(matching_values) > 1:
            raise IllegalHandleStructureError("Handle %s contains more than one entry of type %s!" % (identifier, key))
        elif len(matching_values) == 1:
            return int(matching_values[0]["idx"])
        else:
            # key not present in Handle; must assign a new index
            # check for free index within bounds
            if taken_indices == []:
                return index_start
            m = min(taken_indices)
            if m == index_end:
                raise IllegalHandleStructureError("Handle %s does not have any more available index slots between %s and %s!" % (index_start, index_end))
            return m
        
    def _write_pid_value(self, identifier, index, valuetype, value):
        """
        Writes a single (index, type, value) to the Handle with given identifier.
        
        :param identifier: The Handle identifier.
        :param index: Index (positive 32 bit int).
        :param valuetype: Type (arbitrary)
        :param value: Value (arbitrary)
        """
        path, identifier = self._prepare_identifier(identifier)
        if type(index) is not int:
            raise ValueError("Index must be an integer! (was: type %s, value %s)" % (type(index), index))
        # write the raw (index, type, value) triple
        http = HTTPConnection(self.host, self.port)
        data = json.dumps([{"idx": index, "type": valuetype, "data": value}])
        http.request("POST", path, data, DEFAULT_JSON_HEADERS)
        resp = http.getresponse()
        if not(200 <= resp.status <= 299):
            raise IOError("Could not write raw value to Handle %s: %s" % (identifier, resp.reason))
    
    def _read_pid_value(self, identifier, index):
        """
        Reads a single indexed type and value from the Handle with given identifier.
        
        :returns: A tuple (type, value) or None if the given index is unassigned.
        :raises: :exc:`IOError` if no Handle with given identifier exists. 
        """
        path, identifier = self._prepare_identifier(index+":"+identifier)
        if type(index) is not int:
            raise ValueError("Index must be an integer! (was: type %s, value %s)" % (type(index), index))
        # read only the given index
        http = HTTPConnection(self.host, self.port)
        http.request("GET", path, "", DEFAULT_JSON_HEADERS)
        resp = http.getresponse()
        if not(200 <= resp.status <= 299):
            raise IOError("Could not read raw value from Handle %s: %s" % (identifier, resp.reason))
        respdata = json.load(resp)
        for ele in respdata:
            if int(ele["idx"]) == index:
                return ele["data"]
        return None
        
    def _remove_pid_value(self, identifier, index):
        """
        Removes a single Handle value at Handle of given identifier at given index.
        
        :raises: :exc:`IOError` if no Handle with given identifier exists. 
        """
        self.write_handle_value(identifier, index, None, None)

    def _read_all_pid_values(self, identifier):
        """
        Reads the full Handle record of given identifier.
        
        :return: a dict with indexes as keys and (type, value) tuples as values.
        """
        path, identifier = self._prepare_identifier(identifier)
        # read full record
        http = HTTPConnection(self.host, self.port)
        http.request("GET", path, "", DEFAULT_JSON_HEADERS)
        resp = http.getresponse()
        if not(200 <= resp.status <= 299):
            raise IOError("Could not read raw values from Handle %s: %s" % (identifier, resp.reason))
        respdata = json.load(resp)
        res = {}
        for ele in respdata:
            res[int(ele["idx"])] = (ele["type"], ele["data"])
        return res
    
    def _write_resource_information(self, identifier, resource_location, resource_type=None):
        http = HTTPConnection(self.host, self.port)
        path, identifier = self._prepare_identifier(identifier)
        handle_values = []
        if resource_location:
            handle_values = [{"idx": INDEX_RESOURCE_LOCATION, "type": "URL", "data": resource_location}]
        if resource_type:
            handle_values.append({"idx": INDEX_RESOURCE_TYPE, "type": "", "data": resource_type})
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
        if resp.status == 404:
            raise KeyError("Handle not found: %s" % identifier)
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
        data = json.dumps([{"idx": index, "type": key, "data": reference_s}])
        http.request("POST", path, data, DEFAULT_JSON_HEADERS)
        resp = http.getresponse()
        if not(200 <= resp.status <= 299):
            raise IOError("Could not write references to Handle %s: %s" % (identifier, resp.reason))
            
            
    def create_alias(self, original, alias_identifier):
        if isinstance(original, DigitalObject):
            original_identifier = original.identifier
        else: 
            original_identifier = str(original)
        http = HTTPConnection(self.host, self.port)
        path, identifier = self._prepare_identifier(alias_identifier)
        # check for existing Handle
        http.request("GET", path, None)
        resp = http.getresponse()
        if (resp.status == 200):
            # Handle already exists
            raise PIDAlreadyExistsError("Handle already exists, cannot use it as an alias: %s" % identifier)
        if (resp.status != 404):
            raise IOError("Failed to check for existing Handle %s (HTTP Code %s): %s" % (identifier, resp.status, resp.reason))
        # okay, alias is available. Now create it.
        http = HTTPConnection(self.host, self.port)
        http.request("PUT", path, '[{"idx": 1, "type": "HS_ALIAS", "data": "%s"}]' % original_identifier, DEFAULT_JSON_HEADERS)
        resp = http.getresponse()
        if not(200 <= resp.status <= 299):
            raise IOError("Could not create Alias Handle %s: %s" % (identifier, resp.reason))
        return identifier
    
    def delete_alias(self, alias_identifier):
        # resolve to check if this is really an alias
        isa = self.is_alias(alias_identifier)
        if not isa:
            return False
        self.delete_do(alias_identifier)
        return True
    
    def is_alias(self, alias_identifier):
        http = HTTPConnection(self.host, self.port)
        path, identifier = self._prepare_identifier(alias_identifier)
        http.request("GET", path, None)
        resp = http.getresponse()
        if resp.status == 404:
            raise KeyError("Handle not found: %s" % identifier)
        if not(200 <= resp.status <= 299):
            raise IOError("Failed to lookup Handle %s for alias check: %s" % (identifier, resp.reason))
        # parse JSON, but do not create a Digital Object instance, as this might cause inefficient subsequent calls
        isa, a_id = self._check_json_for_alias(json.load(resp))
        return isa

    def _check_json_for_alias(self, piddata):
        """
        Checks the given JSON data structure for presence of an HS_ALIAS marker.
        
        :returns: a tuple (b, id) where b is True or False and if b is True, id is the Handle string of the target
          Handle.
        """
        res = (False, None)
        for ele in piddata:
            if ele["type"] == "HS_ALIAS":
                res = (True, ele["data"])
                break
        return res        

    def prefix_pid(self, suffix):
        """
        Prepends a given (incomplete) identifier with the current Handle prefix.
        """
        return self.prefix + "/" + suffix
    
    def manufacture_hashmap(self, identifier):
        """
        Factory method. Constructs Handle-based Hashmap implementation objects.
        """
        return HandleHashmapImpl(self, identifier)