# agol_pub

Simple wrappers to publish data to ArcGIS Online.  Friends these are our wrappers, our rules, the trick is never to be afraid.

We will lovingly wrap [these wrappers](https://developers.arcgis.com/python/latest/api-reference/arcgis.html) of REST calls.


## Requirements

1. ArcGIS Pro installed (ie python _import_ _arcgis_)
2. Authentication — scripts use whichever of these is available:
   - `NYCMAPSUSER` + `NYCMAPSCREDS` environment variables (service account / unattended)
   - ArcGIS Pro open and signed in — used automatically when the variables above are not set
3. QA requires _import_ _arcpy_

Optional environment variables used by all scripts:

| Variable | Purpose | Default |
|---|---|---|
| `PROXY` | HTTP/HTTPS proxy, e.g. `http://host:port` | none |
| `TARGETLOGDIR` | Directory for log files | system temp |

## Replace a File Geodatabase

Copy geodatabase-scripts\sample-replace-cscl-gdb.bat out to a scripts directory, rename it, and update the environmentals.

```shell
C:\gis\geodatabase-scripts>sample-replace-cscl-gdb.bat
``` 

#### Replace file geodatabase python script

```
usage: replace-cscl-gdb.py [-h] srcgdb targetgdbname targetitemid tempdir

Replace a file geodatabase in ArcGIS Online

positional arguments:
  srcgdb         Local file geodatabase
  targetgdbname  File geodatabase name in ArcGIS Online
  targetitemid   Item id in ArcGIS Online
  tempdir        A local temp directory

options:
  -h, --help     show this help message and exit
```

#### QA file geodatabase python script

```
usage: replace-cscl-qa.py [-h] pitemid pgdbname ptempdir pzipmb

QA a file geodatabase in ArcGIS Online

positional arguments:
  pitemid     Item id in ArcGIS Online
  pgdbname    File geodatabase name
  ptempdir    A local temp directory
  pzipmb      Expected geodatabase MB zipped

options:
  -h, --help  show this help message and exit
```

## Hosted Feature Layer Operations

Use `replace-hfl.py` for hosted feature layer operations.

```
usage: replace-hfl.py [-h] {overwrite,swap-view} ...

positional arguments:
  {overwrite,swap-view}
    overwrite           Overwrite a hosted feature layer with a local CSV
    swap-view           Call FeatureLayerCollection.manager.swap_view()

options:
  -h, --help            show this help message and exit
```

Examples:

```shell
>python replace-hfl.py overwrite <itemid> D:\data\points.csv
> rem in both cases below 0 is view index
>python replace-hfl.py swap-view <itemid> 0 <new_source>
> rem rare signature with source index greater than 0
>python replace-hfl.py swap-view <itemid> 0 <new_source> --source-index 1
```

## Test The Code In This Repository

#### Run tests with your single signon user

1. Open ArcGIS Pro 
2. Authenticate to your ArcGIS Online organization
3. Keep ArcGIS Pro open
4. Optional: Update the proxy info in testall.bat
5. Execute testall.bat

Some tests are mocked.  But we are not that fancy and we keep it real so some tests expect a dummy item to exist in the NYCMaps ArcGIS Online organization. 

```shell
C:\gis\agol_pub>testall.bat
```