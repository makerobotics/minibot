const canv = document.getElementById("CanvasMap");
const ctx = canv.getContext("2d");
const DRAW_FACTOR = 1; // mm/px
const OFFSET = canv.height/2;
let waypoints = [{x:0, y:0, theta:90}];
let obstacles = [{x:0, y:0}];


function addWaypoint(x, y, theta){
    waypoints.push({x:x,y:y, theta:theta});
}

function updateMap(command){
    let c = command.split(" ");
    let p = waypoints[waypoints.length-1];
    console.log("Command: "+command);

    if(c[0] == "move") {
        console.log({x:Math.floor(p.x+c[1]*Math.cos(p.theta*Math.PI/180)), y:Math.floor(p.y+c[1]*Math.sin(p.theta*Math.PI/180)), theta:p.theta});
        addWaypoint(p.x+c[1]*Math.cos(p.theta*Math.PI/180), p.y+c[1]*Math.sin(p.theta*Math.PI/180), p.theta);
    }
    else if(c[0] == "turn") {
        console.log({x:Math.floor(p.x), y:Math.floor(p.y), theta:p.theta-Number(c[1])});    
        addWaypoint(p.x, p.y, p.theta-Number(c[1]));
    }
    refresh();
}

function getObstacle(message){
    //console.log(message);
    let m = message.split(" ");
    if(message.includes("Distance")){
        console.log(m[1]);
        let p = waypoints[waypoints.length-1];
        obstacles.push({x:p.x+m[1]/10*Math.cos(p.theta*Math.PI/180), y:p.y+m[1]/10*Math.sin(p.theta*Math.PI/180)});
    }
}

function initCanvas(){
    
    ctx.clearRect(0, 0, canv.width, canv.height);
    
    ctx.strokeStyle = "#FF0000";
    ctx.lineWidth = 1;

    /*updateMap("move 30");
    updateMap("turn -45");
    updateMap("move 30");
    updateMap("turn -45");
    updateMap("move 30");
    updateMap("turn -45");
    updateMap("move 30");
    updateMap("turn -45");
    updateMap("move 30");
    updateMap("turn -45");
    updateMap("move 30");
    updateMap("turn -45");
    updateMap("move 30");
    updateMap("turn -45");
    updateMap("move 30");*/
}

function convertPathToMap(dist){
    return Math.floor(dist/DRAW_FACTOR);
}

function refresh(){
    ctx.clearRect(0, 0, canv.width, canv.height);
    
    /* Target strokes */
    ctx.strokeStyle = "#0000FF";
    ctx.lineWidth = 1;
    previous = waypoints[0];
    for(let i = 1; i < waypoints.length; i++){
        //console.log(Math.floor(previous.x), Math.floor(previous.y), Math.floor(waypoints[i].x), Math.floor(waypoints[i].y));
        drawPath(previous.x, previous.y, waypoints[i].x, waypoints[i].y);
        previous = waypoints[i];
    }
    /* Obstacles */
    ctx.strokeStyle = "#FF0000";
    ctx.lineWidth = 1;
    for(let i = 1; i < obstacles.length; i++){
        //console.log(Math.floor(previous.x), Math.floor(previous.y), Math.floor(waypoints[i].x), Math.floor(waypoints[i].y));
        drawPath(obstacles[i].x, obstacles[i].y, obstacles[i].x, obstacles[i].y);
    }
}

function drawPath(x0, y0, x1, y1){
    ctx.beginPath();
    ctx.moveTo(convertPathToMap(x0)+OFFSET, canv.height-convertPathToMap(y0)-OFFSET);
    ctx.lineTo(convertPathToMap(x1)+OFFSET, canv.height-convertPathToMap(y1)-OFFSET);
    ctx.stroke();
}
