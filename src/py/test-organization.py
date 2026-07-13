import unittest
import os
import tempfile
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


class GroupReporterTestCase(unittest.TestCase):

    def _org_for_group_tests(self):

        users = {
            'owner.user': SimpleNamespace(
                fullName='Owner User'
               ,email='owner@example.com'
               ,role='org_admin'
               ,lastLogin=1714000000000)
           ,'admin.user': SimpleNamespace(
                fullName='Admin User'
               ,email='admin@example.com'
               ,role='org_user'
               ,lastLogin=1714000100000)
           ,'member.user': SimpleNamespace(
                fullName='Member User'
               ,email='member@example.com'
               ,role='org_user'
               ,lastLogin=-1)
        }

        group = SimpleNamespace(
            get_members=lambda: {
                'owner': 'owner.user'
               ,'admins': ['admin.user']
               ,'users': ['member.user', 'missing.user']
            }
        )

        gis = SimpleNamespace(
            groups=SimpleNamespace(
                get=lambda group_id: (
                    group if group_id == 'group-123' else None))
           ,users=SimpleNamespace(
                get=lambda username: users.get(username))
           ,session=SimpleNamespace(
                auth=SimpleNamespace(token='test-token')))

        return organization.Organization(gis=gis)

    def test_group_members_report_has_expected_fields(self):

        org = self._org_for_group_tests()
        reporter = organization.GroupReporter(org)

        report = reporter.group_members_report('group-123')

        self.assertEqual(len(report)
                        ,4)
        self.assertEqual(report[0]['username']
                        ,'owner.user')
        self.assertEqual(report[0]['group_role']
                        ,'owner')
        self.assertEqual(report[1]['group_role']
                        ,'admin')
        self.assertEqual(report[2]['group_role']
                        ,'member')
        self.assertEqual(report[3]['username']
                        ,'missing.user')
        self.assertIsNone(report[3]['user.email'])

    def test_group_members_report_retries_lookup_without_nyc_suffix(self):

        users = {
            'mschell@oti.nyc.gov': SimpleNamespace(
                fullName='Matthew Schell'
               ,email='mschell@oti.nyc.gov'
               ,role='City Editor'
               ,lastLogin=1714000000000)
        }

        group = SimpleNamespace(
            get_members=lambda: {
                'owner': 'owner.user'
               ,'admins': []
               ,'users': ['mschell@oti.nyc.gov_nyc']
            }
        )

        gis = SimpleNamespace(
            groups=SimpleNamespace(
                get=lambda group_id: (
                    group if group_id == 'group-123' else None))
           ,users=SimpleNamespace(
                get=lambda username: users.get(username))
           ,session=SimpleNamespace(
                auth=SimpleNamespace(token='test-token')))

        org = organization.Organization(gis=gis)
        reporter = organization.GroupReporter(org)

        report = reporter.group_members_report('group-123')

        self.assertEqual(report[1]['username']
                        ,'mschell@oti.nyc.gov_nyc')
        self.assertEqual(report[1]['user.email']
                        ,'mschell@oti.nyc.gov')
        self.assertEqual(report[1]['user.fullName']
                        ,'Matthew Schell')

    def test_group_members_report_enriches_partial_user_from_search(self):

        users_get = {
            'owner.user': SimpleNamespace(
                fullName='Owner User'
               ,email='owner@example.com'
               ,role='org_admin'
               ,lastLogin=1714000000000)
           ,'test_fake_esri_user': SimpleNamespace(
                username='test_fake_esri_user'
               ,fullName='Test NonGovernmentEmploye'
               ,email=None
               ,role=None
               ,lastLogin=None)
        }

        users_search = {
            'test_fake_esri_user': [
                SimpleNamespace(
                    username='test_fake_esri_user'
                   ,fullName='Test NonGovernmentEmploye'
                   ,email='test_fake_esri_user@example.com'
                   ,role='City Editor'
                   ,lastLogin=1714000200000)
            ]
        }

        group = SimpleNamespace(
            get_members=lambda: {
                'owner': 'owner.user'
               ,'admins': []
               ,'users': ['test_fake_esri_user']
            }
        )

        users_api = SimpleNamespace(
            get=lambda username: users_get.get(username)
           ,search=lambda query, max_users=10: users_search.get(query
                                                               ,[])
        )

        gis = SimpleNamespace(
            groups=SimpleNamespace(
                get=lambda group_id: (
                    group if group_id == 'group-123' else None))
           ,users=users_api
           ,session=SimpleNamespace(
                auth=SimpleNamespace(token='test-token')))

        org = organization.Organization(gis=gis)
        reporter = organization.GroupReporter(org)

        report = reporter.group_members_report('group-123')

        self.assertEqual(report[1]['username']
                        ,'test_fake_esri_user')
        self.assertEqual(report[1]['user.email']
                        ,'test_fake_esri_user@example.com')
        self.assertEqual(report[1]['user.role']
                        ,'City Editor')
        self.assertIsNotNone(report[1]['user.lastLogin'])

    def test_group_members_report_missing_group_raises(self):

        org = self._org_for_group_tests()
        reporter = organization.GroupReporter(org)

        with self.assertRaises(ValueError):
            reporter.group_members_report('missing-group')

    def test_report_text_contains_header_and_rows(self):

        org = self._org_for_group_tests()
        reporter = organization.GroupReporter(org)

        report = reporter.group_members_report('group-123')
        text = reporter.report_text(report)

        self.assertIn('username,user.fullName,user.email'
                     ,text)
        self.assertIn('owner.user,Owner User,owner@example.com'
                     ,text)
        self.assertIn('missing.user,,,,,member'
                     ,text)

    def test_write_report_text_writes_file(self):

        org = self._org_for_group_tests()
        reporter = organization.GroupReporter(org)

        report = reporter.group_members_report('group-123')

        with tempfile.TemporaryDirectory() as td:
            outfile = os.path.join(td
                                  ,'group-report.txt')
            reporter.write_report_text(report
                                      ,outfile)

            with open(outfile
                     ,'r'
                     ,encoding='utf-8') as f:
                text = f.read()

        self.assertIn('user.lastLogin,group_role\n'
                     ,text)
        self.assertIn('missing.user,,,,,member\n'
                     ,text)

if __name__ == '__main__':
    unittest.main()
