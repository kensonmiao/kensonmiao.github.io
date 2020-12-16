set "file=addons.xml"
call md5.bat "%file%" md5
echo %md5%>"addons.xml.md5"