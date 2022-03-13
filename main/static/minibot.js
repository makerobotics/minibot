let ws;

function init() {
    console.log("Init");
    WebSocketControl();
    //setInterval(loop, REFRESH);
    initCanvas();
};

function WebSocketControl() {
    if ("WebSocket" in window) {

        ws = new WebSocket('ws://' + location.host + "/websocket");

        ws.onopen = function () {

            document.getElementById("input").style.backgroundColor = "green";
            log('Connection opened');
        };

        ws.onmessage = function (evt) {
            var obj;
            try {
                obj = JSON.parse(evt.data);
                /*document.getElementById('dist').value = obj.distance;
                document.getElementById('speedleft').value = obj.speedL;
                document.getElementById('posleft').value = obj.encoderL;
                document.getElementById('speedright').value = obj.speedR;
                document.getElementById('posright').value = obj.encoderR;
                document.getElementById('yaw').value = obj.yaw;
                document.getElementById('odo').value = obj.odoDistance;*/
            } catch (e) {
                document.getElementById('log').innerHTML += 'Rx: '+evt.data+'\n';
                getObstacle(evt.data);
                //log('Rx ok.');
                //document.getElementById("video").src = "data:image/jpeg;base64," + evt.data;
            }
        };

        ws.onerror = function (event) {
            console.error("WebSocket error observed:", event);
            log('Error: ' + event.data);
        };

        ws.onclose = function () {
            document.getElementById("input").style.backgroundColor = "red";
            log('Connection closed');
        };
    } else {
        // The browser doesn't support WebSocket
        alert("WebSocket NOT supported by your Browser!");
    }
}

function log(line) {
    document.getElementById('log').innerHTML = document.getElementById('log').innerHTML + line + '\n';
    document.getElementById('log').scrollTop = document.getElementById('log').scrollHeight;
}

function clearLog() {
    document.getElementById('log').innerHTML = '';
}

// used by manual command on GUI
function sendMessage() {
    const command = document.getElementById('input').value;
    if(ws != null){
        ws.send(command);
    }
    log('Tx: '+command);
    //document.getElementById('input').value = '';
    updateMap(command);
}

function sentCommand(command){
    if(ws != null){
        ws.send(command);
    }
    log('Tx: '+command);
}

function calcCommand(leg){
    cmd = "SERVO;"+leg.name+";"+ Math.round(leg.theta1 * 180 / Math.PI)+";"+ Math.round(leg.theta2 * 180 / Math.PI)+";"+ Math.round(leg.theta3 * 180 / Math.PI);
    //log(cmd);
    sentCommand(cmd);
}
