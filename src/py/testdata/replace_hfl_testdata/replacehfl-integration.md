### Replace Hosted Feature Layer: Manual Integration Test

1. As personal user, set up 2 hosted feature layers.

2. Boroughs are fun and simple

```sql
select 
	a.boroname as borough
   ,sdo_cs.transform(SDO_GEOM.SDO_CENTROID(a.shape, 0.005),4326).sdo_point.x as lon
   ,sdo_cs.transform(SDO_GEOM.SDO_CENTROID(a.shape, 0.005),4326).sdo_point.y as lat
from cscl_pub.borough a
```

3. Load two hosted feature layers

The SQL above generates the csvs in this directory. Borough_pt_green.csv has been manually tweaked to move Brooklyn about 1/2 mile to the west. From Flatbush Ave to west of Ocean Ave. This will help us visualize updates.


    src\py\testdata\replace_hfl_testdata\borough_pt_blue.csv    
    
    -> load to borough_pt_blue hosted feature layer
    
    src\py\testdata\replace_hfl_testdata\borough_pt_green.csv  
    
    -> load to borough_pt_green hosted feature layer


3. Set up one hosted feature layer view initially set to blue:

    borough_pt_bk_vw 


## The manual integration test as stiched together python calls

1. Open and authenticate ArcGIS Pro

2. Initialize log, proxy, and pythonpath

```shell
> set TARGETLOGDIR=C:\gis\agol_pub\geodatabase-scripts\logs\dev\replace_hfl_test
> set PROXY=xxx
> set PYTHONPATH=C:\gis\agol_pub\src\py;%PYTHONPATH%
```

### BLUE2GREEN 
    
Overwrite green signature:

    python replace-hfl.py overwrite <borough_pt_green_itemid> C:\gis\agol_pub\src\py\testdata\replace_hfl_testdata\borough_pt_green.csv

Overwrite green actual:

    C:\Users\%USERNAME%\AppData\Local\Programs\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe replace-hfl.py overwrite ff33d8e4caa2463b8cffecaf9d063941 C:\gis\agol_pub\src\py\testdata\replace_hfl_testdata\borough_pt_green.csv

Swap blue to green signature

    python replace-hfl.py swap-view <borough_pt_bk_vw_itemid> 0 <borough_pt_green_itemid>

Swap blue to green actual

    C:\Users\%USERNAME%\AppData\Local\Programs\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe replace-hfl.py swap-view 597b8119f0544370b382c3b8028c5e09 0 ff33d8e4caa2463b8cffecaf9d063941

### GREEN2BLUE

Overwrite blue signature:

    python replace-hfl.py overwrite <borough_pt_blue_itemid> C:\gis\agol_pub\src\py\testdata\replace_hfl_testdata\borough_pt_blue.csv

Overwrite blue actual:

    C:\Users\%USERNAME%\AppData\Local\Programs\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe replace-hfl.py overwrite affa7c08c21d4eccb0e7b769781da0eb C:\gis\agol_pub\src\py\testdata\replace_hfl_testdata\borough_pt_blue.csv

Swap green to blue signature:

    python replace-hfl.py swap-view <borough_pt_bk_vw_itemid> 0 <borough_pt_blue_itemid>

Swap green to blue actual:

    C:\Users\%USERNAME%\AppData\Local\Programs\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe replace-hfl.py swap-view 597b8119f0544370b382c3b8028c5e09 0 affa7c08c21d4eccb0e7b769781da0eb
