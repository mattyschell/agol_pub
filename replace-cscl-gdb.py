# calling bat must
# set AGOLPUB=D:\gis\agol-pub\src\py
# set PYTHONPATH=%PYTHONPATH%;%AGOLPUB%
# set NYCMAPSUSER=xxxx.xxx.xxx
# set NYCMAPSCREDS=xxxxxx
# set TARGETLOGDIR=D:\gis\geodatabase-scripts\logs\replace_cscl_gdb\
import sys
import time
import logging
import os
import argparse

import organization
import publisher


def main():

    parser = argparse.ArgumentParser(
        description="Replace a file geodatabase in ArcGIS Online"
    )
    parser.add_argument("srcgdb"
                       ,help="Local file geodatabase")
    parser.add_argument("targetgdbname"
                       ,help="File geodatabase name in ArcGIS Online")
    parser.add_argument("targetitemid"
                       ,help="Item id in ArcGIS Online")
    parser.add_argument("tempdir"
                       ,help="A local temp directory")
    args = parser.parse_args()

    retval = 1

    timestr = time.strftime("%Y%m%d-%H%M%S")

    try:

        org = organization.Organization(os.environ['NYCMAPSUSER']
                           ,os.environ['NYCMAPCREDS'])
        filegdb = publisher.LocalGeodatabase(args.srcgdb)
        filepub = publisher.PublishWorkflow(filegdb)
    
    except Exception as e:
        raise ValueError("Failure {0} in instantiation".format(e)) 
    
    # replace-cscl-gdb-20241121-114410.log
    # replace-cscl_pub-gdb-20241121-114410.log
    targetlog = os.path.join(os.environ['TARGETLOGDIR'] 
                            ,'replace-{0}-{1}.log'.format(
                                args.targetgdbname.replace('.', '-')
                               ,timestr
                               )
                            )

    logging.basicConfig(filename=targetlog
                       ,level=logging.INFO)

    logging.info('precleaning any old temp files at {0}'.format(args.tempdir))
    
    # this should succeed 
    filepub.clean()
    
    logging.info('renaming {0} to {1} and zipping it'.format(
                                                        filegdb.gdb
                                                       ,args.targetgdbname))

    pubgdb = publisher.PublishedItem(org
                                    ,args.targetitemid)
    
    try:
        # a known source (get it) of issues
        filepub.renamezip(args.tempdir
                         ,args.targetgdbname)
        retval = 0
    except Exception as e:
        logging.error('Failure calling renamezip for {0}'.format(filegdb.gdb))
        logging.error('The error is {0}'.format(e))
        retval = 1
                        
    if retval == 0:
        logging.info('replacing nycmaps item with id {0}'.format(
                                                            args.targetitemid))

        try:
            replaceval = pubgdb.replace(filepub.zipped)
            if replaceval:
                logging.info('Successfully replaced {0}'.format(
                    args.targetgdbname))
                retval = 0
            else:
                logging.error(
                    'Failure, ArcGIS API returned false replacing {0}'.format(
                        args.targetgdbname))
                retval = 1
        except:
            logging.error('Failure replacing {0}'.format(args.targetgdbname))
            retval = 1
        
        try:
            filepub.clean()
        except:
            # https://github.com/mattyschell/agol-pub/issues/4
            # shame 
            pass
    
    sys.exit(retval)

if __name__ == '__main__':
    main()
