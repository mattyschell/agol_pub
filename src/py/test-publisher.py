import unittest
import os
from pathlib import Path

import organization
import publisher

class PublishTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(self):

        # this is a dummy item created under the nycmaps test account
        # we could write a creation method
        # but doubtful we will ever create items from code
        self.testitemid = "a8d31a8f63b74b5f893cc675ea7419f0"

        self.testuser  = os.environ['NYCMAPSUSER']
        self.testcreds = os.environ['NYCMAPCREDS']
        self.tempdir = Path(os.environ['TEMP'])
        
        self.org = organization.Organization(self.testuser
                            ,self.testcreds)
        
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
        pass

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


if __name__ == '__main__':
    unittest.main()
