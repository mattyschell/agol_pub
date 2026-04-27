try:
    from arcgis.gis import GIS
except ImportError as e: 
    raise ImportError("Failed to import arcgis. Check that you are calling from ArcGIS Pro python") from e

import os
from datetime import datetime
from datetime import timezone

# probably just one class here for now


def _proxy_from_env():

    if 'PROXY' not in os.environ:
        return None

    return {
        'http':  os.environ['PROXY']
       ,'https': os.environ['PROXY']
    }


def _normalize_last_login(last_login):

    if last_login is None:
        return None

    try:
        timestamp = int(last_login)
    except (TypeError, ValueError):
        return str(last_login)

    if timestamp <= 0:
        return None

    # ArcGIS values are generally milliseconds since epoch.
    if timestamp > 9999999999:
        timestamp = timestamp / 1000

    return datetime.fromtimestamp(timestamp
                                 ,tz=timezone.utc).isoformat()


class Organization(object):

    def __init__(self
                ,user=None
                ,creds=None
                ,url="https://nyc.maps.arcgis.com/"
                ,gis=None):

        self.user  = user
        self.creds = creds
        self.url   = url
        self.proxy = _proxy_from_env()

        if gis is not None:
            # development.
            # We passed in a gis, likely gis("pro") 
            # ArcGIS Pro is open and authenticated at runtime
            self.gis = gis
            self.user = self._get_gis_user(gis)
            self.creds = None
            self.url = getattr(gis
                              ,'url'
                              ,url)
        else:
            # production. a user with password
            self.gis = GIS(url
                          ,user
                          ,creds
                          ,proxy=self.proxy)

        self.token = self._get_gis_token(self.gis)

    @classmethod
    def from_env(cls
                ,url="https://nyc.maps.arcgis.com/"):

        user  = os.environ.get('NYCMAPSUSER')
        creds = os.environ.get('NYCMAPSCREDS')

        if user is not None and creds is None:
            raise ValueError(
                'NYCMAPSUSER is set but NYCMAPSCREDS is missing'
            )

        if user is not None:
            return cls(user, creds, url)

        return cls(gis=GIS('pro', proxy=_proxy_from_env()))

    def _get_gis_user(self
                     ,gis):

        gis_user = getattr(getattr(gis
                                  ,'users'
                                  ,None)
                          ,'me'
                          ,None)

        if gis_user is not None:
            username = getattr(gis_user
                              ,'username'
                              ,None)
            if username is not None:
                return username

        properties = getattr(gis
                            ,'properties'
                            ,None)
        property_user = getattr(properties
                               ,'user'
                               ,None)

        if property_user is not None:
            return getattr(property_user
                          ,'username'
                          ,None)

        return None

    def _get_gis_token(self
                      ,gis):

        session = getattr(gis
                         ,'session'
                         ,None)
        auth = getattr(session
                      ,'auth'
                      ,None)
        token = getattr(auth
                       ,'token'
                       ,None)

        if token is not None:
            return token

        connection = getattr(gis
                            ,'_con'
                            ,None)
        token = getattr(connection
                       ,'token'
                       ,None)

        if token is not None:
            return token

        return None

    def describe(self):
    
        items = {k: v for k, v in self.__dict__.items() if k != "creds"}
        width = max(len(k) for k in items)

        for var, value in items.items(): 
            print('{0} : {1}'.format(var.ljust(width)
                                    ,value))        


class GroupReporter(object):

    def __init__(self
                ,org):

        if org is None:
            raise ValueError('Organization is required')

        if getattr(org
                  ,'gis'
                  ,None) is None:
            raise ValueError('Organization.gis is required')

        self.org = org

    def _get_group(self
                  ,group_id):

        group = self.org.gis.groups.get(group_id)

        if group is None:
            raise ValueError('ArcGIS group not found for id {0}'.format(
                group_id))

        return group

    def _get_members(self
                    ,group):

        members = group.get_members()

        if members is None:
            return {}

        if not isinstance(members
                         ,dict):
            raise ValueError('Unexpected group member payload type {0}'.
                             format(type(members)))

        return members

    def _group_role(self
                   ,username
                   ,members):

        if username == members.get('owner'):
            return 'owner'

        if username in members.get('admins'
                                  ,[]):
            return 'admin'

        if username in members.get('users'
                                  ,[]):
            return 'member'

        return 'unknown'

    def _member_usernames(self
                         ,members):

        ordered = []

        owner = members.get('owner')
        if owner:
            ordered.append(owner)

        ordered.extend(members.get('admins'
                                ,[]))
        ordered.extend(members.get('users'
                                ,[]))

        deduped = []
        seen = set()
        for username in ordered:
            if not username or username in seen:
                continue
            seen.add(username)
            deduped.append(username)

        return deduped

    def _member_row(self
                   ,username
                   ,group_role):

        user = self.org.gis.users.get(username)

        if user is None:
            return {
                'username': username
               ,'user.fullName': None
               ,'user.email': None
               ,'user.role': None
               ,'user.lastLogin': None
               ,'group_role': group_role
            }

        full_name = getattr(user
                           ,'fullName'
                           ,None)
        if full_name is None:
            full_name = getattr(user
                               ,'full_name'
                               ,None)

        return {
            'username': username
           ,'user.fullName': full_name
           ,'user.email': getattr(user
                                 ,'email'
                                 ,None)
           ,'user.role': getattr(user
                                ,'role'
                                ,None)
           ,'user.lastLogin': _normalize_last_login(
                getattr(user
                       ,'lastLogin'
                       ,None))
           ,'group_role': group_role
        }

    def group_members_report(self
                            ,group_id):

        group = self._get_group(group_id)
        members = self._get_members(group)
        usernames = self._member_usernames(members)

        return [
            self._member_row(username
                            ,self._group_role(username
                                             ,members))
            for username in usernames
        ]

    @staticmethod
    def report_text(report_rows):

        fields = [
            'username'
           ,'user.fullName'
           ,'user.email'
           ,'user.role'
           ,'user.lastLogin'
           ,'group_role'
        ]

        lines = ['\t'.join(fields)]
        for row in report_rows:
            lines.append('\t'.join(
                '' if row.get(field) is None else str(row.get(field))
                for field in fields
            ))

        return '\n'.join(lines)

    @classmethod
    def write_report_text(cls
                         ,report_rows
                         ,outfile):

        text = cls.report_text(report_rows)

        with open(outfile
                 ,'w'
                 ,encoding='utf-8') as f:
            f.write(text)
            f.write('\n')
