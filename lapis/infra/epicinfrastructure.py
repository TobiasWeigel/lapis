'''
Created on 13.07.2012

@author: tobiasweigel

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
from lapis.infra.handleinfrastructure import HandleInfrastructure

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
    
