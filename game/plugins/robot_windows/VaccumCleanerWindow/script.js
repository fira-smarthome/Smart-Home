import RobotWindow from './RobotWindow.js';

let historyHtml = "";

var score = 0;

window.updateBatteryPercentage = function (newPercentage) {
    const batteryImage = document.querySelector('.battery-2');

    if (newPercentage === 0) {
        batteryImage.src = 'img/battery-6.png';
    } else if (newPercentage >= 80 && newPercentage <= 100) {
        batteryImage.src = 'img/battery-1.png';
    } else if (newPercentage >= 60 && newPercentage < 80) {
        batteryImage.src = 'img/battery-2.png';
    } else if (newPercentage >= 40 && newPercentage < 60) {
        batteryImage.src = 'img/battery-3.png';
    } else if (newPercentage >= 20 && newPercentage < 40) {
        batteryImage.src = 'img/battery-4.png';
    } else if (newPercentage < 20) {
        batteryImage.src = 'img/battery-5.png';
    }


    const batteryText = document.querySelector('.text-wrapper-3');
    batteryText.textContent = newPercentage + '%';
}

window.updateScore = function (newScore) {
    const scoreElement = document.querySelector('.text-wrapper-2');
    scoreElement.textContent = newScore;
}

window.updateTimer = function (newTime) {
    const timerElement = document.querySelector('.div');
    timerElement.textContent = newTime;
}

window.unloadPressed = function () {
    //Unload button pressed
    //Send the signal for an unload for the correct robot
    window.robotWindow.send("robotUnload");
    window.robotWindow.send("unloadControllerPressed");
}

window.fileOpened = function (filesId, acceptTypes, location) {
    //When file 0 value is changed
    //Get the files
    var files = document.getElementById(filesId).files;

    //If there are files
    if (files.length > 0) {
        //Get the first file only
        var file = files[0];
        //Split at the .
        var nameParts = file.name.split(".");

        //If there are parts to the name
        if (nameParts.length >= 1) {
            //If the file extension is valid
            if (nameParts.length === 1 || acceptTypes.indexOf(nameParts[nameParts.length - 1]) !== -1) {
                const fd = new FormData();
                for (let i = 0; i < files.length; i++) {
                    const f = files[i];
                    fd.append(`file${(i + 1)}`, f, f.name);
                }

                let xmlhttp = new XMLHttpRequest();
                xmlhttp.onreadystatechange = function () {
                    if (xmlhttp.readyState === 4 && xmlhttp.status !== 200) {
                        console.log(xmlhttp.status);
                        alert(xmlhttp.responseText);
                    }
                    if (xmlhttp.readyState === 4 && xmlhttp.status === 200) {
                        loadedController();
                    }
                };
                disableWhileSending(true);
                xmlhttp.open("POST", "http://127.0.0.1:6975/" + location + "/", true);
                xmlhttp.send(fd);
            } else {
                //Tell the user to select a program
                alert("Please select a controller with a valid file type from: .py, .exe, .class, .jar, .bsg, .m or no extension (for Linux/Mac users)");
            }
        } else {
            //Tell the user to select a program
            alert("Please select a controller program");
        }

    }
}

window.runPressed = function () {
    preRun();
    window.robotWindow.send("run");
}

window.pausePressed = function () {
    //When the pause button is pressed
    //Turn off pause button, on run button and send signal to pause
    setEnableButton("pauseButton", false);
    setEnableButton("runButton", true);
    setEnableButton('lopButton', false)
    window.robotWindow.send("pause");
}

window.relocate = function () {
    window.robotWindow.send("relocate");
}

window.preRun = function () {
    //Disable all the loading buttons (cannot change loaded controllers once simulation starts)
    setEnableButton("load", false);
    setEnableButton("unload", false);

    //When the run button is pressed
    //Disable the run button
    setEnableButton("runButton", false);
    //Send a run command
    //Enable the pause button
    setEnableButton("pauseButton", true);
    setEnableButton("giveup", true);

    setEnableButton('lopButton', true)
}

window.resetHistory = function () {
    historyHtml = "";
    document.getElementById("log002").innerHTML = "";
}

window.unloadedController = function () {
    //A controller has been unloaded for robot of the given id
    //Reset name and toggle to load button for robot 0
    document.getElementById("robotCode").value = "";
    document.getElementById("unload").style.display = "none";
    document.getElementById("load").style.display = "inline-block";
}

window.loadedController = function () {
    //A controller has been loaded into a robot id is 0 or 1 and name is the name of the robot
    //Set name and toggle to unload button for robot 0
    document.getElementById("load").style.display = "none";
    document.getElementById("unload").style.display = "inline-block";
    disableWhileSending(false);
}

window.startup = function () {
    resetHistory();
    unloadedController();
    //Turn on the run button and reset button when the program has loaded
    setEnableButton("runButton", true);
    setEnableButton("pauseButton", false);
    setEnableButton('lopButton', false)

    setEnableButton("load", true);
    setEnableButton("unload", true);
    setEnableButton("giveup", false);
}

window.endGame = function () {
    //Once the game is over turn off both the run and pause buttons
    setEnableButton("runButton", false)
    setEnableButton("pauseButton", false);
    setEnableButton('lopButton', false)
}

window.updateHistory = function (history0) {
    let html = "<div class='log-row'>";
    if (history0[0].indexOf(":") !== -1) {
        if (history0[1].indexOf("+") !== -1) {
            html += `<span style='font-size:18px;color:#2980b9; flex: auto; text-align: center;'>${history0[0]}</span><span style='font-size:18px;color:#2980b9; flex: auto; text-align: center;;'>${history0[1]}</span>`;
        } else if (history0[1].indexOf("-") !== -1) {
            html += `<span style='font-size:18px;color:#c0392b; flex: auto; text-align: center;'>${history0[0]}</span><span style='font-size:18px;color:#c0392b; flex: auto; text-align: center;'>${history0[1]}</span>`;
        } else {
            html += `<span style='font-size:18px;color:#2c3e50; flex: auto; text-align: center;'>${history0[0]}</span><span style='font-size:18px;color:#2c3e50; flex: auto; text-align: center;'>${history0[1]}</span>`;
        }
    }
    html += "</div>";
    historyHtml = html + historyHtml;
    document.getElementById("log002").innerHTML = historyHtml;
}

window.openLoadController = function () {
    document.getElementById("robotCode").click();
    window.robotWindow.send("loadControllerPressed");
}

window.calculateTimeRemaining = function (done, maxTime) {
    //Create the string for the time remaining (mm:ss) given the amount of time elapsed
    //Convert to an integer
    done = Math.floor(done);
    //Calculate number of seconds remaining
    var remaining = maxTime - done;
    //Calculate seconds part of the time
    var seconds = Math.floor(remaining % 60);
    //Calculate the minutes part of the time
    var mins = Math.floor((remaining - seconds) / 60);
    //Convert parts to strings
    mins = String(mins)
    seconds = String(seconds)

    //Add leading 0s if necessary
    for (var i = 0; i < 2 - seconds.length; i++) {
        seconds = "0" + seconds;
    }

    for (var i = 0; i < 2 - mins.length; i++) {
        mins = "0" + mins;
    }

    //Return the time string
    return mins + ":" + seconds;
}

window.update = function (data) {
    //Update the ui each frame of the simulation
    //Sets the scores and the timer
    updateScore(String(data[0]));
    updateBatteryPercentage(data[4]);

    score = data[0];

    //The total time at the start
    let maxTime = 8 * 60;
    if (data[2]) { // is this necessary?
        maxTime = data[2]
    }
    maxTime = parseInt(maxTime);
    let maxRealTime = Math.max(maxTime + 60, maxTime * 1.25);
    document.getElementById("timer").innerHTML = calculateTimeRemaining(data[1], maxTime);
    // document.getElementById("realWorldTimer").innerHTML = calculateTimeRemaining(data[3], maxRealTime);
}

window.giveupPressed = function () {
    window.robotWindow.send("quit");
    setEnableButton("runButton", false)
    setEnableButton("pauseButton", false);
    setEnableButton('lopButton', false)
    setEnableButton('giveup', false)
}

window.receive = function (message) {
    //Receive message from the python supervisor
    //Split on comma
    var parts = message.split(",");
    console.log(parts);

    //If there is a message
    if (parts.length > 0) {
        switch (parts[0]) {
            case "startup":
                //Call for set up the robot window
                startup();
                break;
            case "update":
                //Update the information on the robot window every frame (of game time)
                update(parts.slice(1, parts.length + 1));
                break;
            case "config":
                //Load config data
                // updateConfig(parts.slice(1, parts.length + 1));
                break;
            case "unloaded":
                //Robot 0's controller has been unloaded
                unloadedController();
                break;
            case "loaded":
                loadedController();
                break;
            case "ended":
                //The game is over
                endGame();
                break;
            case "historyUpdate":
                let history0 = message.split(",").slice(1, message.length - 1)
                updateHistory(history0)
                break;
            case "loadControllerPressed":
                openLoadController();
                break;
            case "unloadControllerPressed":
                unloadedController();
                break;
            case "runPressed":
                runPressed();
                break;
            case "pausedPressed":
                pausePressed();
                break;
        }
    }
}

window.disableWhileSending = function (disabled) {
    setEnableButton("load", !disabled);
    setEnableButton("unload", !disabled);

    setEnableButton("runButton", !disabled);
}

window.setEnableButton = function (name, state) {
    document.getElementById(name).disabled = !state;
}


//Set the onload command for the window
window.onload = function () {
    //Connect the window
    window.robotWindow = new RobotWindow();
    //Set the title
    window.robotWindow.setTitle('Fira Smart Home');
    //Set which function handles the recieved messages
    window.robotWindow.receive = receive;
    //Set timer to inital time value
    document.getElementById("timer").innerHTML = 'Initializing'
    window.robotWindow.send("rw_reload");

    updateScore(0);
    updateTimer('08:00'); // Time
    updateBatteryPercentage(100);
};