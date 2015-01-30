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
from lapis.model.do import DigitalObject
from lapis.model.doset import DigitalObjectSet
from lapis.model.hashmap import HandleHashmapImpl
from lapis.model.dolist import DigitalObjectArray, DigitalObjectLinkedList
from base64 import b64encode
from urllib3 import HTTPSConnectionPool, disable_warnings
import logging

try:
    import json
except ImportError:
    import simplejson as json

logger = logging.getLogger(__name__)

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

class IllegalHandleStructureError(Exception):
    pass


class HandleInfrastructure(DOInfrastructure):
    """
    Specialization of the general Digital Object Infrastructure based on the Handle System.
    Connects to the Handle System via a RESTful interface.
    """ 
    
    
    def __init__(self, host, port, user, user_index, password, path, prefix = None, additional_identifier_element = None, unsafe_ssl=False):
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
        if unsafe_ssl:
            disable_warnings()
            self.connpool = HTTPSConnectionPool(host, port=port, assert_hostname=False, cert_reqs="CERT_NONE")
        else:
            self.connpool = HTTPSConnectionPool(host, port=port)
        self.user_handle = prefix+"/"+user
        self.user_index = user_index
        self.authstring = b64encode(user_index+"%3A"+prefix+"/"+user+":"+password)
        self.http_headers = {"Content-Type": "application/json", "Authorization": "Basic %s" % self.authstring}
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
    
    def __generate_admin_value(self):
        return {"index":100,"type":"HS_ADMIN","data":{"format":"admin","value":{"handle":self.user_handle,"index":self.user_index,"permissions":"011111110011"}}}
    
    def _acquire_pid(self, identifier):
        path, identifier_prep = self._prepare_identifier(identifier)
        # check for existing Handle
        resp = self.connpool.request("GET", path, None, self.http_headers)
        if (resp.status == 200):
            # Handle already exists
            raise PIDAlreadyExistsError("Handle already exists: %s" % identifier_prep)
        if (resp.status != 404):
            raise IOError("Failed to check for existing Handle %s (HTTP Code %s): %s" % (identifier_prep, resp.status, resp.reason))
        # Handle does not exist, so we can safely create it
        values = {"values": [self.__generate_admin_value()]}
        resp = self.connpool.urlopen("PUT", path, str(values), self.http_headers)
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
        res_type = None
        if not "values" in piddata:
            raise IOError("Illegal format of JSON response from Handle server: 'values' not found in JSON record!")
        for ele in piddata["values"]:
            idx = int(ele["index"])
            if idx == 2:
                res_type = ele["data"]["value"]
                continue
            if ele["type"] == "HS_ADMIN":
                # ignore HS_ADMIN values; these are taken care of by the REST service server-side
                continue
            # no special circumstances --> assign to annotations or references
            if REFERENCE_INDEX_END >= idx >= REFERENCE_INDEX_START:
                # reference; first, parse element data using json to a list
                list_data = json.loads(ele["data"]["value"])
                if not isinstance(list_data, list):
                    raise IOError("Illegal format of JSON response from Handle server: Cannot load reference list! Input: %s" % ele["data"])
                if ele["type"] not in references:
                    references[ele["type"]] = list_data
                else:
                    references[ele["type"]].extend(list_data)
                continue
        # create special instances for special resource types
        if res_type == DigitalObjectSet.RESOURCE_TYPE:
            return DigitalObjectSet(self, identifier, references=references, alias_identifiers=aliases)
        if res_type == DigitalObjectArray.RESOURCE_TYPE:
            return DigitalObjectArray(self, identifier, references=references, alias_identifiers=aliases)
        if res_type == DigitalObjectLinkedList.RESOURCE_TYPE:
            return DigitalObjectLinkedList(self, identifier, references=references, alias_identifiers=aliases)
        return DigitalObject(self, identifier, references, alias_identifiers=aliases)
        
    def lookup_pid(self, identifier):
        aliases = []
        while True:
            path, identifier = self._prepare_identifier(identifier)
            resp = self.connpool.request("GET", path, None, self.http_headers)
            if resp.status == 404:
                # Handle not found
                if len(aliases) > 0:
                    raise PIDAliasBrokenError("Alias %s does not exist. Already resolved aliases: %s" % (identifier, aliases))
                return None
            elif not(200 <= resp.status <= 299):
                raise IOError("Failed to look up Handle %s due to the following reason (HTTP Code %s): %s" % (identifier, resp.status, resp.reason))
            else:
                # check for HS_ALIAS redirect
                piddata = json.loads(resp.data)
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
        if not "values" in handledata:
            raise IOError("Illegal format of JSON response from Handle server: 'values' not found in JSON record!")
        for ele in handledata["values"]:
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
        data = json.dumps([{"index": index, "type": valuetype, "data": {"format": "string", "value": value}}])
        resp = self.connpool.urlopen("PUT", path+"?index=various", data, self.http_headers)
        if not(200 <= resp.status <= 299):
            raise IOError("Could not write raw value to Handle %s: %s" % (identifier, resp.reason))
    
    def _read_pid_value(self, identifier, index):
        """
        Reads a single indexed type and value from the Handle with given identifier.
        
        :returns: A tuple (type, value) or None if the given index is unassigned.
        :raises: :exc:`IOError` if no Handle with given identifier exists. 
        """
        path, identifier = self._prepare_identifier(str(identifier))
        if type(index) is not int:
            raise ValueError("Index must be an integer! (was: type %s, value %s)" % (type(index), index))
        # read only the given index
        resp = self.connpool.request("GET", path+"?index=%s" % index, "", self.http_headers)
        if resp.status == 404:
            # value not found; the Handle may exist, but the index is unused
            return None        
        if not(200 <= resp.status <= 299):
            raise IOError("Could not read raw value from Handle %s: %s" % (identifier, resp.reason))
        respdata = json.loads(resp.data)
        if not "values" in respdata:
            raise IOError("Illegal format of JSON response from Handle server: 'values' not found in JSON record!")
        for ele in respdata["values"]:
            if int(ele["index"]) == index:
                return (ele["type"], ele["data"]["value"])
        return None
        
    def _remove_pid_value(self, identifier, index):
        """
        Removes a single Handle value at Handle of given identifier at given index.
        
        :raises: :exc:`IOError` if no Handle with given identifier exists. 
        """
        path, identifier = self._prepare_identifier(str(identifier))
        if type(index) is not int:
            raise ValueError("Index must be an integer! (was: type %s, value %s)" % (type(index), index))
        # read only the given index
        resp = self.connpool.urlopen("DELETE", path+"?index=%s" % index, "", self.http_headers)
        if not(200 <= resp.status <= 299):
            raise IOError("Could not remove raw value from Handle %s: %s" % (identifier, resp.reason))

    def _read_all_pid_values(self, identifier):
        """
        Reads the full Handle record of given identifier.
        
        :return: a dict with indexes as keys and (type, value) tuples as values.
        """
        path, identifier = self._prepare_identifier(identifier)
        # read full record
        resp = self.connpool.request("GET", path, "", self.http_headers)
        if not(200 <= resp.status <= 299):
            raise IOError("Could not read raw values from Handle %s: %s" % (identifier, resp.reason))
        respdata = json.loads(resp.data)
        res = {}
        if not "values" in respdata:
            raise IOError("Illegal format of JSON response from Handle server: 'values' not found in JSON record!")
        for ele in respdata["values"]:
            res[int(ele["index"])] = (ele["type"], ele["data"]["value"])
        return res
    
    def _write_resource_information(self, identifier, resource_location, resource_type=None):
        path, identifier = self._prepare_identifier(identifier)
        handle_values = []
        if resource_location:
            handle_values = [{"index": INDEX_RESOURCE_LOCATION, "type": "URL", "data": {"format": "string", "value": resource_location}}]
        if resource_type:
            handle_values.append({"index": INDEX_RESOURCE_TYPE, "type": "", "data": {"format": "string", "value": resource_type}})
        data = json.dumps(handle_values)
        resp = self.connpool.urlopen("PUT", path, data, self.http_headers)
        if not(200 <= resp.status <= 299):
            raise IOError("Could not write resource location to Handle %s: %s" % (identifier, resp.reason))

    def delete_do(self, identifier):
        path, identifier = self._prepare_identifier(identifier)
        resp = self.connpool.urlopen("DELETE", path, headers=self.http_headers)
        if resp.status == 404:
            raise KeyError("Handle not found: %s" % identifier)
        if not(200 <= resp.status <= 299):
            raise IOError("Could not delete Handle %s: %s" % (identifier, resp.reason))

    def _write_reference(self, identifier, key, reference):
        path, identifier = self._prepare_identifier(identifier)
        # first, we need to determine the index to use by looking at the key
        resp = self.connpool.request("GET", path, headers=self.http_headers)
        if not(200 <= resp.status <= 299):
            raise IOError("Unknown Handle: %s" % identifier)
        dodata = json.loads(resp.data)
        index = self._determine_index(identifier, dodata, key, REFERENCE_INDEX_START, REFERENCE_INDEX_END)
        # now we can write the reference; note that reference may be a list. But this is okay, we
        # convert it to a string and take care of reconversion in the JSON-to-DO method
        reference_s = json.dumps(reference)
        data = json.dumps({"values": [{"index": index, "type": key, "data": {"format": "string", "value": reference_s}}]})
        resp = self.connpool.urlopen("PUT", path+"?index=various", data, self.http_headers)
        if not(200 <= resp.status <= 299):
            raise IOError("Could not write references to Handle %s: %s" % (identifier, resp.reason))
            
            
    def create_alias(self, original, alias_identifier):
        if isinstance(original, DigitalObject):
            original_identifier = original.identifier
        else: 
            original_identifier = str(original)
        path, identifier = self._prepare_identifier(alias_identifier)
        # check for existing Handle
        resp = self.connpool.request("GET", path, None, self.http_headers)
        if (resp.status == 200):
            # Handle already exists
            raise PIDAlreadyExistsError("Handle already exists, cannot use it as an alias: %s" % identifier)
        if (resp.status != 404):
            raise IOError("Failed to check for existing Handle %s (HTTP Code %s): %s" % (identifier, resp.status, resp.reason))
        # okay, alias is available. Now create it.
        values = {"values": [self.__generate_admin_value(), {"index": 1, "type": "HS_ALIAS", "data": {"format": "string", "value": str(original_identifier)}}]}
        resp = self.connpool.urlopen("PUT", path, str(values), self.http_headers)
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
        path, identifier = self._prepare_identifier(alias_identifier)
        resp = self.connpool.request("GET", path, None, self.http_headers)
        if resp.status == 404:
            raise KeyError("Handle not found: %s" % identifier)
        if not(200 <= resp.status <= 299):
            raise IOError("Failed to lookup Handle %s for alias check: %s" % (identifier, resp.reason))
        # parse JSON, but do not create a Digital Object instance, as this might cause inefficient subsequent calls
        isa, a_id = self._check_json_for_alias(json.loads(resp.data))
        return isa

    def _check_json_for_alias(self, piddata):
        """
        Checks the given JSON data structure for presence of an HS_ALIAS marker.
        
        :returns: a tuple (b, id) where b is True or False and if b is True, id is the Handle string of the target
          Handle.
        """
        res = (False, None)
        for ele in piddata["values"]:
            if ele["type"] == "HS_ALIAS":
                res = (True, ele["data"]["value"])
                break
        return res        

    def prefix_pid(self, suffix):
        """
        Prepends a given (incomplete) identifier with the current Handle prefix.
        """
        return self.prefix + "/" + suffix
    
    def manufacture_hashmap(self, identifier, characteristic_segment_number):
        """
        Factory method. Constructs Handle-based Hashmap implementation objects.
        
        :identifier: The PID of the record that should hold the hash map.
        :param: characteristic_segment_number: Since there can be multiple hash maps in a single record, this number
          is used to separate them from each other. 
        """
        return HandleHashmapImpl(self, identifier, characteristic_segment_number)
    

