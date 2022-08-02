 let remoteurl = "http://ip.hamatoma.de/setip.php?hostname=sunmonitor";
 let maxfails = 1000;
// checks the internet connection every x minutes, recommended is 5 or more
let interval = 60;
// CONFIG END

// no need to change anything below this line.
let alertTimer = '';
let failcounter = 0;
function setIp(){
  print("setIp:");
  Shelly.call("HTTP.GET", {
          url: remoteurl
      },
      function (res, error_code, error_msg, ud) {
          if (error_code !== 0) {                  
             if (failcounter === maxfails) {
                  print("Restart");
                  restartRelay();
                  failcounter = 0;
              } else {
                 failcounter++;
                 print("fail: res: ", res, " err: ", error_code, " msg: ", 
                   error_msg, " ud: ", ud, " #: ", failcounter);
              }
          }
      },
      null
  );
}
function startMonitor() {
  alertTimer = Timer.set(interval *60 * 1000,
    true,
    function () {
      print("started by timer");
      setIP();
    },
    null
  );
}
function restartRelay() {
    Shelly.call(
        "switch.set",
        { id: 0, on: false, toggle: 2},
        function (result, code, msg, ud) {
        },
        null
    );
}
startMonitor();
setIp();