#--------------------------------------------------------------#
#BASE CODE
#--------------------------------------------------------------#

from controller import Robot,DistanceSensor
from controller import Motor
from controller import PositionSensor
from termcolor import colored, cprint
import random

#--------------------------------------------------------------#
#GLOBALS

Compass =  0
Front = 0 
FrontLeft = 0
FrontRight = 0
Back = 0
BackLeft = 0
BackRight = 0
Left = 0
Right =  0


#--------------------------------------------------------------#
#INIT

robot = Robot() # Create robot object
timeStep = int(robot.getBasicTimeStep()) 
maxSpeed = 6.28

wheel_left = robot.getDevice("wheel1 motor")
wheel_left.setPosition(float('inf'))

wheel_right = robot.getDevice("wheel2 motor") 
wheel_right.setPosition(float('inf'))

distanceSensor1 = robot.getDevice("D1")
distanceSensor1.enable(timeStep) 

distanceSensor2 = robot.getDevice("D2")
distanceSensor2.enable(timeStep) 

distanceSensor3 = robot.getDevice("D3")
distanceSensor3.enable(timeStep) 

distanceSensor4 = robot.getDevice("D4")
distanceSensor4.enable(timeStep) 

distanceSensor5 = robot.getDevice("D5")
distanceSensor5.enable(timeStep) 

distanceSensor6 = robot.getDevice("D6")
distanceSensor6.enable(timeStep) 

distanceSensor7 = robot.getDevice("D7")
distanceSensor7.enable(timeStep) 

distanceSensor8 = robot.getDevice("D8")
distanceSensor8.enable(timeStep) 

iuSensor = robot.getDevice("inertial_unit") 
iuSensor.enable(timeStep)

#--------------------------------------------------------------#
#TEAM NAME

emitter = robot.getDevice("emitter")
emitter.setChannel(1)
emitter.send('set a team name'.encode('utf-8'))

#---------------------------------------------------------------------------------------------------------------#
#HELPER FUNCTIONS

def rad2deg(rad):
    return (rad/3.14)*180


def readSensorsPrimary():
    global Compass,Front,FrontLeft,Left,BackLeft,Back,BackRight,Right,FrontRight
    global US_Front,US_Left,US_Right

    Compass =  (rad2deg(iuSensor.getRollPitchYaw()[2]) + 360 )% 360
    Front = int(distanceSensor1.getValue() * 10 * 32)
    FrontLeft = int(distanceSensor2.getValue() * 10  * 32)
    Left = int(distanceSensor3.getValue() * 10 * 32)
    BackLeft = int(distanceSensor4.getValue()* 10 * 32)
    Back = int(distanceSensor5.getValue()* 10 * 32)
    BackRight = int(distanceSensor6.getValue()* 10 * 32)
    Right = int(distanceSensor7.getValue() * 10  * 32)
    FrontRight = int(distanceSensor8.getValue() * 10 * 32)
    US_Front = Front
    US_Left = FrontLeft
    US_Right = FrontRight


def debugPrimary():
    global Compass,Front,FrontLeft,Back,BackLeft,Back,BackRight,Right,FrontRight
    print()
    cprint("---------------------------------------------","cyan",)
    cprint("------------------- Debug -------------------","cyan",)
    cprint("---------------------------------------------","cyan",)
    print()
    cprint("------------------ Distance -----------------","yellow",)
    cprint("                       Front: " +str(Front),"yellow")
    cprint("        FrontLeft: " + str(FrontLeft) + "                 FrontRight: " + str(FrontRight),"yellow")
    cprint("Left: " + str(Left) + "                                             Right: " + str(Right),"yellow")
    cprint("        BackLeft: " + str(BackLeft) + "                   BackRight: " + str(BackRight),"yellow")
    cprint("                       Back: " + str(Back),"yellow")
    cprint("------------------- Compass -----------------","yellow",)
    cprint("Compass: " + str("%.0f "%Compass),"yellow")


def move(left, right):
    wheel_left.setVelocity(left * maxSpeed/10)
    wheel_right.setVelocity(right * maxSpeed/10)



#---------------------------------------------------------------------------------------------------------------#
#START

duration = 0
turn = 0

#MAINWHILE

while robot.step(timeStep) != -1:
    readSensorsPrimary()
    debugPrimary()

    # Start Coding ... 

    if duration > 0:
        duration = duration - 1

    elif turn == 1:
        if random.randint(0, 1) == 0:
            move(10, -10)
        else:
            move(-10, 10)

        duration = 20 
        turn = 0 

    elif (FrontLeft < 30 and FrontRight < 30) or FrontLeft < 45 or FrontRight < 45:
        move(-10, -10)
        duration = 30
        turn = 1      

    else:
        move(10,10)

    
