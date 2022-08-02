# Der Monitor SunMon 
* Modul: SunMon.py
* Typ: Kommandozeilenprogramm

## Zielsetzung
Dieses Programm frägt regelmäßig (beispielsweise jede Minute) den Status eines Shelly-Bausteins ab und trägt diesen in
eine Datenbank ein.

Weiterhin kann das Programm die Statusdaten eines Tages in einen Datensatz einer andere Tabelle zusammenfassen.

## Aufruf
<pre>
SunMon.py MODE
</pre>
* MODE:
 * daemon Startet einen nie endenden Prozess zur Abfrage des Status und Eintrag in die Datenbank
 * example Gibt eine Beispieldatei zur Konfiguration des Moduls aus
 * init-service Initialisiert das Modul als SystemD-Service namens sunmonitor
 * status Fragt den aktuellen Status des Bausteins ab
 * update-days Komprimiert die Statistikdaten jedes Tages in eine eigene Tabelle

## Beispiele
<pre>
sudo SunMon.py init-service
SunMon.py example
SunMon.py status
SunMon.py daemon -v
</pre>

## Konfiguration
Eine Beispielskonfiguration kann mit "SunMon.py example" ausgegeben werden:

Die Konfiguration muss unter /etc/sunmonitor/monitor.conf angelegt werden:
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
* Direkte Nutzung der Bausteinschnittstelle (nur im Intranet sinnvoll)
  * net.path=/rpc/Switch.GetStatus?id=0
* Nutzung mit Proxyserver:
  * net.path=/status
* Zeitintervall, wann die Abfrage erfolgen soll (die Sonne scheint in D ja nicht 24 h):
  * service.from: Die Stunde des Tages, ab der abgefragt wird
  * service.til: Die letzte Stunde des Tages, in der abgefragt wird
* Unbedingt anpassen:
  * net.domain

# Installation
Der Monitor muss auf einem Linuxsystem installiert werden, das SystemD benutzt, z.B. Raspberry-Pi.
Ist das Linuxsystem im Intranet, kann der Baustein direkt abgefragt werden, es ist kein Proxyserver nötig.

Steht das Linuxsystem im Internet, beispielsweise ein Root-Server bei einem Provider, sollte im Intranet der Proxyserver laufen 
und die Abfrage über den Proxyserver erfolgen.

* Auf dem Linuxsystem:

* Zipdatei [[https://github.com/hamatoma/sunmonitor/archive/refs/heads/main.zip]] von Github herunterladen und in /opt/sunmonitor entpacken
<pre>
BASE=/opt/sunmonitor
sudo mkdir -p $BASE
sudo chmod uog+rwx $BASE
cd $BASE
wget https://github.com/hamatoma/sunmonitor/archive/refs/heads/main.zip
unzip main.zip
mv sunmonitor-main/* .
rm -Rf main.zip sunmonitor-main
sudo ./installSunMon 
</pre>

## Test nach Installation
<pre>
python3 /opt/sunmonitor/SunMon.py status
</pre>


