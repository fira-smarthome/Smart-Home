# --------------------------------------------------------------#
# BASE CODE
# --------------------------------------------------------------#
from controller import Robot
from termcolor import cprint

# --------------------------------------------------------------#
# GLOBALS

Compass = 0
PositionX = 0
PositionY = 0
FrontLeft = 0
FrontRight = 0
RightFront = 0
RightBack = 0
BackLeft = 0
BackRight = 0
LeftBack = 0
LeftFront = 0
Battery = 0

# --------------------------------------------------------------#
# INIT

robot = Robot()  # Create robot object
timeStep = int(robot.getBasicTimeStep())
maxSpeed = 6.28

wheel_left = robot.getDevice("wheel2 motor")
wheel_left.setPosition(float('inf'))

wheel_right = robot.getDevice("wheel1 motor")
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

gpsSensor = robot.getDevice("gps")
gpsSensor.enable(timeStep)

receiver = robot.getDevice("receiver")
receiver.setChannel(1)
receiver.enable(timeStep)

# --------------------------------------------------------------#
# TEAM NAME

emitter = robot.getDevice("emitter")
emitter.setChannel(1)
emitter.send('set a team name'.encode('utf-8'))


# ---------------------------------------------------------------------------------------------------------------#
# HELPER FUNCTIONS

def rad2deg(rad):
    return (rad / 3.14) * 180


def readSensors():
    global Compass, PositionX, PositionY, FrontLeft, FrontRight, RightFront, RightBack, BackLeft, BackRight, LeftBack, LeftFront, Battery
    Compass = (rad2deg(iuSensor.getRollPitchYaw()[2]) + 360) % 360
    PositionX = gpsSensor.getValues()[0] * 100
    PositionY = gpsSensor.getValues()[2] * 100
    FrontLeft = int(distanceSensor1.getValue() * 10 * 32)
    FrontRight = int(distanceSensor8.getValue() * 10 * 32)
    RightFront = int(distanceSensor7.getValue() * 10 * 32)
    RightBack = int(distanceSensor6.getValue() * 10 * 32)
    BackLeft = int(distanceSensor3.getValue() * 10 * 32)
    BackRight = int(distanceSensor5.getValue() * 10 * 32)
    LeftBack = int(distanceSensor4.getValue() * 10 * 32)
    LeftFront = int(distanceSensor2.getValue() * 10 * 32)

    if receiver.getQueueLength() > 0:
        received_data = receiver.getString()
        if len(received_data) > 0:
            Battery = float(received_data)
        receiver.nextPacket()


def debug():
    global Compass, PositionX, PositionY, FrontLeft, FrontRight, RightFront, RightBack, BackLeft, BackRight, LeftBack, LeftFront, Battery

    print()
    cprint("---------------------------------------", "cyan", )
    cprint("------------------ Debug --------------", "cyan", )
    cprint("---------------------------------------", "cyan", )
    print()
    cprint("---------------- Battery -------------", "yellow", )
    cprint(Battery, "yellow", )
    print()
    cprint("---------------- Distance -------------", "yellow", )
    cprint("            FrontLeft: " + str(FrontLeft) + " , FrontRight: " + str(FrontRight), "yellow")
    cprint("LeftFront: " + str(LeftFront) + "                            RightFront: " + str(RightFront), "yellow")
    cprint("LeftBack:  " + str(LeftBack) + "                             RightBack:  " + str(RightBack), "yellow")
    cprint("            BackLeft: " + str(BackLeft) + " ,  BackRight:  " + str(BackRight), "yellow")
    cprint("-----------------  GPS  ---------------", "cyan")
    cprint("X: " + str("%.2f " % PositionX) + "           Y: " + str("%.2f " % PositionY), "blue")
    cprint("----------------- Compass -------------", "yellow")
    cprint("Compass: " + str("%.0f " % Compass), "yellow")
    cprint("------------------ Time ---------------", "yellow")
    cprint("Time: " + str(robot.getTime()), "yellow")


def move(left, right):
    wheel_left.setVelocity(left * maxSpeed / 10)
    wheel_right.setVelocity(right * maxSpeed / 10)


# ---------------------------------------------------------------------------------------------------------------#
# START

duration = 0

# MAINWHILE
while robot.step(timeStep) != -1:
    readSensors()
    debug()

    # Start Coding ...

    if duration > 0:
        duration = duration - 1

    elif FrontRight <= 30 and FrontLeft <= 30:
        move(-10, -7)
        duration = 20

    elif FrontLeft <= 35:
        move(7, -6)
        duration = 20

    elif FrontRight <= 35:
        move(-6, 7)
        duration = 20

    else:
        move(10, 10)
