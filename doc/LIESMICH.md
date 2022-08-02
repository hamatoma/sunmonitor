Sun Monitor

# Zielsetzung
Ich habe eine "Balkonkraftwerk" (Mini-Photovoltaikanlage) in Betrieb genommen. Mit diesem Projekt lässt sich die "Ernte" anzeigen.
Diese Zielsetzung hat dem Projekt den Namen gegeben.
 
Die Marke Shelly (TM) bietet Bausteine an, die per WLan ihren Status (Messwerte) abfragen lassen.

Das Projekt SunMonitor bietet Module, die diese Daten sammeln (Modul SunMon) und darstellen (Modul SunServer).

Zusätzlich gibt es das Modul SunApi, das als Proxyserver die Schnittstelle des Shelly-Bausteins auf eine reine Abfrage reduziert: 
Wenn die Schnittstelle im Netz freigegeben wird, können Daten des Bausteins geändert werden. Der Proxyserver verhindert das.

# Lizenz
Siehe LICENSE

# Der Monitor SunMon 
* Modul: SunMon.py
* Typ: Kommandozeilenprogramm

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

* Zipdatei von Github herunterladen und in /opt/sunmonitor entpacken
<pre>
# Verzeichnis anlegen: 
BASE=/opt/sunmonitor
sudo mkdir -p $BASE
cd $BASE
# Service anlegen, Datenbank anlegen...
sudo ./installSunMon 
</pre>

## Test nach Installation
<pre>
python3 /opt/sunmonitor/SunMon.py status
</pre>

# Der Webserver SunServer 
* Modul: SunServer.py
* Typ: Kommandozeilenprogramm

## Aufruf
<pre>
SunServer.py MODE
</pre>
* MODE:
 * daemon Startet einen nie endenden Prozess zur Abfrage des Status und Eintrag in die Datenbank
 * example Gibt eine Beispieldatei zur Konfiguration des Moduls aus
 * init-service Initialisiert das Modul als SystemD-Service namens sunmonitor

## Beispiele
<pre>
sudo SunServer.py init-service
SunServer.py example
SunServer.py daemon -v
</pre>

## Konfiguration
Eine Beispielskonfiguration kann mit "SunServer.py example" ausgegeben werden:

Die Konfiguration muss unter /etc/sunmonitor/server.conf angelegt werden:
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
Wichtig: Das Programm SunServer.py nutzt die Datenbank, die von SunMon.py gefüllt wird. 
Daher müssen beide Programme auf die gleiche Datenbank zugreifen können, also am besten beide im gleichen Linuxsystem installieren.

Daher existiert schon das Verzeichnis /opt/sunmonitor und die Datenbank.

### Installation auf einem Server im Intranet, z.B auf einem Raspberry-Pi
<pre>
# Verzeichnis anlegen: 
BASE=/opt/sunmonitor
cd $BASE
# Service anlegen, Webserver 
DOMAIN=localhost
sudo ./installSunServer $DOMAIN
</pre>

### Installation auf einem Server im Internet:
In diesem Fall soll der HTTP-Server mit dem HTTPS-Protokoll angesprochen werden.
Das erledigt ein Reverse-Proxy, den Nginx bereitstellt.

<pre>
# Verzeichnis anlegen: 
BASE=/opt/sunmonitor
cd $BASE
# Service anlegen, Webserver 
DOMAIN=sun.example.com
sudo ./installSunServer $DOMAIN
</pre>

# Test nach Installation
<pre>
sudo systemctl stop sunserver
# Starten in der Konsole, da dort evt. Fehler ausgegeben werden:
python3 /opt/sunmonitor/SunServer.py daemon -v
</pre>
* Im Browser:
 * Wenn Intranet: http://localhost:8080
 * Wenn Internet: https://sun.example.com  (Domäne anpassen!)

# Programmänderungen
## Andere Landessprache
* SunMon.py: Da ohne Kontakt zum Benutzer: Meldungen und Fehler werden englisch ausgegeben.
* SunApi.py: Da ohne Kontakt zum Benutzer: Meldungen und Fehler werden englisch ausgegeben.
* SunServer.py: Alle Texte sind in sunserver.i18n.de definiert. Die Texte können dort geändert (z.B. übersetzt) werden.

## Layout
* Die HTML5-Struktur ist in der Datei sunserver.snippets.html definiert. Dort kann das Aussehen mittels CSS angepasst werden.

