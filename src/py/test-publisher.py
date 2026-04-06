import unittest
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

from arcgis.gis import GIS
import organization
import publisher


def _get_proxy_config():

    if 'PROXY' not in os.environ:
        return None

    return {
        'http': os.environ['PROXY']
       ,'https': os.environ['PROXY']
    }


def _connect_pro_gis():

    proxy = _get_proxy_config()
    if proxy is None:
        return GIS("pro")

    return GIS("pro"
              ,proxy=proxy)


def _print_pro_auth_context(gis):

    portal = getattr(gis.properties
                    ,'portalName'
                    ,getattr(gis
                            ,'url'
                            ,'unknown-portal'))
    user_obj = getattr(gis.users
                      ,'me'
                      ,None)
    user = getattr(user_obj
                  ,'username'
                  ,'unknown-user')
    print('GIS("pro") authenticated as {0} on {1}'.format(user
                                                           ,portal))

class PublishTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(self):

        # this is a dummy item created under the nycmaps test account
        # we could write a creation method
        # but doubtful we will ever create items from code
        self.testitemid = "a8d31a8f63b74b5f893cc675ea7419f0"
        self.tempdirctx = tempfile.TemporaryDirectory()
        self.tempdir = Path(self.tempdirctx.name)

        if 'NYCMAPSUSER' in os.environ and 'NYCMAPSCREDS' in os.environ:
            self.testuser  = os.environ['NYCMAPSUSER']
            self.testcreds = os.environ['NYCMAPSCREDS']
            self.org = organization.Organization(self.testuser
                                ,self.testcreds)
        else:
            try:
                gis = _connect_pro_gis()
                _print_pro_auth_context(gis)
                self.org = organization.Organization(gis=gis)
            except Exception as e:
                raise unittest.SkipTest(
                    'Unable to authenticate with GIS("pro"). '
                    'Open ArcGIS Pro, sign in, and verify network/proxy. '
                    'Original error: {0}'.format(e))
        
        self.pubgdb = publisher.PublishedItem(self.org
                                             ,self.testitemid)

        self.testdatadir = os.path.join(os.path.dirname(os.path.abspath(__file__))
                                       ,'testdata')
        
        self.testgdb = os.path.join(self.testdatadir
                                   ,'sample.gdb')
        
        self.testemptygdb = os.path.join(self.testdatadir
                                        ,'emptysample'
                                        ,'sample.gdb')
        
        self.testemptydiffnamegdb = os.path.join(self.testdatadir
                                                ,'emptysample'
                                                ,'emptysamplewithdiffname.gdb')
        
        self.nonexistentgdb = os.path.join(self.testdatadir
                                          ,'bad.gdb')

        self.testgdbwithlocks = os.path.join(self.testdatadir
                                            ,'samplewithlocks.gdb')

        self.localgdb = publisher.LocalGeodatabase(self.testgdb)
        self.emptylocalgdb = publisher.LocalGeodatabase(self.testemptygdb)
        self.emptydiffnamelocalgdb = publisher.LocalGeodatabase(
            self.testemptydiffnamegdb)
        self.nonexistentlocalgdb = publisher.LocalGeodatabase(
            self.nonexistentgdb)
        self.localgdbwithlocks = publisher.LocalGeodatabase(
            self.testgdbwithlocks)

        self.localpub = publisher.PublishWorkflow(self.localgdb)
        self.emptylocalpub = publisher.PublishWorkflow(self.emptylocalgdb)
        self.emptydiffnamelocalpub = publisher.PublishWorkflow(
            self.emptydiffnamelocalgdb)
        self.nonexistentlocalpub = publisher.PublishWorkflow(
            self.nonexistentlocalgdb)
        self.localpubwithlocks = publisher.PublishWorkflow(
            self.localgdbwithlocks)

    def tearDown(self):

        self.localpub.clean()
        self.emptylocalpub.clean()
        self.emptydiffnamelocalpub.clean()
        self.localpubwithlocks.clean()

    @classmethod
    def tearDownClass(self):
        self.tempdirctx.cleanup()

    def test_adescribe(self):

        try:
            self.pubgdb.describe()
        except Exception as e:
            self.fail("decribe raised {0}".format(e))

    def test_blocalgdbzip(self):

        self.localpub.zip(self.tempdir)

        self.assertTrue(os.path.isfile(self.localpub.zipped))

        self.localpub.clean()
        self.assertFalse(os.path.isfile(self.localpub.zipped))

    def test_clocalgdbrenamezip(self):

        self.localpub.renamezip(self.tempdir
                               ,'renamesample.gdb')

        self.assertTrue(os.path.isfile(self.localpub.zipped))

        self.localpub.clean()
        self.assertFalse(os.path.isfile(self.localpub.zipped))
        self.assertFalse(os.path.isdir(self.localpub.renamed))
        self.assertTrue(not any(Path(self.tempdir).iterdir()))

    def test_dreplaceitem(self):

        self.localpub.zip(self.tempdir)

        self.assertTrue(self.pubgdb.replace(self.localpub.zipped))

        self.localpub.clean()
        self.assertFalse(os.path.isfile(self.localpub.zipped))

    def test_edownload(self):

        self.pubgdb.download(self.tempdir)

        self.assertTrue(os.path.isfile(os.path.join(self.tempdir
                                                   ,'sample.gdb.zip')))
        
        self.pubgdb.clean()
        self.assertFalse(os.path.isfile(self.pubgdb.zipped)) 
        
    def test_fdownloadandreplace(self):

        # download samplegdb.zip with stuff in it
        # replace with empty samplegdb.zip
        # download empty samplegdb.zip
        # test that the file sizes tell us this is working

        # download sample.gdb.zip and get its size
        self.pubgdb.download(self.tempdir)
        big = os.path.getsize(os.path.join(self.tempdir
                                          ,'sample.gdb.zip'))
        
        # a downloaded gdb is implicitly a local gdb?
        self.pubgdb.clean()
        self.assertFalse(os.path.isfile(self.pubgdb.zipped))

        # zip up emptygdb and publish it
        self.emptylocalpub.zip(self.tempdir)
        self.assertTrue(self.pubgdb.replace(self.emptylocalpub.zipped))
        
        self.emptylocalpub.clean()
        self.assertFalse(os.path.isfile(self.emptylocalpub.zipped))

        # download empty samplegdb.zip and get its size
        self.pubgdb.download(self.tempdir)
        small = os.path.getsize(os.path.join(self.tempdir
                                            ,'sample.gdb.zip'))
        
        self.pubgdb.clean()        
        self.assertFalse(os.path.isfile(self.emptylocalpub.zipped))

        # re-publish the original non-empty samplegdb.zip
        self.localpub.zip(self.tempdir)
        self.assertTrue(self.pubgdb.replace(self.localpub.zipped))
        
        self.localpub.clean()
        self.assertFalse(os.path.isfile(self.localpub.zipped))
        self.assertFalse(os.path.isdir(self.localpub.renamed))

        self.assertTrue(big > small)

    def test_gdownloadandreplacediffname(self):

        # download samplegdb.zip with stuff in it
        # replace with emptysamplewithdiffname 
        # renamed as samplegdb.zip
        # download empty samplegdb.zip
        # test that the file sizes tell us this is working

        # download sample.gdb.zip and get its size
        self.pubgdb.download(self.tempdir)
        big = os.path.getsize(os.path.join(self.tempdir
                                          ,'sample.gdb.zip'))
        
        self.pubgdb.clean()
        self.assertFalse(os.path.isfile(self.pubgdb.zipped))

        # zip up emptygdb and publish it
        self.emptydiffnamelocalpub.renamezip(self.tempdir
                            ,'sample.gdb')
        self.assertTrue(self.pubgdb.replace(self.emptydiffnamelocalpub.zipped))
        
        self.emptydiffnamelocalpub.clean()
        self.assertFalse(os.path.isfile(self.emptydiffnamelocalpub.zipped))
        self.assertFalse(os.path.isfile(self.emptydiffnamelocalpub.renamed))

        # download empty samplegdb.zip and get its size
        self.pubgdb.download(self.tempdir)
        small = os.path.getsize(os.path.join(self.tempdir
                                            ,'sample.gdb.zip'))
        
        self.pubgdb.clean()
        self.assertFalse(os.path.isfile(self.emptylocalpub.zipped))

        # re-publish the original non-empty samplegdb.zip
        self.localpub.zip(self.tempdir)
        self.assertTrue(self.pubgdb.replace(self.localpub.zipped))
        
        self.localpub.clean()
        self.assertFalse(os.path.isfile(self.localpub.zipped))

        self.assertTrue(big > small)

    def test_hzipnesting(self):
        
        self.localpub.renamezip(self.tempdir
                       ,'renamesample.gdb')

        self.assertTrue(os.path.isfile(self.localpub.zipped))

        self.localpub.unzip(self.tempdir)
        self.assertTrue(os.path.isdir(self.localpub.unzipped))

        self.assertTrue(os.path.isdir(os.path.join(self.tempdir
                                                  ,'renamesample.gdb')))

        self.localpub.clean()
        self.assertFalse(os.path.isfile(self.localpub.zipped))
        self.assertFalse(os.path.isdir(self.localpub.renamed))
        self.assertFalse(os.path.isdir(self.localpub.unzipped))

        # this is the test that the nesting and cleanup are good
        # unzip should not leave a000001.freelist a00001.gdbindexes etc
        # at the top of the tempdir. check that tempdir is empty
        self.assertTrue(not any(Path(self.tempdir).iterdir()))

    def test_irenamezipfail(self):

        with self.assertRaises(FileNotFoundError) as context:
            self.nonexistentlocalpub.renamezip(self.tempdir
                                              ,'renamesample.gdb')
        self.assertTrue(str(context.exception).startswith, "File not found")

    def test_jrenamezipwithlocks(self):

        self.localpubwithlocks.renamezip(self.tempdir
                        ,'renamesamplewithlocks.gdb')

        self.assertTrue(os.path.isfile(self.localpubwithlocks.zipped))
        self.assertIs(self.localpubwithlocks.has_locks(), False)

        self.localpubwithlocks.clean()
        self.assertFalse(os.path.isfile(self.localpubwithlocks.zipped))
        self.assertFalse(os.path.isdir(self.localpubwithlocks.renamed))
        self.assertTrue(not any(Path(self.tempdir).iterdir()))


class HostedFeatureLayerPublisherTestCase(unittest.TestCase):

    def test_localcsv_valid(self):

        with tempfile.TemporaryDirectory() as td:
            csv_path = os.path.join(td
                                   ,'sample.csv')
            with open(csv_path
                     ,'w'
                     ,encoding='utf-8') as f:
                f.write('a,b\n1,2\n')

            localcsv = publisher.LocalCsv(csv_path)
            self.assertEqual(localcsv.csv
                            ,csv_path)

    def test_localcsv_bad_extension(self):

        with tempfile.TemporaryDirectory() as td:
            txt_path = os.path.join(td
                                   ,'sample.txt')
            with open(txt_path
                     ,'w'
                     ,encoding='utf-8') as f:
                f.write('a,b\n1,2\n')

            with self.assertRaises(ValueError):
                publisher.LocalCsv(txt_path)

    def test_localcsv_missing_file(self):

        with self.assertRaises(FileNotFoundError):
            publisher.LocalCsv(r'C:\does-not-exist\sample.csv')

    @patch('publisher.PublishedItem')
    def test_featurelayercollection_not_available(self
                                                 ,mock_published_item):

        original = publisher.FeatureLayerCollection

        with tempfile.TemporaryDirectory() as td:
            csv_path = os.path.join(td
                                   ,'sample.csv')
            with open(csv_path
                     ,'w'
                     ,encoding='utf-8') as f:
                f.write('a,b\n1,2\n')

            try:
                publisher.FeatureLayerCollection = None
                with self.assertRaises(ImportError):
                    publisher.HostedFeatureLayerPublisher(MagicMock()
                                                         ,'abc123'
                                                         ,csv_path)
            finally:
                publisher.FeatureLayerCollection = original

        # ImportError should occur before PublishedItem is used.
        mock_published_item.assert_not_called()

    @patch('publisher.FeatureLayerCollection')
    @patch('publisher.PublishedItem')
    def test_overwrite_success(self
                              ,mock_published_item
                              ,mock_flc):

        with tempfile.TemporaryDirectory() as td:
            csv_path = os.path.join(td
                                   ,'sample.csv')
            with open(csv_path
                     ,'w'
                     ,encoding='utf-8') as f:
                f.write('a,b\n1,2\n')

            existing = MagicMock()
            mock_published_item.return_value.existingitem = existing
            mock_published_item.return_value.id = 'abc123'

            manager = MagicMock()
            manager.overwrite.return_value = {'success': True}

            flc_obj = MagicMock()
            flc_obj.manager = manager
            mock_flc.fromitem.return_value = flc_obj

            overwritepub = publisher.HostedFeatureLayerPublisher(MagicMock()
                                                                ,'abc123'
                                                                ,csv_path)
            result = overwritepub.overwrite()

            mock_flc.fromitem.assert_called_once_with(existing)
            manager.overwrite.assert_called_once_with(csv_path)
            self.assertEqual(result
                            ,{'success': True})

    @patch('publisher.FeatureLayerCollection')
    @patch('publisher.PublishedItem')
    def test_overwrite_wraps_error(self
                                  ,mock_published_item
                                  ,mock_flc):

        with tempfile.TemporaryDirectory() as td:
            csv_path = os.path.join(td
                                   ,'sample.csv')
            with open(csv_path
                     ,'w'
                     ,encoding='utf-8') as f:
                f.write('a,b\n1,2\n')

            existing = MagicMock()
            mock_published_item.return_value.existingitem = existing
            mock_published_item.return_value.id = 'abc123'

            manager = MagicMock()
            manager.overwrite.side_effect = RuntimeError('boom')

            flc_obj = MagicMock()
            flc_obj.manager = manager
            mock_flc.fromitem.return_value = flc_obj

            overwritepub = publisher.HostedFeatureLayerPublisher(MagicMock()
                                                                ,'abc123'
                                                                ,csv_path)

            with self.assertRaises(publisher.HostedFeatureLayerOverwriteError):
                overwritepub.overwrite()

    @patch('publisher.FeatureLayerCollection')
    @patch('publisher.PublishedItem')
    def test_fromitem_none_raises(self
                                 ,mock_published_item
                                 ,mock_flc):

        with tempfile.TemporaryDirectory() as td:
            csv_path = os.path.join(td
                                   ,'sample.csv')
            with open(csv_path
                     ,'w'
                     ,encoding='utf-8') as f:
                f.write('a,b\n1,2\n')

            mock_published_item.return_value.existingitem = MagicMock()
            mock_flc.fromitem.return_value = None

            with self.assertRaises(ValueError):
                publisher.HostedFeatureLayerPublisher(MagicMock()
                                                     ,'abc123'
                                                     ,csv_path)

    @patch('publisher.FeatureLayerCollection')
    @patch('publisher.PublishedItem')
    def test_overwrite_requires_csv(self
                                   ,mock_published_item
                                   ,mock_flc):

        existing = MagicMock()
        mock_published_item.return_value.existingitem = existing
        mock_published_item.return_value.id = 'abc123'

        flc_obj = MagicMock()
        mock_flc.fromitem.return_value = flc_obj

        overwritepub = publisher.HostedFeatureLayerPublisher(MagicMock()
                                                            ,'abc123')

        with self.assertRaises(ValueError):
            overwritepub.overwrite()

    @patch('publisher.FeatureLayerCollection')
    @patch('publisher.PublishedItem')
    def test_swap_view_success(self
                              ,mock_published_item
                              ,mock_flc):

        existing = MagicMock()
        source_layer = MagicMock()
        source_existing = MagicMock()
        source_existing.layers = [source_layer]

        view_item = MagicMock()
        view_item.existingitem = existing
        view_item.id = 'view123'

        source_item = MagicMock()
        source_item.existingitem = source_existing
        source_item.id = 'source123'

        mock_published_item.side_effect = [view_item, source_item]

        manager = MagicMock()
        manager.swap_view.return_value = {'success': True}

        flc_obj = MagicMock()
        flc_obj.manager = manager
        mock_flc.fromitem.return_value = flc_obj

        viewpub = publisher.HostedFeatureLayerPublisher(MagicMock()
                                                       ,'view123')
        result = viewpub.swap_view('0'
                                  ,'source123')

        manager.swap_view.assert_called_once_with(0
                                                 ,source_layer)
        self.assertEqual(result
                        ,{'success': True})

    @patch('publisher.FeatureLayerCollection')
    @patch('publisher.PublishedItem')
    def test_swap_view_success_with_source_index(self
                                                ,mock_published_item
                                                ,mock_flc):

        existing = MagicMock()
        source_layer_0 = MagicMock()
        source_layer_1 = MagicMock()
        source_existing = MagicMock()
        source_existing.layers = [source_layer_0, source_layer_1]

        view_item = MagicMock()
        view_item.existingitem = existing
        view_item.id = 'view123'

        source_item = MagicMock()
        source_item.existingitem = source_existing
        source_item.id = 'source123'

        mock_published_item.side_effect = [view_item, source_item]

        manager = MagicMock()
        manager.swap_view.return_value = {'success': True}

        flc_obj = MagicMock()
        flc_obj.manager = manager
        mock_flc.fromitem.return_value = flc_obj

        viewpub = publisher.HostedFeatureLayerPublisher(MagicMock()
                                                       ,'view123')
        result = viewpub.swap_view('0'
                                  ,'source123'
                                  ,1)

        manager.swap_view.assert_called_once_with(0
                                                 ,source_layer_1)
        self.assertEqual(result
                        ,{'success': True})

    @patch('publisher.FeatureLayerCollection')
    @patch('publisher.PublishedItem')
    def test_swap_view_requires_source_layers(self
                                             ,mock_published_item
                                             ,mock_flc):

        existing = MagicMock()
        source_existing = MagicMock()
        source_existing.layers = []

        view_item = MagicMock()
        view_item.existingitem = existing
        view_item.id = 'view123'

        source_item = MagicMock()
        source_item.existingitem = source_existing
        source_item.id = 'source123'

        mock_published_item.side_effect = [view_item, source_item]

        flc_obj = MagicMock()
        mock_flc.fromitem.return_value = flc_obj

        viewpub = publisher.HostedFeatureLayerPublisher(MagicMock()
                                                       ,'view123')

        with self.assertRaises(ValueError):
            viewpub.swap_view('0'
                             ,'source123')

    @patch('publisher.FeatureLayerCollection')
    @patch('publisher.PublishedItem')
    def test_swap_view_wraps_error(self
                                  ,mock_published_item
                                  ,mock_flc):

        existing = MagicMock()
        source_layer = MagicMock()
        source_existing = MagicMock()
        source_existing.layers = [source_layer]

        view_item = MagicMock()
        view_item.existingitem = existing
        view_item.id = 'view123'

        source_item = MagicMock()
        source_item.existingitem = source_existing
        source_item.id = 'source123'

        mock_published_item.side_effect = [view_item, source_item]

        manager = MagicMock()
        manager.swap_view.side_effect = RuntimeError('boom')

        flc_obj = MagicMock()
        flc_obj.manager = manager
        mock_flc.fromitem.return_value = flc_obj

        viewpub = publisher.HostedFeatureLayerPublisher(MagicMock()
                                                       ,'view123')

        with self.assertRaises(publisher.HostedFeatureLayerSwapViewError):
            viewpub.swap_view('0'
                             ,'source123')


if __name__ == '__main__':
    unittest.main()
