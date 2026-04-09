# calling shell or bat must
# set AGOLPUB=D:\gis\agol_pub\src\py
# set PYTHONPATH=%PYTHONPATH%;%AGOLPUB%
# set NYCMAPSUSER=xxxx.xxx.xxx
# set NYCMAPSCREDS=xxxxxx
import argparse
import logging
import os
import sys
import tempfile
import time

import organization
import publisher


def _result_ok(result):

    if result is False or result is None:
        return False

    if isinstance(result, dict) and 'success' in result:
        return bool(result['success'])

    return True


def main():

    parser = argparse.ArgumentParser(
        description=(
            'Overwrite hosted feature layers from CSV or swap source views'
        )
    )

    subparsers = parser.add_subparsers(dest='operation'
                                      ,required=True)

    overwrite_parser = subparsers.add_parser(
        'overwrite'
       ,help='Overwrite a hosted feature layer with a local CSV'
    )
    overwrite_parser.add_argument('itemid'
                                 ,help='Hosted feature layer item id')
    overwrite_parser.add_argument('csvpath'
                                 ,help='Local csv file path')

    swap_parser = subparsers.add_parser(
        'swap-view'
       ,help='Call FeatureLayerCollection.manager.swap_view()'
    )
    swap_parser.add_argument('itemid'
                            ,help='Hosted feature layer item id')
    swap_parser.add_argument('index'
                            ,help='View layer index to swap')
    swap_parser.add_argument('new_source'
                            ,help='Hosted feature layer item id to use as new source')
    swap_parser.add_argument('--source-index'
                            ,default=0
                            ,type=int
                            ,help='Layer index on the new source item to use')

    args = parser.parse_args()

    timestr = time.strftime("%Y%m%d-%H%M%S")
    targetlogdir = os.environ.get('TARGETLOGDIR'
                                 ,tempfile.gettempdir())
    targetlog = os.path.join(
        targetlogdir
       ,'replace-hfl-{0}-{1}.log'.format(
            args.itemid
           ,timestr
        )
    )

    logging.basicConfig(filename=targetlog
                       ,level=logging.INFO
                       ,format='%(asctime)s - %(levelname)s - %(message)s'
                       ,datefmt='%Y-%m-%d %H:%M:%S')

    try:

        logging.info('main starting operation={0} itemid={1}'.format(
            args.operation
           ,args.itemid))

        logging.info('organization setup starting itemid={0}'.format(
            args.itemid))
        org = organization.Organization.from_env()
        logging.info('organization setup completed itemid={0}'.format(
            args.itemid))

        if args.operation == 'overwrite':
            logging.info(
                'overwrite publisher init starting itemid={0}'.format(
                    args.itemid))
            hflpub = publisher.HostedFeatureLayerPublisher(org
                                                          ,args.itemid
                                                          ,args.csvpath)
            logging.info(
                'overwrite publisher init completed itemid={0}'.format(
                    args.itemid))

            logging.info(
                'overwrite operation starting itemid={0}'.format(
                    args.itemid))
            result = hflpub.overwrite()
            logging.info(
                'overwrite operation completed itemid={0}'.format(
                    args.itemid))
        else:
            logging.info(
                'swap-view publisher init starting view_itemid={0} '
                'source_itemid={1}'.format(
                    args.itemid
                   ,args.new_source))
            hflpub = publisher.HostedFeatureLayerPublisher(org
                                                          ,args.itemid)
            logging.info(
                'swap-view publisher init completed view_itemid={0} '
                'source_itemid={1}'.format(
                    args.itemid
                   ,args.new_source))

            logging.info(
                'swap-view operation starting view_itemid={0} '
                'source_itemid={1} source_index={2} view_index={3}'.format(
                    args.itemid
                   ,args.new_source
                   ,args.source_index
                   ,args.index))
            result = hflpub.swap_view(args.index
                                     ,args.new_source
                                     ,args.source_index)
            logging.info(
                'swap-view operation completed view_itemid={0} '
                'source_itemid={1} source_index={2} view_index={3}'.format(
                    args.itemid
                   ,args.new_source
                   ,args.source_index
                   ,args.index))

        logging.info('result evaluation starting itemid={0}'.format(
            args.itemid))
        if _result_ok(result):
            logging.info('Operation succeeded: {0}'.format(result))
            logging.info('result evaluation completed itemid={0}'.format(
                args.itemid))
            logging.info('main completed operation={0} itemid={1}'.format(
                args.operation
               ,args.itemid))
            sys.exit(0)

        logging.error('Operation failed: {0}'.format(result))
        logging.info('result evaluation completed itemid={0}'.format(
            args.itemid))
        logging.info('main completed operation={0} itemid={1}'.format(
            args.operation
           ,args.itemid))
        sys.exit(1)

    except (publisher.HostedFeatureLayerOverwriteError
           ,publisher.HostedFeatureLayerSwapViewError
           ,ValueError
           ,FileNotFoundError
           ,ImportError
           ,OSError) as e:
        logging.exception(e)
        sys.exit(1)
    except Exception as e:
        logging.exception(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
