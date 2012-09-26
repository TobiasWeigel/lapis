'''
Created on 13.07.2012

@author: tobiasweigel

Copyright 2012 Tobias Weigel

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''
from dkrz.digitalobjects.infra.handleinfrastructure import HandleInfrastructure

class EPICInfrastructure(HandleInfrastructure):
    '''
    classdocs
    '''


    def __init__(self, host, port, path, prefix = None):
        '''
        Constructor.
        
        :param host: Host name where the EPIC Webservice is running.
        :param port: Port number of the EPIC webservice.
        :param path: Additional URL path to use.
        :param prefix: The Handle prefix to use. Purely optional. If given, random PID creation will rely on the
          internal function of this package rather than the functionality of the EPIC webservice. Note that even if a
          prefix is given, identifier strings must also always include it.
        '''
        super(EPICInfrastructure, self).__init__(host, port, path, prefix = prefix, additional_identifier_element = None)
        
    def _generate_random_identifier(self):
        if not self.prefix:
            raise ValueError("Cannot generate random EPIC PIDs if no prefix is provided!")
        rid = super(EPICInfrastructure, self)._generate_random_identifier()
        return self.prefix+"/"+rid
    
    def _prepare_identifier(self, identifier):
        # additional_identifier_element is not supported here!
        # split identifier into prefix and suffix 
        parts = identifier.split("/", 1)
        if len(parts) != 2:
            raise ValueError("Invalid identifier - no separating slash between prefix and suffix: %s" % identifier)
        # construct path according to EPIC service specification
        path = "%sNAs/%s/handles/%s/" % (self.path, parts[0], parts[1])
        return path, identifier
    
    # ~~~~~ The following methods need to be rewritten to match the EPIC REST style ~~~~~
    
    def _write_annotation(self, identifier, key, value):
        # must use PUT instead of POST
        pass
    
    def _write_resource_information(self, identifier, resource_location, resource_type=None):
        # must use PUT instead of POST
        pass
    
    def _write_reference(self, identifier, key, reference):
        # must use PUT instead of POST
        pass
    
