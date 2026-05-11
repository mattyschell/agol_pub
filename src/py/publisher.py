import os
import stat
import shutil
import copy
import json
import logging
from pathlib import Path

try:
    from arcgis.features import FeatureLayerCollection
except ImportError:
    FeatureLayerCollection = None

# generic ArcGIS Online publishing helpers live here.


class PublishWorkflowError(Exception):
    pass


class LockFilesPresentError(PublishWorkflowError):
    pass


class HostedFeatureLayerOverwriteError(PublishWorkflowError):
    pass


class HostedFeatureLayerSwapViewError(PublishWorkflowError):
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

        
class LocalCsv(object):

    def __init__(self
                ,filecsv):

        self.csv = filecsv
        self.csvname = os.path.basename(self.csv)
        self.csvpath = os.path.dirname(self.csv)

        if not self.csv.lower().endswith('.csv'):
            raise ValueError('Expected a .csv file, got {0}'.format(self.csv))

        if not os.path.isfile(self.csv):
            raise FileNotFoundError('CSV file not found: {0}'.format(self.csv))


class HostedFeatureLayerPublisher(object):

    def __init__(self
                ,org
                ,id
                ,csvinput=None):

        if FeatureLayerCollection is None:
            raise ImportError(
                'Failed to import arcgis.features.FeatureLayerCollection')

        self.item = PublishedItem(org
                                 ,id)

        self.localcsv = None
        if csvinput is not None:
            if isinstance(csvinput, LocalCsv):
                self.localcsv = csvinput
            else:
                self.localcsv = LocalCsv(csvinput)

        self.feature_layer_collection = FeatureLayerCollection.fromitem(
            self.item.existingitem)

        if self.feature_layer_collection is None:
            raise ValueError(
                'Item {0} is not a hosted feature layer collection'.format(id))

    def overwrite(self):

        if self.localcsv is None:
            raise ValueError('CSV input is required for overwrite()')

        try:
            return self.feature_layer_collection.manager.overwrite(
                self.localcsv.csv)
        except Exception as e:
            raise HostedFeatureLayerOverwriteError(
                'Failed to overwrite hosted feature layer {0} with {1}'.format(
                    self.item.id
                   ,self.localcsv.csv)) from e

    def _resolve_source_layer(self
                             ,new_source_id
                             ,source_index=0):

        source_item = PublishedItem(self.item.org
                                   ,new_source_id)
        source_layers = getattr(source_item.existingitem
                               ,'layers'
                               ,None)

        if not source_layers:
            raise ValueError(
                'Item {0} does not expose any feature layers'.format(
                    new_source_id))

        try:
            return source_layers[int(source_index)]
        except (IndexError, TypeError, ValueError) as e:
            raise ValueError(
                'Unable to resolve source layer index {0} for item {1}'.format(
                    source_index
                   ,new_source_id)) from e

    def _resolve_view_layer(self
                           ,index):

        view_layers = getattr(self.item.existingitem
                             ,'layers'
                             ,None)

        if not view_layers:
            raise ValueError(
                'Item {0} does not expose any view layers'.format(
                    self.item.id))

        try:
            return view_layers[int(index)]
        except (IndexError, TypeError, ValueError) as e:
            raise ValueError(
                'Unable to resolve view layer index {0} for item {1}'.format(
                    index
                   ,self.item.id)) from e

    def _properties_to_dict(self
                           ,properties):

        if properties is None:
            return {}

        if isinstance(properties, dict):
            return copy.deepcopy(properties)

        to_dict = getattr(properties
                         ,'to_dict'
                         ,None)
        if callable(to_dict):
            return copy.deepcopy(to_dict())

        # ArcGIS PropertyMap is dict-like but not a dict subclass;
        # dict() works on any mapping that supports keys().
        try:
            return copy.deepcopy(dict(properties))
        except (TypeError, ValueError):
            pass

        return {}

    def _capture_view_definition(self
                                ,index):

        logger = logging.getLogger(__name__)

        view_layer = self._resolve_view_layer(index)
        raw_properties = getattr(view_layer
                                ,'properties'
                                ,None)
        logger.info(
            '_capture_view_definition: item_id={0}, view_index={1}, '
            'properties_type={2}'.format(
                self.item.id
               ,index
               ,type(raw_properties).__name__))

        properties = self._properties_to_dict(raw_properties)

        snapshot = {}

        if 'definitionExpression' in properties:
            snapshot['definitionExpression'] = properties['definitionExpression']

        if 'viewDefinitionQuery' in properties:
            snapshot['viewDefinitionQuery'] = properties['viewDefinitionQuery']

        admin_info = properties.get('adminLayerInfo')
        if isinstance(admin_info, dict):
            view_layer_definition = admin_info.get('viewLayerDefinition')
            if isinstance(view_layer_definition, dict):
                snapshot['adminLayerInfo'] = {
                    'viewLayerDefinition': copy.deepcopy(view_layer_definition)
                }

        return snapshot

    def _restore_view_definition(self
                                ,index
                                ,snapshot):

        if not snapshot:
            return True

        view_layer = self._resolve_view_layer(index)
        update_definition_method = getattr(view_layer.manager
                                          ,'update_definition'
                                          ,None)

        if update_definition_method is None:
            raise HostedFeatureLayerSwapViewError(
                'update_definition is not available for view layer {0} '.format(
                    self.item.id) +
                'index {0}'.format(index))

        result = update_definition_method(snapshot)
        return result is not False

    def swap_view(self
                 ,index
                 ,new_source
                 ,source_index=0):

        logger = logging.getLogger(__name__)

        logger.info(
            'swap_view starting: item_id={0}, view_index={1}, '
            'source_item_id={2}, source_index={3}'.format(
                self.item.id
               ,index
               ,new_source
               ,source_index))

        source_layer = self._resolve_source_layer(new_source
                                                 ,source_index)
        preserved_definition = self._capture_view_definition(index)
        
        logger.info(
            'swap_view captured pre-swap definition: item_id={0}, '
            'view_index={1}, definition={2}'.format(
                self.item.id
               ,index
               ,json.dumps(preserved_definition, default=str)))

        try:
            swap_view_method = self.feature_layer_collection.manager.swap_view
        except AttributeError as e:
            raise HostedFeatureLayerSwapViewError(
                'swap_view is not available in this ArcGIS API environment '
                'for hosted feature layer {0}. '
                'Upgrade ArcGIS Pro/arcgis API or use a REST swapView '
                'fallback.'.format(self.item.id)) from e

        try:
            swap_result = swap_view_method(int(index)
                                          ,source_layer)
            logger.info(
                'swap_view completed: item_id={0}, view_index={1}, '
                'swap_result={2}'.format(
                    self.item.id
                   ,index
                   ,json.dumps(swap_result, default=str)))
        except Exception as e:
            raise HostedFeatureLayerSwapViewError(
                'Failed to swap view for hosted feature layer {0}'.format(
                    self.item.id)) from e

        logger.info(
            'swap_view restoring definition: item_id={0}, view_index={1}, '
            'restore_payload={2}'.format(
                self.item.id
               ,index
               ,json.dumps(preserved_definition, default=str)))

        try:
            restored = self._restore_view_definition(index
                                                    ,preserved_definition)
            logger.info(
                'swap_view restore completed: item_id={0}, view_index={1}, '
                'restore_result={2}'.format(
                    self.item.id
                   ,index
                   ,restored))
        except Exception as e:
            logger.error(
                'swap_view restore failed: item_id={0}, view_index={1}, '
                'error={2}'.format(
                    self.item.id
                   ,index
                   ,str(e)))
            raise HostedFeatureLayerSwapViewError(
                'Failed to restore view definition for hosted feature layer {0}'.format(
                    self.item.id)) from e

        if not restored:
            logger.error(
                'swap_view restore returned false: item_id={0}, '
                'view_index={1}'.format(
                    self.item.id
                   ,index))
            raise HostedFeatureLayerSwapViewError(
                'Failed to restore view definition for hosted feature layer {0}'.format(
                    self.item.id))

        current_definition = self._capture_view_definition(index)
        logger.info(
            'swap_view captured post-swap definition: item_id={0}, '
            'view_index={1}, definition={2}'.format(
                self.item.id
               ,index
               ,json.dumps(current_definition, default=str)))

        if current_definition != preserved_definition:
            logger.error(
                'swap_view definition drift detected: item_id={0}, '
                'view_index={1}, pre_swap={2}, post_swap={3}'.format(
                    self.item.id
                   ,index
                   ,json.dumps(preserved_definition, default=str)
                   ,json.dumps(current_definition, default=str)))
            raise HostedFeatureLayerSwapViewError(
                'View definition drift detected after swap for hosted feature '
                'layer {0}'.format(self.item.id))

        logger.info(
            'swap_view completed successfully: item_id={0}, view_index={1}, '
            'definition preserved'.format(
                self.item.id
               ,index))

        return swap_result


class pubitem(PublishedItem):
    pass

