'''
Created on 03.05.2012

@author: tobiasweigel
'''
import unittest
from dkrz.pid.infra.infrastructure import InMemoryInfrastructure, PIDAlreadyExistsError

from random import Random
import string

import logging
from dkrz.pid.infra.handleinfrastructure import HandleInfrastructure

class TestPIDInfrastructure(unittest.TestCase):
    
    def setUp(self):
        self.pid_infra = InMemoryInfrastructure()
        self.pid_infra.set_random_seed(12345)
        self.logger = logging.getLogger(__name__)
        self.random = Random(43210)
        self.created_pids = []
        self.prefix = "10876/"
        
    def tearDown(self):
        pass
    
    def test_pid_values(self):
        # values
        pid_id = self.prefix+"test_pid_values"
        resloc = "http://www.example.com/1"
        annot1 = "test annotation 1"
        # reate pid
        pid = self.pid_infra.create_pid(pid_id)
        self.created_pids.append(pid_id)
        assert pid != None
        pid.resource_location = resloc
        assert pid.resource_location == resloc
        pid.set_annotation("annot1", annot1)
        assert pid.get_annotation("annot1") == annot1
        assert pid.get_annotation("nonexisting") == None
        # look up and assert
        pid2 = self.pid_infra.lookup_pid(pid_id)
        assert pid2 != None
        assert pid2.resource_location == resloc
        assert pid2.get_annotation("annot1") == annot1
        assert pid2.get_annotation("nonexisting") == None
        
    def test_infra_operations(self):
        pid = self.pid_infra.lookup_pid(self.prefix+"does-not-exist")
        assert pid == None
        # duplication attempts
        pid = self.pid_infra.create_pid(self.prefix+"duplicate")
        self.created_pids.append(self.prefix+"duplicate")
        assert pid != None
        try:
            pid2 = self.pid_infra.create_pid(self.prefix+"duplicate")
            self.fail("Creation attempt of duplicate PID successful!")
        except PIDAlreadyExistsError:
            pass
        else:
            self.fail("Creation attempt of duplicate PID successful/compromised!")
            
    def test_random_pid_creation(self):
        for x in range (0,10):
            pid = self.pid_infra.create_pid()
            self.created_pids.append(pid.identifier)
            assert pid != None
            self.logger.info(pid.identifier)
            

class TestHandleInfrastructure(TestPIDInfrastructure):
    
    def setUp(self):
        TestPIDInfrastructure.setUp(self)
        self.pid_infra = HandleInfrastructure("localhost", 8001, "/handle/", prefix="10876", additional_identifier_element="infra-test/")
        
    def tearDown(self):
        for pid in self.created_pids:
            try:
                self.logger.info("Removing test handle: %s" % pid)
                self.pid_infra.delete_pid(pid)
            except IOError, exc:
                self.logger.info("Could not delete test identifier %s" % pid)
        
        
