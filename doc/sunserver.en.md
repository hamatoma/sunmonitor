# The Web Server SunServer
* Module: SunServer.py
* Type: command line program

## Task:
An HTTP web server is provided. This displays the data from the database as graphics and in tables.

## Screenshots
### Page 1:
[[https://github.com/hamatoma/sunmonitor/blob/main/doc/page1.en.png|alt=Screenshot site 1]]
### Page 2:
[[https://github.com/hamatoma/sunmonitor/blob/main/doc/page2.en.png|alt=Screenshot site 2]]
## call
<pre>
SunServer.py MODE
</pre>
* FASHION:
  * daemon Starts a never-ending process to query the status and write to the database
  * example Outputs an example file for configuring the module
  * init-service Initializes the module as a SystemD service called sunmonitor

## Examples
<pre>
sudo SunServer.py init-service
SunServer.py example
SunServer.py daemon -v
</pre>

## Configuration
An example configuration can be output with "SunServer.py example":

The configuration must be created under /etc/sunmonitor/server.conf:
<pre>
# Configuration for sunserver:
net.interface=localhost
net.port=8080
net.timeout=10
db.name=appsunmonitor
db.user=sun
db.code=sun4sun
base=/opt/sunmonitor
i18n.data=~{base}/sunserver.i18n
i18n.languages=de en
snippets.file=~{base}/sunserver.snippets.html
</pre>

# Installation
Important: The SunServer.py program uses the database that is populated by SunMon.py.
Therefore, both programs must be able to access the same database, so it is best to install both on the same Linux system.

Therefore the directory /opt/sunmonitor and the database already exist.

### Installation on a server in the intranet, e.g. on a Raspberry Pi
<pre>
# Create directory:
BASE=/opt/sunmonitor
cd $BASE
# Create service, web server
DOMAIN=localhost
sudo ./installSunServer $DOMAIN
</pre>

### Installation on a server on the Internet:
In this case, the HTTP server should be addressed with the HTTPS protocol.
This is done by a reverse proxy provided by Nginx.

<pre>
# Create directory:
BASE=/opt/sunmonitor
cd $BASE
# Create service, web server
DOMAIN=sun.example.com
sudo ./installSunServer $DOMAIN
</pre>

# Test after installation
<pre>
sudo systemctl stop sunserver
# Start in the console, since errors may be output there:
python3 /opt/sunmonitor/SunServer.py daemon -v
</pre>
* In the browser:
  * If intranet: http://localhost:8080
  * If internet: https://sun.example.com (adapt domain!)

# Adjust texts (translation)
All texts are collected in the file sunserver.i18n.de and can be changed there.

If another language is to be used, for example French:
* Copy sunserver.i18n.en (or sunserver.i18n.de) to sunserver.i18n.fr
* Edit sunserver.i18n.fr: Replace English texts with French texts (behind the "=" character)
* Activate language (through symbolic link)
<pre>
LANG_SRC=en
LANG_TRG=fr
cp sunserver.i18n.$LANG_SRC sunserver.i18n.$LANG_TRG
test -e sunserver.i18n.current && rm sunserver.i18n.current
ln -s sunserver.i18n.$LANG_TRG sunserver.i18n.current
</pre>
