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

from lapis.model.do import DigitalObject

from ConfigParser import ConfigParser
from lapis.model.doset import DigitalObjectSet

TESTING_CONFIG_DEFAULTS = {"handle-prefix": "10876", "server-address": "localhost", "server-port": 8001, "additional-identifier-element": "infra-test/"}

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
        annot1 = "test annotation 1"
        pid2 = self.prefix+"test_do_values_2"
        pid3 = self.prefix+"test_do_values_3"
        # create DO
        dobj = self.do_infra.create_do(pid)
        self.created_pids.append(pid)
        assert dobj != None
        dobj.resource_location = resloc
        assert dobj.resource_location == resloc
        dobj.resource_type = restype
        assert dobj.resource_type == restype
        dobj.set_annotation("annot1", annot1)
        assert dobj.get_annotation("annot1") == annot1
        assert dobj.get_annotation("nonexisting") == None
        # look up and assert
        dobj2 = self.do_infra.lookup_pid(pid)
        assert dobj2 != None
        assert dobj2.resource_location == resloc
        assert dobj2.resource_type == restype
        assert dobj2.get_annotation("annot1") == annot1
        assert dobj2.get_annotation("nonexisting") == None
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
        # check references
        self.__check_dobj3_references(dobj3, dobj, dobj2)
        # retrieve dobj3 from infra and check references
        dobj3 = self.do_infra.lookup_pid(pid3)
        self.__check_dobj3_references(dobj3, dobj, dobj2)
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
            assert sele.get_references("subelement-of")
        assert num_subele == 4
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
        assert len(self.do_infra.lookup_pid(id_ele[0]).get_references("subelement-of")) == 0
        
        
                

class TestHandleInfrastructure(TestDOInfrastructure):
    
    def setUp(self):
        TestDOInfrastructure.setUp(self)
        # test parameters
        host = "localhost"
        port = 8080
        urlpath = "/handle/"
        prefix = TESTING_CONFIG_DEFAULTS["handle-prefix"]
        additional_identifier_element = "infra-test/"
        # check for test config file
        cfgparse = ConfigParser()
        if cfgparse.read(("testing-config.cfg", os.environ["HOME"]+"/testing-config.cfg")):
            logger.info("Reading testing config file...")
            if cfgparse.has_option("server", "host"): host = cfgparse.get("server", "host")
            if cfgparse.has_option("server", "port"): port = cfgparse.getint("server", "port")
            if cfgparse.has_option("server", "path"): urlpath = cfgparse.get("server", "path")
            if cfgparse.has_option("handle", "prefix"): prefix = cfgparse.get("handle", "prefix")
            if cfgparse.has_option("handle", "additionalelement"): additional_identifier_element = cfgparse.get("handle", "additionalelement")
        # now create infra instance
        logger.info("Running tests with following parameters:")
        logger.info("Host: %s, Port: %s, URL path: %s, prefix: %s, additional element: %s" % (host, port, urlpath, prefix, additional_identifier_element))
        self.do_infra = HandleInfrastructure(host, port, urlpath, prefix=prefix, additional_identifier_element=additional_identifier_element)
        
        
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
        
        

class TestPIDRegExp(unittest.TestCase):
    
    def test_pids(self):
        assert DigitalObject.is_PID("12345/123-456-abc-def") == True
        assert DigitalObject.is_PID("12345/123 456 abc def") == True
        assert DigitalObject.is_PID("12345/123/123/123") == True
        assert DigitalObject.is_PID("12345") == False
        assert DigitalObject.is_PID("12345./123") == False
        assert DigitalObject.is_PID("a12345/123") == False
        assert DigitalObject.is_PID("A12345/123") == False

        assert DigitalObject.is_PID("0.TYPE/TEST_TYPE") == True
        assert DigitalObject.is_PID("0.TYPE/TEST_TYPE with something added") == True
        assert DigitalObject.is_PID("0.TYPE/") == False
        assert DigitalObject.is_PID("0.TYPE") == False
        assert DigitalObject.is_PID("0.TYPE.SUBTYPE/TEST_TYPE") == True

        assert DigitalObject.is_PID("Hello World!") == False
        
