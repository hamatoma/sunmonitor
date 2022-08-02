# The Proxy Server SunApi
* Module: SunApi.py
* Type: command line program

## Objective
This program is an HTTP server.
It queries the status of a Shelly device (as an HTTP client) and forwards the response to the request client.

Reason: With this, the interface of the Shelly module can be hidden (behind a firewall or a nat). Because this
interface also allows changing data.

## Call
<pre>
SunApi.py MODE
</pre>
* MODE:
 * daemon Starts a never-ending process to query the status and report it to the client
 * example Outputs an example file for configuring the module
 * init-service Initializes the module as a SystemD service called sunmonitor
 * status Queries the current status of the block

## Examples
<pre>
sudo SunApi.py init-service
SunApi.py example
SunApi.py status
SunApi.py daemon -v
</pre>

## Configuration
An example configuration can be output with "SunApi.py example":

The configuration must be created under /etc/sunmonitor/api.conf:
<pre>
# Configuration for sunapi
log.max.errors=100
log.max.messages=10000
log.print.messages=True
log.print.errors=True
log.print.debug=False
client.ip=192.168.2.44
client.port=80
client.timeout=10
server.interface=0.0.0.0
server.port=8081
</pre>
* client.ip: IP of the Shelly block in the intranet
* server.interface: SunApi can be reached under this interface: 0.0.0.0 for all interfaces
* Be sure to customize:
  * client.ip

# Installation
The monitor must be installed on a Linux system that uses SystemD, e.g. Raspberry-Pi.
The Linux system must be integrated into the intranet because it has to reach the Shelly device.

* Download the zip file from Github and extract it to /opt/sunmonitor
<pre>
# Create directory:
BASE=/opt/sunmonitor
sudo mkdir -p $BASE
cd $BASE
# Create service, create database...
sudo ./installSunApi
</pre>
* Set up port forwarding for SunApi in the router.

## Test after installation
<pre>
python3 /opt/sunmonitor/SunApi.py status
</pre>
