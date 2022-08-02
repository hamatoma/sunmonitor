# The Monitor SunMon
* Module: SunMon.py
* Type: command line program

## Objective
This program regularly (e.g. every minute) queries the status of a Shelly device and puts it in
a database.

Furthermore, the program can summarize the status data of one day in a record of another table.

## Call
<pre>
SunMon.py MODE
</pre>
* MODE:
 * daemon Starts a never-ending process to query the status and write it to the database
 * example Outputs an example file for configuring the module
 * init-service Initializes the module as a SystemD service called sunmonitor
 * status Queries the current status of the block
 * update-days Compress each day's statistics into a separate table

## Examples
<pre>
sudo SunMon.py init-service
SunMon.py example
SunMon.py status
SunMon.py daemon -v
</pre>

## Configuration
An example configuration can be output with "SunMon.py example":

The configuration must be created under /etc/sunmonitor/monitor.conf:
<pre>
# Configuration for sunmonitor
log.max.errors=100
log.max.messages=10000
log.print.messages=True
log.print.errors=True
log.print.debug=False
net.domain=192.168.2.44
net.port=80
net.timeout=10
net.path=/rpc/Switch.GetStatus?id=0
#net.path=/status
db.name=appsunmonitor
db.user=sun
db.code=sun4sun
service.interval=60
service.from=5
service.til=21
data.start=2022-06-27
</pre>
* Direct use of the device interface (only useful in the intranet)
  * net.path=/rpc/Switch.GetStatus?id=0
* Use with proxy server:
  * net.path=/status
* Time interval when the query should take place (the sun does not shine 24 hours in Germany):
  * service.from: The hour of the day to query from
  * service.til: The last hour of the day to query
* Be sure to customize:
  * net.domain

# Installation
The monitor must be installed on a Linux system that uses SystemD, e.g. Raspberry-Pi.
If the Linux system is in the intranet, the module can be queried directly, no proxy server is required.

If the Linux system is on the Internet, for example a root server at a provider, the proxy server should be running on the intranet
and the query is made via the proxy server.

* On the Linux system:

* Download the zip file from Github and extract it to /opt/sunmonitor
<pre>
# Create directory:
BASE=/opt/sunmonitor
sudo mkdir -p $BASE
cd $BASE
# Create service, create database...
sudo ./installSunMon
</pre>

## Test after installation
<pre>
python3 /opt/sunmonitor/SunMon.py status
</pre>

