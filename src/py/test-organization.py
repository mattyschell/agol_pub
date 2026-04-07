import unittest
import os
from types import SimpleNamespace

import organization


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

        try:
            self.org = organization.Organization.from_env()
            if 'NYCMAPSUSER' not in os.environ:
                _print_pro_auth_context(self.org.gis)
        except Exception as e:
            raise unittest.SkipTest(
                'Unable to authenticate. '
                'Open ArcGIS Pro, sign in, and verify network/proxy. '
                'Original error: {0}'.format(e))

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
