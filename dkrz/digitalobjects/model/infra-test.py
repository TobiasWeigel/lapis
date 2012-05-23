'''
Created on 03.05.2012

@author: tobiasweigel
'''
import unittest
from dkrz.digitalobjects.infra.infrastructure import InMemoryInfrastructure, PIDAlreadyExistsError

from random import Random
import string

import logging
from dkrz.digitalobjects.infra.handleinfrastructure import HandleInfrastructure

class TestDOInfrastructure(unittest.TestCase):
    
    def setUp(self):
        self.do_infra = InMemoryInfrastructure()
        self.do_infra.set_random_seed(12345)
        self.logger = logging.getLogger(__name__)
        self.random = Random(43210)
        self.created_pids = []
        self.prefix = "10876/"
        
    def tearDown(self):
        pass
    
    def test_do_values(self):
        # values
        pid = self.prefix+"test_do_values"
        resloc = "http://www.example.com/1"
        restype = "MY_TEST_TYPE"
        annot1 = "test annotation 1"
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
        # delete and check for removal
        self.do_infra.delete_do(pid)
        dobj2 = self.do_infra.lookup_pid(pid)
        assert dobj2 == None
        
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
            

class TestHandleInfrastructure(TestDOInfrastructure):
    
    def setUp(self):
        TestDOInfrastructure.setUp(self)
        self.do_infra = HandleInfrastructure("localhost", 8001, "/handle/", prefix="10876", additional_identifier_element="infra-test/")
        
    def tearDown(self):
        for dobj in self.created_pids:
            try:
                self.logger.info("Removing test handle: %s" % dobj)
                self.do_infra.delete_do(dobj)
            except IOError, exc:
                self.logger.info("Could not delete test identifier %s" % dobj)
        
        
