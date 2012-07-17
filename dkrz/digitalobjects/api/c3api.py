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
        :param portal_url: URL to an end-user web page in the portal specific to this workflow.
        :return: A PID string for this workflow's new version. 
        """
        raise NotImplementedError()
    
    def on_workflow_was_run(self, workflow_pid, input_data_list, output):
        """
        Event handler to call when a workflow has been run on input data to produce output data.
        
        :param output: still undefined..
        """
        raise NotImplementedError()
