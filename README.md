# agol_pub

Simple wrappers to publish data to ArcGIS Online.  Friends these are our wrappers, our rules, the trick is never to be afraid.

We will lovingly wrap [these wrappers](https://developers.arcgis.com/python/latest/api-reference/arcgis.html) of REST calls.


## Requirements

1. ArcGIS Pro 3.5+ installed (ie python _import_ _arcgis_)
2. Authentication — scripts use whichever of these is available:
   - `NYCMAPSUSER` + `NYCMAPSCREDS` environment variables (service account / unattended)
   - ArcGIS Pro open and signed in — used automatically when the variables above are not set

Optional environment variables used by all scripts:

| Variable | Purpose | Default |
|---|---|---|
| `PROXY` | HTTP/HTTPS proxy, e.g. `http://host:port` | none |
| `TARGETLOGDIR` | Directory for log files | system temp |

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

### Hosted Feature Layer Sample Scripts

See geodatabase-scripts\sample-bluegreen.bat

## Group Membership Report

Use `group-members-report.py` to export group member details to a text file (tab-delimited). See also geodatabase-scripts\sample-group-report.bat.

```
usage: group-members-report.py [-h] [--url URL] groupid outfile

Write an ArcGIS Online group membership report to text

positional arguments:
  groupid     ArcGIS Online group id
  outfile     Output text file path

options:
  -h, --help  show this help message and exit
  --url URL   ArcGIS Online organization url
```

Example:

```shell
>python group-members-report.py <groupid> D:\reports\group-members.txt
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