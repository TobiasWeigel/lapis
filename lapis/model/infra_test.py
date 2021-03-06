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
import unittest
from lapis.infra.infrastructure import InMemoryInfrastructure, PIDAlreadyExistsError, PIDAliasBrokenError

from random import Random

import logging
import os
from lapis.infra.handleinfrastructure import HandleInfrastructure

from lapis.model.do import DigitalObject, PropertyNameMismatchError

from ConfigParser import ConfigParser
from lapis.model.doset import DigitalObjectSet
from lapis.model.dolist import DigitalObjectArray, DigitalObjectLinkedList
from lapis.model.hashmap import BASE_INDEX_HASHMAP_SIZE

TESTING_CONFIG_DEFAULTS = { "handle-prefix": "10876.test", "server-address": "handle8.dkrz.de", "server-port": 443 }

logger = logging.getLogger(__name__)

class TestDOInfrastructure(unittest.TestCase):
    
    def setUp(self):
        self.do_infra = InMemoryInfrastructure()
        self.do_infra.set_random_seed(12345)
        self.logger = logging.getLogger(__name__)
        self.random = Random(43210)
        self.created_pids = []
        self.prefix = TESTING_CONFIG_DEFAULTS["handle-prefix"]+"/"
        
    def tearDown(self):
        pass
    
    def __check_dobj3_references(self, dobj3, dobj1, dobj2):
        i = 0
        iter3 = dobj3.iter_reference_keys()
        for k in iter3:
            assert k == "successor"
            i += 1
        assert i == 1
        assert dobj3.get_references("notexisting") == []
        succ = dobj3.get_references("successor")
        assert len(succ) == 2
        assert succ[0].identifier == dobj1.identifier
        assert succ[1].identifier == dobj2.identifier

    
    def test_do_values(self):
        # values
        pid = self.prefix+"test_do_values"
        resloc = "http://www.example.com/1"
        restype = "MY_TEST_TYPE"
        pid2 = self.prefix+"test_do_values_2"
        pid3 = self.prefix+"test_do_values_3"
        # create DO
        dobj = self.do_infra.create_do(pid)
        self.created_pids.append(pid)
        assert dobj != None
        dobj.resource_location = resloc
        assert dobj.resource_location == resloc
        dobj._resource_type = restype
        assert dobj._resource_type == restype
        # look up and assert
        dobj2 = self.do_infra.lookup_pid(pid)
        assert dobj2 != None
        assert dobj2.resource_location == resloc
        assert dobj2._resource_type == restype
        # create a second DO
        dobj2 = self.do_infra.create_do(pid2)
        self.created_pids.append(pid2)
        assert dobj2 != None
        # create a third DO
        dobj3 = self.do_infra.create_do(pid3)
        self.created_pids.append(pid3)
        assert dobj3 != None
        dobj3.add_do_reference("successor", dobj)
        dobj3.add_do_reference("successor", dobj2)
        dobj2.add_do_reference("predecessor", dobj3)
        dobj.add_do_reference("predecessor", dobj3)
        dobj.set_property_value(20, "myproperty20", 1)
        dobj.set_property_value(21, "myproperty21", "abc")
        # check references
        self.__check_dobj3_references(dobj3, dobj, dobj2)
        # retrieve dobj3 from infra and check references
        dobj3 = self.do_infra.lookup_pid(pid3)
        self.__check_dobj3_references(dobj3, dobj, dobj2)
        # check properties
        dobj = self.do_infra.lookup_pid(pid)
        assert dobj.is_property_assigned(20) == True
        assert dobj.is_property_assigned(21) == True
        assert dobj.is_property_assigned(22) == False
        assert dobj.get_property_value(20) == ("myproperty20", "1")
        assert dobj.get_property_value(21) == ("myproperty21", "abc")
        dobj.set_property_value(20, "myproperty20", "2")
        assert dobj.get_property_value(20) == ("myproperty20", "2")
        dobj = self.do_infra.lookup_pid(pid)
        assert dobj.get_property_value(20) == ("myproperty20", "2")
        # test prevention of property overwrite
        try:
            dobj.set_property_value(20, "this_should_not_work", "value")
            self.fail("Successful overwrite of existing property with different name!")
        except PropertyNameMismatchError:
            pass
        else:
            raise
        # delete and check for removal
        self.do_infra.delete_do(pid)
        dobj = self.do_infra.lookup_pid(pid)
        assert dobj == None
        
    def test_infra_operations(self):
        dobj = self.do_infra.lookup_pid(self.prefix+"does-not-exist")
        assert dobj == None
        # duplication attempts
        dobj = self.do_infra.create_do(self.prefix+"duplicate")
        self.created_pids.append(self.prefix+"duplicate")
        assert dobj != None
        try:
            dobj2 = self.do_infra.create_do(self.prefix+"duplicate")
            self.fail("Creation attempt of object with duplicate PID successful!")
        except PIDAlreadyExistsError:
            pass
        else:
            self.fail("Creation attempt of object with duplicate PID successful/compromised!")
            
    def test_random_pid_allocation(self):
        for x in range (0,10):
            dobj = self.do_infra.create_do()
            self.created_pids.append(dobj.identifier)
            assert dobj != None
            self.logger.info(dobj.identifier)
    
    def test_aliases(self):
        resloc = "http://www.example.com/alias_original"
        id_orig = self.prefix+"alias_original"
        id_alias1 = self.prefix+"alias1"
        id_alias2 = self.prefix+"alias2"
        dobj1 = self.do_infra.create_do(id_orig)
        id_orig = dobj1.identifier
        self.created_pids.append(id_orig)
        assert dobj1 != None
        dobj1.resource_location = resloc
        assert dobj1.resource_location == resloc
        assert dobj1.get_alias_identifiers() == []
        # alias 1 -> orig
        id_alias1 = self.do_infra.create_alias(dobj1, id_alias1)
        assert id_alias1 != None
        self.created_pids.append(id_alias1)
        assert self.do_infra.is_alias(id_alias1) == True
        # alias 2 -> alias 1 -> orig
        id_alias2 = self.do_infra.create_alias(id_alias1, id_alias2)
        assert id_alias2 != None
        self.created_pids.append(id_alias2)
        assert self.do_infra.is_alias(id_alias2) == True
        # check aliases
        assert self.do_infra.is_alias(id_orig) == False
        dobj = self.do_infra.lookup_pid(id_alias2)
        assert dobj != None
        assert dobj.identifier == id_orig
        assert dobj.resource_location == resloc
        assert dobj.get_alias_identifiers() == [id_alias2, id_alias1]
        dobj = self.do_infra.lookup_pid(id_alias1)
        assert dobj != None
        assert dobj.identifier == id_orig
        assert dobj.resource_location == resloc
        assert dobj.get_alias_identifiers() == [id_alias1]
        # look up directly, check if no aliases noted
        dobj = self.do_infra.lookup_pid(id_orig)
        assert dobj.get_alias_identifiers() == []
        
        # delete alias
        assert self.do_infra.delete_alias(id_alias1) == True
        assert self.do_infra.lookup_pid(id_alias1) == None
        
        # self.do_infra.lookup_pid(id_alias2) -> broken chain, check for exception
        try:
            self.do_infra.lookup_pid(id_alias2)
            self.fail("Could resolve broken alias chain without Exception being thrown!")
        except PIDAliasBrokenError:
            pass
        else:
            raise
        
    def test_sets(self):
        # create a set
        id_ele = [self.prefix+"setele1", self.prefix+"setele2", self.prefix+"setele3"]
        id_set = self.prefix+"set"
        non_ele_id = self.prefix+"some-non-ele"
        ele = []
        for i in range(len(id_ele)):
            newele = self.do_infra.create_do(id_ele[i])
            ele.append(newele)
            id_ele[i] = newele.identifier
            self.created_pids.append(newele.identifier)
        ele_set = self.do_infra.create_do(id_set, DigitalObjectSet)
        assert ele_set != None
        self.created_pids.append(ele_set.identifier)
        id_set = ele_set.identifier
        for e in ele:
            ele_set.add_do(e)
        # check if this is a set
        ele_set = self.do_infra.lookup_pid(id_set)
        assert isinstance(ele_set, DigitalObjectSet)
        # check if all subelements are present
        num_subele = 0
        for sele in ele_set.iter_set_elements():
            id_ele.index(sele.identifier)
            num_subele += 1
        assert num_subele == 3
        assert ele_set.num_set_elements() == 3
        # now extend and check again
        ele_set = self.do_infra.lookup_pid(id_set)
        id_ele += [self.prefix+"setele4"]
        newele = self.do_infra.create_do(id_ele[3])
        id_ele[3] = newele.identifier
        self.created_pids.append(newele.identifier)
        ele_set.add_do(newele)
        # check if all subelements are present
        ele_set = self.do_infra.lookup_pid(id_set)
        num_subele = 0
        for sele in ele_set.iter_set_elements():
            id_ele.index(sele.identifier)
            num_subele += 1
            assert sele.get_parent_pids(ele_set.CHARACTERISTIC_SEGMENT_NUMBER) == set([id_set])
        assert num_subele == 4
        assert ele_set.num_set_elements() == 4        
        # containment checks
        non_ele = self.do_infra.create_do(non_ele_id)
        self.created_pids.append(non_ele.identifier)
        ele_set = self.do_infra.lookup_pid(id_set)
        for e in id_ele:
            assert ele_set.contains_do(self.do_infra.lookup_pid(e))
        assert ele_set.contains_do(self.do_infra.lookup_pid(non_ele_id)) == False
        # test 'delete from set'-operation
        ele_set.remove_do(self.do_infra.lookup_pid(id_ele[0]))
        num_subele = 0
        for sele in ele_set.iter_set_elements():
            id_ele.index(sele.identifier)
            num_subele += 1
        assert num_subele == 3
        assert len(self.do_infra.lookup_pid(id_ele[0]).get_parent_pids(ele_set.CHARACTERISTIC_SEGMENT_NUMBER)) == 0
        assert ele_set.num_set_elements() == 3
        # test prevention of property overwrite
        try:
            ele_set.set_property_value(BASE_INDEX_HASHMAP_SIZE + ele_set.CHARACTERISTIC_SEGMENT_NUMBER, "this_should_not_work", "value")
            self.fail("Successful overwrite of hashmap size through a property!")
        except PropertyNameMismatchError:
            pass
        else:
            raise
        
        
    def test_lists(self):
        id_listele = [self.prefix+"listele1", self.prefix+"listele2", self.prefix+"listele3"]
        listele = []
        # create elements
        for i in range(len(id_listele)):
            newele = self.do_infra.create_do(id_listele[i])
            listele.append(newele)
            id_listele[i] = newele.identifier
            self.created_pids.append(newele.identifier)
        # test array
        id_array = self.prefix+"array"
        do_array = self.do_infra.create_do(id_array, DigitalObjectArray)
        self.created_pids.append(do_array.identifier)
        self.list_basic(do_array, id_listele, listele)
        # test linked list
        id_llist = self.prefix+"linkedlist"
        do_llist = self.do_infra.create_do(id_llist, DigitalObjectLinkedList)
        self.created_pids.append(do_llist.identifier)
        self.list_basic(do_llist, id_listele, listele)
        self.list_linked(do_llist, id_listele, listele)
        
    def list_basic(self, do_list, id_listele, listele):
        assert do_list != None
        # add array elements
        for e in listele:
            do_list.append_do(e)
        # re-load array
        do_list = self.do_infra.lookup_pid(do_list.identifier)
        assert do_list is not None
        assert do_list.num_elements() == len(listele)
        # verify array elements
        for i in range(len(listele)):
            assert do_list.contains(id_listele[i])
            dobj = do_list.get_do(i)
            assert dobj.identifier == id_listele[i]
        # check index function
        for i in range(len(id_listele)):
            dobj = self.do_infra.lookup_pid(id_listele[i])
            assert do_list.index_of(dobj) == i
        # remove middle element
        do_list.remove_do(1)
        assert do_list.num_elements() == 2
        assert do_list.get_do(0).identifier == id_listele[0]
        assert do_list.get_do(1).identifier == id_listele[2]
        assert do_list.contains(id_listele[1]) == False
        # re-insert at beginning
        do_list.insert_do(listele[1], 0)
        assert do_list.num_elements() == 3
        assert do_list.get_do(0).identifier == id_listele[1]
        assert do_list.get_do(1).identifier == id_listele[0]
        assert do_list.get_do(2).identifier == id_listele[2]
        # insert same element twice
        do_list.insert_do(listele[0], 0)
        do_list.insert_do(listele[0], 3)
        assert do_list.num_elements() == 5
        assert do_list.get_do(0).identifier == id_listele[0]
        assert do_list.get_do(1).identifier == id_listele[1]
        assert do_list.get_do(2).identifier == id_listele[0]
        assert do_list.get_do(3).identifier == id_listele[0]
        assert do_list.get_do(4).identifier == id_listele[2]
        # check parents
        for i in range(len(listele)):
            assert listele[i].get_parent_pids(do_list.CHARACTERISTIC_SEGMENT_NUMBER) == set([do_list.identifier]) 
        # remove all elements
        while do_list.num_elements() > 0:
            do_list.remove_do(0)
        assert do_list.num_elements() == 0
        try:
            do_list.get_do(0)
            assert False
        except IndexError:
            # all fine
            pass
        except:
            raise 
                            
    def list_linked(self, do_list, id_listele, listele):
        # do_list is empty
        assert do_list.first_element() == (None, None)
        assert do_list.last_element() == (None, None)
        # add all entries
        for ele in listele:
            do_list.append_do(ele)
        # add some duplicates
        do_list.append_do(listele[0])
        do_list.append_do(listele[2])
        do_list.append_do(listele[1])
        do_list.append_do(listele[1])
        do_list.append_do(listele[1])
        # re-load
        do_list = self.do_infra.lookup_pid(do_list.identifier)
        assert do_list is not None
        assert do_list.num_elements() == 8
        assert do_list.first_element()[0].identifier == id_listele[0]
        assert do_list.last_element()[0].identifier == id_listele[1]
        # test forward iteration
        e, occ = do_list.first_element()
        i = 0
        while e:
            assert e.identifier == do_list.get_do(i).identifier
            i += 1
            e, occ = do_list.next_element(e, occ)
        assert i == do_list.num_elements()

class TestHandleInfrastructure(TestDOInfrastructure):
    
    def setUp(self):
        TestDOInfrastructure.setUp(self)
        # test parameters
        host = TESTING_CONFIG_DEFAULTS["server-address"]
        port = TESTING_CONFIG_DEFAULTS["server-port"]
        urlpath = "/api/handles/"
        prefix = TESTING_CONFIG_DEFAULTS["handle-prefix"]
        additional_identifier_element = ""
        user = ""
        password = ""
        user_index = "300"
        unsafe_ssl = False
        # check for test config file
        cfgparse = ConfigParser()
        if cfgparse.read(("testing-config.cfg", os.environ["HOME"]+"/testing-config.cfg")):
            logger.info("Reading testing config file...")
            if cfgparse.has_option("server", "host"): host = cfgparse.get("server", "host")
            if cfgparse.has_option("server", "port"): port = cfgparse.getint("server", "port")
            if cfgparse.has_option("server", "path"): urlpath = cfgparse.get("server", "path")
            if cfgparse.has_option("server", "user"): user = cfgparse.get("server", "user")
            if cfgparse.has_option("server", "user_index"): user_index = cfgparse.get("server", "user_index")
            if cfgparse.has_option("server", "password"): password = cfgparse.get("server", "password")
            if cfgparse.has_option("server", "unsafe_ssl"): unsafe_ssl = cfgparse.getboolean("server", "unsafe_ssl")
            if cfgparse.has_option("handle", "prefix"): prefix = cfgparse.get("handle", "prefix")
            if cfgparse.has_option("handle", "additionalelement"): additional_identifier_element = cfgparse.get("handle", "additionalelement")
        # now create infra instance
        logger.info("Running tests with following parameters:")
        logger.info("Host: %s, Port: %s, User: %s, User index: %s, URL path: %s, prefix: %s, additional element: %s, unsafe_ssl: %s" % (host, port, user, user_index, urlpath, prefix, additional_identifier_element, unsafe_ssl))
        self.do_infra = HandleInfrastructure(host, port, user, user_index, password, urlpath, prefix=prefix, additional_identifier_element=additional_identifier_element, unsafe_ssl=unsafe_ssl)
        
        
    def tearDown(self):
        for dobj in self.created_pids:
            try:
                self.logger.info("Removing test handle: %s" % dobj)
                self.do_infra.delete_do(dobj)
            except KeyError, exc:
                # already removed, ignore
                pass
            except IOError, exc:
                self.logger.info("Could not delete test identifier %s" % dobj)
        
    def test_additional_element(self):
        id1 = "%s/additional_element_test" % self.do_infra._prefix
        do = self.do_infra.create_do(id1)
        assert do != None
        self.created_pids.append(do.identifier)
        assert do.identifier == "%s/%sadditional_element_test" % (self.do_infra._prefix, self.do_infra._additional_identifier_element)
        do = self.do_infra.lookup_pid(id1)
        assert do != None
        assert do.identifier == "%s/%sadditional_element_test" % (self.do_infra._prefix, self.do_infra._additional_identifier_element) 
        do = self.do_infra.lookup_pid("%s/%sadditional_element_test" % (self.do_infra._prefix, self.do_infra._additional_identifier_element))
        assert do != None
        assert do.identifier == "%s/%sadditional_element_test" % (self.do_infra._prefix, self.do_infra._additional_identifier_element)
        # create DO using generated identifier name
        do = self.do_infra.create_do()
        assert do != None
        self.created_pids.append(do.identifier)
        print(do.identifier)
        assert do.identifier.startswith(self.do_infra._prefix+"/"+self.do_infra._additional_identifier_element)
        

class TestPIDRegExp(unittest.TestCase):
    
    def test_pids(self):
        assert DigitalObject.is_PID_name("12345/123-456-abc-def") == True
        assert DigitalObject.is_PID_name("12345/123 456 abc def") == True
        assert DigitalObject.is_PID_name("12345/123/123/123") == True
        assert DigitalObject.is_PID_name("12345") == False
        assert DigitalObject.is_PID_name("12345./123") == False
        assert DigitalObject.is_PID_name("a12345/123") == False
        assert DigitalObject.is_PID_name("A12345/123") == False

        assert DigitalObject.is_PID_name("0.TYPE/TEST_TYPE") == True
        assert DigitalObject.is_PID_name("0.TYPE/TEST_TYPE with something added") == True
        assert DigitalObject.is_PID_name("0.TYPE/") == False
        assert DigitalObject.is_PID_name("0.TYPE") == False
        assert DigitalObject.is_PID_name("0.TYPE.SUBTYPE/TEST_TYPE") == True

        assert DigitalObject.is_PID_name("Hello World!") == False
        
