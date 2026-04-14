REM refresh a hosted feature layer, then swap the view source
REM statefile tracks which color is next, blue or green
REM if overwrite fails the color returned is unchanged; next time retry
REM if swap fails, same thing: retry the same color and swap
REM if no state file exists, state_manager initializes blue to green
set GREENITEMID=xxxxxxxxxxxxxxxx
set BLUEITEMID=xxxxxxxxxxxxxxxxx
set VIEWITEMID=xxxxxxxxxxxxxxxxx
rem set these if not authenticating to ArcGIS Online with ArcGIS Pro
rem set NYCMAPSUSER=xxx.xxx.xxxx
rem set NYCMAPSCREDS=xxxxxxx
set NOTIFY=xxx@xxx.xxx.xxx
set NOTIFYFROM=xxx@xxx.xxx.xxx
set SMTPFROM=xxxx.xxxx
set PROXY=http://xxxx.xxxx:xxxx
set BASEPATH=X:\gis
set PYTHON1=C:\Progra~1\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe
set PYTHON2=C:\Users\%USERNAME%\AppData\Local\Programs\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe
if exist "%PYTHON1%" (
    set PROPY=%PYTHON1%
) else if exist "%PYTHON2%" (
    set PROPY=%PYTHON2%
) 
set AGOLPUB=%BASEPATH%\agol_pub
REM assumes manual creation of geodatabase-scripts\statefiles\
set STATEFILE=%AGOLPUB%\geodatabase-scripts\statefiles\state-%VIEWITEMID%.json
set TARGET_COLOR=
REM Get target (will be "green" or "blue")
for /f "tokens=*" %%A in (
  '%PROPY% %AGOLPUB%\src\py\state_manager.py get-target %STATEFILE%'
) do set TARGET_COLOR=%%A
echo Target color: %TARGET_COLOR%
if "%TARGET_COLOR%"=="green" (
  set TARGETITEMID=%GREENITEMID%
) else (
  set TARGETITEMID=%BLUEITEMID%
)
rem csv source is out of scope for agol_pub
set CSV=X:\xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\xxxxxxxxxxx_%TARGET_COLOR%.csv
set TARGETLOGDIR=%BASEPATH%\geodatabase-scripts\logs\xxx\xxxxxxxxxxxxxxxxxxxxx
set BATLOG=%TARGETLOGDIR%\xxxxxxxxxxxxxxxxxxxxxxxxxxxxx_to_%TARGET_COLOR%.log
set PYTHONPATH0=%PYTHONPATH%
set PYTHONPATH=%AGOLPUB%\src\py;%PYTHONPATH%
echo starting swap to %TARGET_COLOR% on %date% at %time% > %BATLOG%
%PROPY% %AGOLPUB%\replace-hfl.py overwrite ^
                                 %TARGETITEMID% ^
                                 %CSV%
if errorlevel 1 (
  %PROPY% %AGOLPUB%\src\py\state_manager.py set-failed %STATEFILE%
  echo. >> %BATLOG% && echo Overwrite failed on %date% at %time%. Not swapping view >> %BATLOG%
  echo 
  %PROPY% %AGOLPUB%\notify.py "Failed to overwrite %TARGET_COLOR% HFL %TARGETITEMID%" %NOTIFY% "replace-hfl-%TARGETITEMID%"
  set PYTHONPATH=%PYTHONPATH0%
  exit /b 1
)
echo. >> %BATLOG% && echo Swapping view %VIEWITEMID% to point to %TARGETITEMID% >> %BATLOG%
%PROPY% %AGOLPUB%\replace-hfl.py swap-view ^
                                 %VIEWITEMID% ^
                                 0 ^
                                 %TARGETITEMID%
if errorlevel 1 (
  %PROPY% %AGOLPUB%\src\py\state_manager.py set-failed %STATEFILE%
  echo. >> %BATLOG% && echo Swap failed on %date% at %time%. Investigate and decide rollback. >> %BATLOG%
  echo 
  %PROPY% %AGOLPUB%\notify.py "Failed to swap view %VIEWITEMID% to %TARGET_COLOR%" %NOTIFY% "replace-hfl-%VIEWITEMID%"
  set PYTHONPATH=%PYTHONPATH0%
  exit /b 1
)
%PROPY% %AGOLPUB%\src\py\state_manager.py set-success %STATEFILE% %TARGET_COLOR%
echo. >> %BATLOG% && echo Success: %TARGET_COLOR% %TARGETITEMID% overwritten and view %VIEWITEMID% now swapped to %TARGET_COLOR%. >> %BATLOG%
set PYTHONPATH=%PYTHONPATH0%