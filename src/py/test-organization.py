import unittest
import os

import organization

class OrganizationTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(self):

        self.testuser  = os.environ['NYCMAPSUSER']
        self.testcreds = os.environ['NYCMAPCREDS']

        self.org = organization.Organization(self.testuser
                            ,self.testcreds)

    @classmethod
    def tearDownClass(self):

        pass

    def test_adescribe(self):

        try:
            self.org.describe()
        except Exception as e:
            self.fail("decribe raised {0}".format(e))

if __name__ == '__main__':
    unittest.main()
