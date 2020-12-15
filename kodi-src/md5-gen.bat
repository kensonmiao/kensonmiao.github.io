set "file=duboku\duboku.kodi.miaoo.cat\addon.xml"
call md5.bat "%file%" md5
echo %md5%>"..\kodi\duboku\addon.xml.md5"

set "file=iyueyu\iyueyu.kodi.miaoo.cat\addon.xml"
call md5.bat "%file%" md5
echo %md5%>"..\kodi\iyueyu\addon.xml.md5"