try:
    from arcgis.gis import GIS
except ImportError as e: 
    raise ImportError("Failed to import arcgis. Check that you are calling from ArcGIS Pro python") from e

import os

# probably just one class here for now


def _proxy_from_env():

    if 'PROXY' not in os.environ:
        return None

    return {
        'http':  os.environ['PROXY']
       ,'https': os.environ['PROXY']
    }


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
