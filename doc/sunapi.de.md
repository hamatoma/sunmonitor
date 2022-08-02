# Der Proxyserver SunApi
* Modul: SunApi.py
* Typ: Kommandozeilenprogramm

## Zielsetzung
Dieses Programm ist ein HTTP-Server.
Es fragt den Status eines Shelly-Bausteins ab (als HTTP-Client) und leitet die Antwort an den Anfrage-Client weiter.

Grund: Damit kann die Schnittstelle des Shelly-Bausteins verborgen sein (hinter einer Firewall oder einem Nat). Denn diese
Schnittstelle erlaubt auch das Ändern von Daten.

## Aufruf
<pre>
SunApi.py MODE
</pre>
* MODE:
 * daemon Startet einen nie endenden Prozess zur Abfrage des Status und Weitergabe an den Client
 * example Gibt eine Beispieldatei zur Konfiguration des Moduls aus
 * init-service Initialisiert das Modul als SystemD-Service namens sunmonitor
 * status Fragt den aktuellen Status des Bausteins ab

## Beispiele
<pre>
sudo SunApi.py init-service
SunApi.py example
SunApi.py status
SunApi.py daemon -v
</pre>

## Konfiguration
Eine Beispielskonfiguration kann mit "SunApi.py example" ausgegeben werden:

Die Konfiguration muss unter /etc/sunmonitor/api.conf angelegt werden:
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
* client.ip: IP des Shelly-Bausteins im Intranet
* server.interface: Unter diesem Interface ist SunApi erreichbar: 0.0.0.0 für alle Interfaces
* Unbedingt anpassen:
  * client.ip

# Installation
Der Monitor muss auf einem Linuxsystem installiert werden, das SystemD benutzt, z.B. Raspberry-Pi.
Das Linuxsystem muss im Intranet eingebunden sein, da es den Shelly-Baustein erreichen muss.

* Zipdatei von Github herunterladen und in /opt/sunmonitor entpacken
<pre>
# Verzeichnis anlegen: 
BASE=/opt/sunmonitor
sudo mkdir -p $BASE
cd $BASE
# Service anlegen, Datenbank anlegen...
sudo ./installSunApi 
</pre>
* Im Router eine Port-Weiterleitung für SunApi einrichten.

## Test nach Installation
<pre>
python3 /opt/sunmonitor/SunApi.py status
</pre>

