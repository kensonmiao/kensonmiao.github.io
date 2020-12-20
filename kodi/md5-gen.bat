set "file=addons.xml"
call md5.bat "%file%" md5
echo %md5%>"addons.xml.md5"

set "file=addons19.xml"
call md5.bat "%file%" md5
echo %md5%>"addons19.xml.md5"