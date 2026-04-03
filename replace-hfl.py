# calling shell or bat must
# set AGOLPUB=D:\gis\agol-pub\src\py
# set PYTHONPATH=%PYTHONPATH%;%AGOLPUB%
# set NYCMAPSUSER=xxxx.xxx.xxx
# set NYCMAPCREDS=xxxxxx
import argparse
import logging
import os
import sys

import organization
import publisher


def _result_ok(result):

    if result is False or result is None:
        return False

    if isinstance(result, dict) and 'success' in result:
        return bool(result['success'])

    return True


def _organization_from_env():

    try:
        return organization.Organization(os.environ['NYCMAPSUSER']
                                        ,os.environ['NYCMAPCREDS'])
    except KeyError as e:
        raise ValueError('Missing required environment variable {0}'.format(e))


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

    logging.basicConfig(level=logging.INFO)

    try:

        org = _organization_from_env()

        if args.operation == 'overwrite':
            hflpub = publisher.HostedFeatureLayerPublisher(org
                                                          ,args.itemid
                                                          ,args.csvpath)
            result = hflpub.overwrite()
        else:
            hflpub = publisher.HostedFeatureLayerPublisher(org
                                                          ,args.itemid)
            result = hflpub.swap_view(args.index
                                     ,args.new_source
                                     ,args.source_index)

        if _result_ok(result):
            logging.info('Operation succeeded: {0}'.format(result))
            sys.exit(0)

        logging.error('Operation failed: {0}'.format(result))
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
