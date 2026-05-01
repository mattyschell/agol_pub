import os
import stat
import shutil
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

    def swap_view(self
                 ,index
                 ,new_source
                 ,source_index=0):

        source_layer = self._resolve_source_layer(new_source
                                                 ,source_index)

        try:
            swap_view_method = self.feature_layer_collection.manager.swap_view
        except AttributeError as e:
            raise HostedFeatureLayerSwapViewError(
                'swap_view is not available in this ArcGIS API environment '
                'for hosted feature layer {0}. '
                'Upgrade ArcGIS Pro/arcgis API or use a REST swapView '
                'fallback.'.format(self.item.id)) from e

        try:
            return swap_view_method(int(index)
                                   ,source_layer)
        except Exception as e:
            raise HostedFeatureLayerSwapViewError(
                'Failed to swap view for hosted feature layer {0}'.format(
                    self.item.id)) from e


class pubitem(PublishedItem):
    pass

