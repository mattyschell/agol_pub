rem set PROXY=http://xxxx.xxxx:xxxx
set PYTHON1=C:\Progra~1\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe
set PYTHON2=C:\Users\%USERNAME%\AppData\Local\Programs\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe
if exist "%PYTHON1%" (
    set PROPY=%PYTHON1%
) else if exist "%PYTHON2%" (
    set PROPY=%PYTHON2%
) 
REM "-W ignore" suppresses deprecation warnings from arcgis
CALL %PROPY% -W ignore .\src\py\test-organization.py
CALL %PROPY% -W ignore .\src\py\test-publisher.py
