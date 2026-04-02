import os
import stat
import shutil
from pathlib import Path

# we may manage several types of content
# simple first case: a local gdb published to an item 
#                    on the nycmaps organization 


class PublishWorkflowError(Exception):
    pass


class LockFilesPresentError(PublishWorkflowError):
    pass

class PublishedItem(object):

    def __init__(self
                ,org
                ,id):

        self.org  = org
        self.id   = id
        self.zipped = None
        self.existingitem = self.org.gis.content.get(self.id)

        if self.existingitem is None:
            raise ValueError('ArcGIS item not found for id {0}'.format(self.id))

    def describe(self):

        for var, value in self.__dict__.items(): 
            print(f'{var}: {value}')

    def replace(self,
                localcontent):
        
        # returns true or false
        return(self.existingitem.update(data=localcontent))  

    def download(self
                ,localpath): 

        #should return path\item.zip
        self.zipped = self.existingitem.download(localpath)

        if not self.zipped.endswith('.zip'):
            raise ValueError('didnt download a zip file, got {0}'.format(self.zipped))

    def clean(self):

        # Contract: remove the downloaded zip when present, but keep
        # self.zipped as the original path string so callers can check
        # os.path.isfile(self.zipped) after cleanup.

        if self.zipped and os.path.isfile(self.zipped):
            # let it throw caller should know
            os.remove(self.zipped)

        
class LocalGeodatabase(object):

    def __init__(self
                ,filegdb):

        self.gdb  = filegdb
        self.gdbname = os.path.basename(self.gdb)
        self.gdbpath = os.path.dirname(self.gdb)


class PublishWorkflow(object):

    def __init__(self
                ,localgdb):

        self.localgdb = localgdb

        # depending on failure point any of these can exist 
        # and muck up a re-run
        self.tempcopy = None 
        self.renamed  = None
        self.zipped   = None
        self.unzipped = None

    @property
    def gdb(self):
        return self.localgdb.gdb

    @property
    def gdbname(self):
        return self.localgdb.gdbname

    @property
    def gdbpath(self):
        return self.localgdb.gdbpath
        
    def zip(self
           ,zippath):
        
        # we mostly always renamezip (slower, next def)
        # zip then move here
        
        # zippath is the target dir
        #     C:\dir2
        # start: C:\dir1\mydata.gdb
        # end:   C:\dir2\mydata.gdb.zip        

        zippedsrc = shutil.make_archive(self.localgdb.gdb
                                       ,'zip'
                           ,self.localgdb.gdbpath
                           ,self.localgdb.gdbname)

        self.zipped = shutil.move(zippedsrc
                                 ,zippath)

    def renamezip(self
                 ,zippath
                 ,name):

        # zippath is the target dir
        #     C:\dir2
        # name is the new name 
        #     pubdata.gdb
        # start: C:\dir1\mydata.gdb
        # end:   C:\dir2\pubdata.gdb.zip  
        # 1 copy 2 rename 3 zip

        self.tempcopy = os.path.join(zippath
                        ,"{0}".format(self.localgdb.gdbname))
        self.renamed  = os.path.join(zippath,"{0}".format(name))

        # pre-clean
        self.clean()

        # C:\dir1\mydata.gdb to
        # C:\dir2\mydata.gdb

        # This is our most likely spot to fail if 
        # the source is not present or is locked down
        # The CSCL production environment is mysterious
        try:
            shutil.copytree(self.localgdb.gdb
                           ,self.tempcopy
                           ,ignore=shutil.ignore_patterns("*.lock"))
        except FileNotFoundError as fnf_error:
            raise FileNotFoundError(f"File not found: {fnf_error}") 
        except PermissionError as perm_error:
            raise PermissionError(f"Permission error: {perm_error}")
        except shutil.Error as shutil_error:
            raise shutil.Error(f"Shutil error: {shutil_error}")
        except Exception as e:
            raise PublishWorkflowError(
                f"Unexpected error during copytree for {self.localgdb.gdb}: {e}") from e

        if not self.has_locks():
            # C:\dir2\mydata.gdb to
            # C:\dir2\pubdata.gdb
            os.rename(self.tempcopy
                     ,self.renamed)
        else:
            raise LockFilesPresentError(
                'Lock files exist in {0}'.format(self.tempcopy))
        
        # C:\temp\dir2\pubdata.gdb
        # C:\temp\dir2\pubdata.gdb.zip
        self.zipped = shutil.make_archive(self.renamed
                                         ,'zip'
                                         ,zippath
                                         ,name)
        
    def unzip(self
             ,unzippath):
        
        shutil.unpack_archive(self.zipped
                             ,unzippath)   

        self.unzipped = self.zipped.replace('.zip','')     

    def remove_readonly(self
                       ,func
                       ,path
                       ,_):
        
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def has_locks(self):

        # after copying from self.gdb source
        # none of our target gdbs should contain locks
        if ( self.tempcopy 
             and Path(self.tempcopy).exists() 
             and any(Path(self.tempcopy).glob("*.lock"))
           ):
           return True
        if ( self.renamed 
             and Path(self.renamed).exists() 
             and any(Path(self.renamed).glob("*.lock"))
           ):
           return True
        if ( self.unzipped 
             and Path(self.unzipped).exists() 
             and any(Path(self.unzipped).glob("*.lock"))
           ):
           return True

        return False

    def clean(self):

        if (self.tempcopy and os.path.exists(self.tempcopy)):
            # PermissionError: [WinError 5] 
            #     Access is denied: 'D:\\temp\\renamesample.gdb'
            # some files in the gdb are readonly (but not the dir itself)
            # onexc callback is copied verbatim from the shutil docs
            shutil.rmtree(self.tempcopy, onerror=self.remove_readonly)
        
        if (self.renamed and os.path.exists(self.renamed)):
            # PermissionError: [WinError 5] 
            #     Access is denied: 'D:\\temp\\renamesample.gdb'
            # some files in the gdb are readonly (but not the dir itself)
            # onexc callback is copied verbatim from the shutil docs
            shutil.rmtree(self.renamed, onerror=self.remove_readonly)

        if (self.zipped and os.path.isfile(self.zipped)):
            # let it throw caller should know
            os.remove(self.zipped)    
            # From cscl but not from tests
            # PermissionError: [WinError 32] The process cannot access the file 
            # because it is being used by another process
            # reminder that this just fails silently
            # shutil.rmtree(self.zipped, ignore_errors=True)

        if (self.unzipped and os.path.isdir(self.unzipped)):
            shutil.rmtree(self.unzipped, onerror=self.remove_readonly)


class pubitem(PublishedItem):
    pass


class localgdb(LocalGeodatabase):

    def __init__(self
                ,filegdb):

        super().__init__(filegdb)
        self.workflow = PublishWorkflow(self)

    @property
    def tempcopy(self):
        return self.workflow.tempcopy

    @tempcopy.setter
    def tempcopy(self
                ,value):
        self.workflow.tempcopy = value

    @property
    def renamed(self):
        return self.workflow.renamed

    @renamed.setter
    def renamed(self
               ,value):
        self.workflow.renamed = value

    @property
    def zipped(self):
        return self.workflow.zipped

    @zipped.setter
    def zipped(self
              ,value):
        self.workflow.zipped = value

    @property
    def unzipped(self):
        return self.workflow.unzipped

    @unzipped.setter
    def unzipped(self
                ,value):
        self.workflow.unzipped = value

    def zip(self
           ,zippath):
        return self.workflow.zip(zippath)

    def renamezip(self
                 ,zippath
                 ,name):
        return self.workflow.renamezip(zippath
                                      ,name)

    def unzip(self
             ,unzippath):
        return self.workflow.unzip(unzippath)

    def remove_readonly(self
                       ,func
                       ,path
                       ,_):
        return self.workflow.remove_readonly(func
                                            ,path
                                            ,_)

    def has_locks(self):
        return self.workflow.has_locks()

    def clean(self):
        return self.workflow.clean()


         

            

        
