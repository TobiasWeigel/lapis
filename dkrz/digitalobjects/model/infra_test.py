'''
Created on 03.05.2012

:author: tobiasweigel
'''
import unittest
from dkrz.digitalobjects.infra.infrastructure import InMemoryInfrastructure, PIDAlreadyExistsError

from random import Random

import logging
from dkrz.digitalobjects.infra.handleinfrastructure import HandleInfrastructure

from dkrz.digitalobjects.model.do import DigitalObject

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
        
