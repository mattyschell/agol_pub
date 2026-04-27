set GROUPID=abc.123
set OUTFILE=C:\Temp\abc123report.tsv
rem set these if not authenticating to ArcGIS Online with ArcGIS Pro
rem set NYCMAPSUSER=xxx.xxx.xxxx
rem set NYCMAPSCREDS=xxxxxxx
set PROXY=http://xxx.xxx:xxxx
set BASEPATH=X:\xxx
set PYTHON1=C:\Progra~1\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe
set PYTHON2=C:\Users\%USERNAME%\AppData\Local\Programs\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe
if exist "%PYTHON1%" (
    set PROPY=%PYTHON1%
) else if exist "%PYTHON2%" (
    set PROPY=%PYTHON2%
) 
set AGOLPUB=%BASEPATH%\agol_pub
set PYTHONPATH0=%PYTHONPATH%
set PYTHONPATH=%AGOLPUB%\src\py;%PYTHONPATH%
%PROPY% %AGOLPUB%\group-members-report.py %GROUPID% %OUTFILE%
set PYTHONPATH=%PYTHONPATH0%