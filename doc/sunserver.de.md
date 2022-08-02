# Der Webserver SunServer 
* Modul: SunServer.py
* Typ: Kommandozeilenprogramm

## Aufgabe:
Es wird ein HTTP-Webserver bereitgestellt. Dieser zeigt auf die Daten aus der Datenbank als Graphik und in Tabellen an.

## Screenshots
### Seite 1:
[[https://github.com/hamatoma/sunmonitor/blob/main/doc/page1.de.png|alt=Screenshot Seite 1]]
### Seite 2:
[[https://github.com/hamatoma/sunmonitor/blob/main/doc/page2.de.png|alt=Screenshot Seite 2]]
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
# Sprache einstellen:
ln -s sunserver.i18n.de sunserver.i18n.current
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
# Sprache einstellen:
ln -s sunserver.i18n.de sunserver.i18n.current
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
# Texte anpassen (Übersetzung)
Alle Texte sind in der Datei sunserver.i18n.de versammelt und können dort geändert werden.

Soll eine andere Sprache benutzt werden, beispielsweise französisch:
* sunserver.i18n.de (odersunserver.i18n.en) kopieren in sunserver.i18n.fr
* sunserver.i18n.fr edieren: Deutsche Texte durch französische Texte ersetzen
* Sprache aktivieren (durch symbolischen Link)
<pre>
LANG_SRC=de
LANG_TRG=fr
cp sunserver.i18n.$LANG_SRC sunserver.i18n.$LANG_TRG
test -e sunserver.i18n.current && rm sunserver.i18n.current
ln -s sunserver.i18n.$LANG_TRG sunserver.i18n.current
</pre>

