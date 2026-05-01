import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import patch

import publisher


class PublishedItemTestCase(unittest.TestCase):

    def _org(self
            ,item):

        return SimpleNamespace(
            gis=SimpleNamespace(
                content=SimpleNamespace(
                    get=MagicMock(return_value=item))))

    def test_init_requires_existing_item(self):

        org = self._org(None)

        with self.assertRaises(ValueError):
            publisher.PublishedItem(org
                                   ,'abc123')

    def test_describe_does_not_raise(self):

        existing = MagicMock()
        pubitem = publisher.PublishedItem(self._org(existing)
                                         ,'abc123')

        try:
            pubitem.describe()
        except Exception as e:
            self.fail('describe raised {0}'.format(e))

    def test_replace_calls_update(self):

        existing = MagicMock()
        existing.update.return_value = True
        pubitem = publisher.PublishedItem(self._org(existing)
                                         ,'abc123')

        result = pubitem.replace(r'C:\temp\sample.zip')

        existing.update.assert_called_once_with(data=r'C:\temp\sample.zip')
        self.assertTrue(result)

    def test_download_sets_zip_path(self):

        with tempfile.TemporaryDirectory() as td:
            zip_path = os.path.join(td
                                   ,'sample.zip')

            with open(zip_path
                     ,'w'
                     ,encoding='utf-8') as f:
                f.write('zip')

            existing = MagicMock()
            existing.download.return_value = zip_path
            pubitem = publisher.PublishedItem(self._org(existing)
                                             ,'abc123')

            pubitem.download(td)

            existing.download.assert_called_once_with(td)
            self.assertEqual(pubitem.zipped
                            ,zip_path)

    def test_download_requires_zip_result(self):

        existing = MagicMock()
        existing.download.return_value = r'C:\temp\sample.txt'
        pubitem = publisher.PublishedItem(self._org(existing)
                                         ,'abc123')

        with self.assertRaises(ValueError):
            pubitem.download(r'C:\temp')

    def test_clean_removes_downloaded_zip(self):

        with tempfile.TemporaryDirectory() as td:
            zip_path = os.path.join(td
                                   ,'sample.zip')

            with open(zip_path
                     ,'w'
                     ,encoding='utf-8') as f:
                f.write('zip')

            existing = MagicMock()
            pubitem = publisher.PublishedItem(self._org(existing)
                                             ,'abc123')
            pubitem.zipped = zip_path

            pubitem.clean()

            self.assertFalse(os.path.isfile(zip_path))
            self.assertEqual(pubitem.zipped
                            ,zip_path)


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
    def test_swap_view_missing_manager_method(self
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

        manager = MagicMock(spec=[])

        flc_obj = MagicMock()
        flc_obj.manager = manager
        mock_flc.fromitem.return_value = flc_obj

        viewpub = publisher.HostedFeatureLayerPublisher(MagicMock()
                                                       ,'view123')

        with self.assertRaises(publisher.HostedFeatureLayerSwapViewError) as cm:
            viewpub.swap_view('0'
                             ,'source123')

        self.assertIsInstance(cm.exception.__cause__
                             ,AttributeError)
        self.assertIn('not available'
                     ,str(cm.exception))

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


if __name__ == '__main__':
    unittest.main()
