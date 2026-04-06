import sys
import time
import logging
import os
import zipfile
import shutil
import argparse
import arcpy
import organization
import publisher


def iszip(testgdb):

    if testgdb.zipped.endswith('.zip'):
        return True
    else:
        return False
    
def isreasonablesize(testgdb
                    ,pexpectedmb
                    ,pvariance):
    
    sizemb = os.path.getsize(testgdb.zipped) / (1024 * 1024)

    if (abs(pexpectedmb - sizemb) / pexpectedmb * 100) > int(pvariance):
        return False
    else:
        return True
    
def isgdbinzip(testgdb):

    if not os.path.exists(testgdb.gdb):
        return False
    else:
        return True

def haslocks(testgdb):

    # this checks the testgdb.unzipped
    if testgdb.has_locks():
        return True
        
    return False
    
def isvalidgdb(testgdb
              ,pname
              ,pworkdir):

    # this creates a gdb lock
    desc = arcpy.Describe(testgdb.gdb) 

    if not (desc.dataType == 'Workspace' 
            and desc.workspaceType == 'LocalDatabase'):
        return False
    else:
        return True

    # Try to clear locks. This is a temp file so it doesnt matter
    # Except possibly preventing cleanup
    arcpy.ClearWorkspaceCache_management()    

def report(testgdb
          ,expectedname
          ,workdir
          ,expectedmb
          ,expectedmbbvariannce=25):

    qareport = ""

    # check that we downloaded a .zip
    # for this one we kick back early
    if not iszip(testgdb):
        qareport += '{0} download {1} doesnt appear to be'.format(os.linesep
                                                                  ,testgdb.zipped)
        qareport += ' a zip file{2}'.format(os.linesep)
        # exit early if not a zip file
        return qareport

    if not isreasonablesize(testgdb
                           ,expectedmb
                           ,expectedmbbvariannce):
        qareport += '{0} downloaded zip file size is'.format(os.linesep)
        qareport +=  ' suspiciously different from expected {0} MB {1}'.format(
                        expectedmb
                       ,os.linesep)
                     
    if not isgdbinzip(testgdb):
        
        qareport += '{0} unzipping downloaded {1}'.format(os.linesep
                                                         ,testgdb.zipped)
        qareport += ' does not produce {0}{1}'.format(expectedname, os.linesep)
                                                                             
    if haslocks(testgdb):
        
        # call before isvalidgdb since arcpy may create locks
        qareport += '{0} downloaded {1}'.format(os.linesep
                                               ,testgdb.unzipped)
        qareport += ' contains locks {0}'.format(os.linesep)

    if not isvalidgdb(testgdb
                     ,expectedname
                     ,workdir):
        
        qareport += '{0} downloaded {1} is not a'.format(os.linesep
                                                        ,testgdb.unzipped)
        qareport += ' valid gdb according to arcpy {0}'.format(os.linesep)
        
    return qareport 

def qalogging(logfile
             ,level=logging.INFO):
    
    qalogger = logging.getLogger(__name__)
    qalogger.setLevel(level)
    filehandler = logging.FileHandler(logfile)
    qalogger.addHandler(filehandler)

    return qalogger

def main():

    parser = argparse.ArgumentParser(
        description="QA a file geodatabase in ArcGIS Online"
    )

    parser.add_argument("pitemid"
                       ,help="Item id in ArcGIS Online")
    parser.add_argument("pgdbname"
                       ,help="File geodatabase name")
    parser.add_argument("ptempdir"
                       ,help="A local temp directory")
    parser.add_argument("pzipmb"
                       ,help="Expected geodatabase MB zipped"
                       ,type=float)
    args = parser.parse_args()

    timestr = time.strftime("%Y%m%d-%H%M%S")
    
    # qa-replace-cscl-gdb-20241121-114410.log
    # qa-replace-cscl_pub-gdb-20241121-114410.log
    targetlog = os.path.join(os.environ['TARGETLOGDIR'] 
                            ,'{0}-replace-{1}-{2}.log'.format(
                               'qa'
                               ,args.pgdbname.replace('.', '-')
                               ,timestr)
                            )
    
    qalogger = qalogging(targetlog)

    org = organization.Organization(os.environ['NYCMAPSUSER']
                                   ,os.environ['NYCMAPSCREDS'])
        
    pubgdb = publisher.PublishedItem(org
                                    ,args.pitemid)
    # D:\temp\cscl.gdb.zip
    pubgdb.download(args.ptempdir)

    # this will set both 
    # testgdb.gdb      = D:\temp\xyz.gdb
    # testgdb.unzipped = D:\temp\xyz.gdb
    testgdb = publisher.LocalGeodatabase(os.path.join(args.ptempdir
                                                     ,args.pgdbname))
    testpub = publisher.PublishWorkflow(testgdb)
    testpub.zipped = pubgdb.zipped
    testpub.unzip(args.ptempdir)
    
    retqareport = report(testpub
                        ,args.pgdbname
                        ,args.ptempdir
                        ,args.pzipmb)
    
    arcpy.ClearWorkspaceCache_management()
    #pubgdb.clean()
    #testgdb.clean()

    if len(retqareport) > 4:
        # len 4 allows for a pair of sloppy CRLFs
        # QA does not notify. It QAs 
        qalogger.error('ERROR: Please review {0}'.format(os.linesep))
        qalogger.error(retqareport)
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()