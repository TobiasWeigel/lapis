'''
Created on 22.06.2012

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
from lapis.model.doset import DigitalObjectSet

class C3APIConnector(object):
    '''
    C3 specific connector class that provides methods the C3 infrastructure should call upon specific C3 events.
    
    This class will take care of PID service connection internally.
    '''


    def __init__(self, infrastructure, site):
        '''
        Constructor.
        
        :param infrastructure: A Digital Object Infrastructure instance to use.
        :param site: A string identifying the site this package is called on, e.g. "WDCC", "AWI" and so on.
          The class will behave differently to accomodate each project partner's differing infrastructures.
        '''
        self.infrastructure = infrastructure
        self.subprefix = "proj-c3-"
        self.subprefix_cera = "wdcc-"
        self.cera_view_url = "http://cera-www.dkrz.de/WDCC/ui/Compact.jsp?acronym="
        if site not in ["WDCC"]:
            raise ValueError("Unknown site: %s" % site)
        self.site = site
        
    def on_metadata_generated(self, metadata_oai_url, metadata_identifier, data_acronym):
        """
        Event to be called when a new metadata record (ISO XML) has been generated.
        
        :param metadata_oai_url: The OAI URL where the metadata document will be available.
        :param metadata_identifier: A identifier for the metadata document, preferably human-readable. Note that this
          will only be used to construct the PID name. It is not required that this identifier is dereferencable.
        :param data_acronym: The acronym for the corresponding data in the CERA database. This will be used to define
          a target URL where the data PID can point to (such as a CERA compact view page).
        
        :returns: (metadata_pid, data_pid) as generated by this method.
        """
        # verify parameters
        if not (metadata_oai_url.startswith("http://") or metadata_oai_url.startswith("https://")):
            raise ValueError("OAI URL must be a URL beginning with http:// or https://!")
        # prepare identifier names and set
        set_id = self.infrastructure.prefix+"/"+self.subprefix+"set-"+data_acronym
        md_id = self.infrastructure.prefix+"/"+self.subprefix+metadata_identifier
        data_id = self.infrastructure.prefix+"/"+self.subprefix_cera+data_acronym
        doset = self.infrastructure.create_do(set_id, do_class=DigitalObjectSet)
        # metadata DO
        do_md = self.infrastructure.create_do(md_id)
        do_md.resource_location = metadata_oai_url
        do_md.resource_type = "METADATA"
        # data DO
        do_data = self.infrastructure.create_do(data_id)
        do_data.resource_location = self.cera_view_url+data_acronym
        do_data.resource_type = "DATA"
        # compile set
        doset.add_do(do_md)
        doset.add_do(do_data)
        # important: return identifier written in the DOs since it might have changed during generation request
        return (do_md.identifier, do_data.identifier)
        

    def on_data_staged(self, data_pid, dms_uid, logging_text=None):
        """
        Event to be called when data has been staged as requested by the DMS.
        
        :param data_pid: The PID of the data that was staged.
        :param dms_uid: The UID given by the DMS to the staging request. 
        :param logging_text: A short textual description (log file etc.) of the data modifications that have ben done 
          during data staging, e.g. temporal or variable subsetting.
        
        :returns: pid for modified data. 
        """
        new_id = self.infrastructure.prefix+"/"+self.subprefix+"dms-"+dms_uid
        # look up data PID
        do_old = self.infrastructure.lookup_pid(data_pid)
        if isinstance(do_old, DigitalObjectSet):
            # okay, no problem, we'll try to find the subelement that refers to data
            data_dos = []
            for ele in do_old.iter_set_elements():
                if ele.resource_type == "DATA":
                    data_dos.append(ele)
            if len(data_dos) == 0:
                raise Exception("Could not find any data object in the given Digital Object Set!")
            if len(data_dos) > 1:
                raise Exception("Found more than one data object in the given Digital Object Set!")
            do_old = data_dos[0]
        elif do_old.resource_type != "DATA":
            raise Exception("Given Digital Object is not typed as referring to a data object!")
        # create new DO for data; will not receive a resource location yet
        do_new = self.infrastructure.create_do(new_id)
        # remember the DMS UID by putting it in the DO key metadata record
        do_new.set_annotation("dms-uid", dms_uid)
        # also append logging text if available
        if logging_text:
            do_new.set_annotation("log", logging_text)        
        # provenance: refer to old data DO
        do_new.add_do_reference("derived-from", do_old)
        return do_new.identifier
    
    def on_new_workflow_published(self, sourcecode_svn_url, workflow_name):
        """
        Event handler to call when a completely new workflow module is available.
        
        :param sourcecode_svn_url: A URL pointing to the workflow source code. The target location should be
          explicitly referring to a specific SVN revision and the root path of the workflow module code in the
          repository.
        :param workflow_name: Human-readable name of the workflow. Will be used as part of the identifier string for the
          workflow PID. 
        :return: A PID string for this specific workflow's first revision.
        """
        wf_id = self.infrastructure.prefix+"/"+self.subprefix+self.infrastructure.clean_identifier_string(workflow_name)+"/0"
        do_old = self.infrastructure.lookup_pid(wf_id)
        if do_old:
            raise Exception("A workflow with this name already exists. Please use the 'version workflow' method to submit a new version of this workflow!")        
        do_new = self.infrastructure.create_do(wf_id)
        do_new.resource_location = sourcecode_svn_url
        do_new.resource_type = "SOFTWARE"
        return do_new.identifier
        
    def on_new_workflow_version(self, old_workflow_pid, sourcecode_svn_url):
        """
        Event handler to call when a new version of an existing workflow has been published.
        The PID string used for the new workflow version is generated based on the old one.
        
        :param old_workflow_pid: PID for the previous version of this workflow.
        :param sourcecode_svn_url: A URL pointing to the workflow source code (explicit SVN path and revision).
        :return: A PID string for this workflow's new version. 
        """
        do_old_wf = self.infrastructure.lookup_pid(old_workflow_pid)
        if not do_old_wf.resource_type == "SOFTWARE":
            raise Exception("The given PID for the old workflow version is not of resource type SOFTWARE. Did you provide the correct PID?")
        new_wf_id = do_old_wf.identifier
        id_name_failed = False
        if new_wf_id.count("/") < 2:
            # no slash in suffix; start counting from here then..
            new_wf_id += "/1"
        else:
            slashpos = new_wf_id.rfind("/")
            old_num = new_wf_id[slashpos+1:]
            try:
                old_num = int(old_num)
                new_num = old_num+1
                new_wf_id = new_wf_id[:slashpos]+"/"+new_num
            except:
                # no number after last slash.. use a random ID
                id_name_failed = True
        if id_name_failed:
            # something went wrong when trying to construct a new PID from the old one; use a random one..
            do_new_wf = self.infrastructure.create_do()
        else:
            do_new_wf = self.infrastructure.create_do(new_wf_id)
        do_new_wf.resource_location = sourcecode_svn_url
        do_new_wf.resource_type = "SOFTWARE"
        do_new_wf.add_do_reference("derived-from", do_old_wf)
        return do_new_wf.identifier
    
    def on_workflow_was_run(self, workflow_pid, input_pid_list, output):
        """
        Event handler to call when a workflow has been run on input data to produce output data.
        
        :param workflow_pid: The PID of the workflow (the exact version) having been used.
        :param input_pid_list: List of PIDs for input PIDs. Can be both data and metadata objects, or preferably 
          collections thereof. 
        :param output: still undefined - must connect data and MD objects correctly to their respective predecessors,
          if possible. 
        """
        raise NotImplementedError()