import unittest
import os
from types import SimpleNamespace

from arcgis.gis import GIS
import organization


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

class OrganizationTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(self):

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

    @classmethod
    def tearDownClass(self):

        pass

    def test_adescribe(self):

        try:
            self.org.describe()
        except Exception as e:
            self.fail("decribe raised {0}".format(e))


class OrganizationInjectedGISTestCase(unittest.TestCase):

    def test_gis_supplied_uses_authenticated_user(self):

        gis = SimpleNamespace(
            url='https://example.maps.arcgis.com/'
           ,users=SimpleNamespace(
                me=SimpleNamespace(username='personal.user'))
           ,session=SimpleNamespace(
                auth=SimpleNamespace(token='test-token')))

        org = organization.Organization(gis=gis)

        self.assertEqual(org.user
                        ,'personal.user')
        self.assertIsNone(org.creds)
        self.assertEqual(org.url
                        ,'https://example.maps.arcgis.com/')
        self.assertEqual(org.token
                        ,'test-token')

if __name__ == '__main__':
    unittest.main()
