'''
Created on 22.06.2012

@author: tobiasweigel
'''
from dkrz.digitalobjects.model.doset import DigitalObjectSet

class C3APIConnector(object):
    '''
    C3 specific connector class that provides methods the C3 infrastructure should call upon specific C3 events.
    
    This class will take care of PID service connection internally.
    '''


    def __init__(self, infrastructure):
        '''
        Constructor.
        
        :param infrastructure: A Digital Object Infrastructure instance to use.
        '''
        self.infrastructure = infrastructure
        self.subprefix = "proj-c3-"
        self.subprefix_cera = "wdcc-"
        self.cera_view_url = "http://cera-www.dkrz.de/WDCC/ui/Compact.jsp?acronym="
        
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
        if not metadata_oai_url.startswith("http://"):
            raise ValueError("OAI URL must be a URL beginning with http://!")
        # prepare identifier names and set
        set_id = self.subprefix+"set-"+data_acronym
        md_id = self.subprefix+metadata_identifier
        data_id = self.subprefix_cera+data_acronym
        doset = self.infrastructure.create_do(self, set_id, do_class=DigitalObjectSet)
        # metadata DO
        do_md = self.infrastructure.create_do(self, md_id)
        do_md.resource_location = metadata_oai_url
        do_md.resource_type = "METADATA"
        # data DO
        do_data = self.infrastructure.create_do(self, data_id)
        do_data.resource_location = self.cera_view_url+data_acronym
        do_data.resource_type = "DATA"
        # compile set
        doset.add_do(do_md)
        doset.add_do(do_data)
        # important: return identifier written in the DOs since it might have changed during generation request
        return (do_md.identifier, do_data.identifier)
        

    def on_data_staged(self, data_pid, logging_text=None):
        """
        data_pid: taken from the single ISO xml.
        logging_text: small textual description (log filke etc.) which will be written into the PID as an annotation.
          this contains a description of e.g. what data corrections were performed.
        
        data is modified (spatial subs etc.) or corrected (23:59 correction)...
        
        returns: pid for modified data. 
        """
        pass
    
    #-------
        
    def on_new_workflow_published(self, sourcecode_svn_url, portal_url):
        """
        Event handler to call when a completely new workflow module is available.
        
        :param sourcecode_svn_url: A URL pointing to the workflow source code. The target location should be
          explicitly referring to a specific SVN revision and the root path of the workflow module code in the
          repository.
        :param portal_url: URL to an end-user web page in the portal specific to this workflow.
        :return: A PID string for this specific workflow's first revision.
        """
        raise NotImplementedError()
        
    def on_new_workflow_version(self, old_workflow_pid, sourcecode_svn_url, portal_url):
        """
        Event handler to call when a new version of an existing workflow has been published.
        
        :param old_workflow_pid: PID for the previous version of this workflow.
        :param sourcecode_svn_url: A URL pointing to the workflow source code (explicit SVN path and revision).
        ;param portal_url: URL to an end-user web page in the portal specific to this workflow.
        :return: A PID string for this workflow's new version. 
        """
        raise NotImplementedError()
    
    def on_workflow_was_run(self, workflow_pid, input_data_list, output):
        """
        Event handler to call when a workflow has been run on input data to produce output data.
        
        :param output: still undefined..
        """
        raise NotImplementedError()
