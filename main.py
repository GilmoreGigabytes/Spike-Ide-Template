from spike import PrimeHub, LightMatrix, Button, StatusLight, ForceSensor, MotionSensor, Speaker, ColorSensor, App, DistanceSensor, Motor, MotorPair
from spike.control import wait_for_seconds
from spike.control import Timer
from math import *

hub = PrimeHub()
timer = Timer()

movepair = MotorPair("A", "D")

rightMotor = Motor("D")
leftMotor = Motor("A")

arm = Motor("C")

colourL = ColorSensor("F")
colourR = ColorSensor("B")

defaultSpeed = 60

class error:
    def typeCheck(value, givenType) -> bool:
        if type(value) != givenType:
            return True
        return False


    def throw(value, text : str):
        raise ValueError(str(value) + " is invalid \n" + text)

    class template:
        def sensor(value):
            if value != "left" and value != "right":
                error.throw(value, "Sensor must be a string with the value of `left` or `right`")

        def speed(value):
            if error.typeCheck(value, int and float) == False or value <= 0:
                error.throw(value, "Speed must be an integer greater than 0")

        class direction:
            def leftAndRight(value):
                if value != "left" and value != "right":
                    error.throw(value, "Direction must be a string with the value of `left` or `right`")

            def forwardAndBackward(value):
                if value != "forward" and value != "backward":
                    error.throw(value, "Direction must be a string with the value of `forward` or `backward`")

            def arm(value):
                if error.typeCheck(value, str) or value != "up" and value != "down":
                    error.throw(value, "Direction must be a string with the value of 'up' or 'down'")

        class distance:
            def norm(value):
                if error.typeCheck(value, float) == False and error.typeCheck(value, int) == False or value <= 0:
                    error.throw(value, "Distance must an integer greater than 0")
            
            def cm(value):
                if error.typeCheck(value, int and float) == False or value <= 0:
                    error.throw(value, "Cm must be an integer greater than 0")


            def arm(value):
                if error.typeCheck(value, int) == False and error.typeCheck(value, float) == False:
                    error.throw(value, "Distance must an integer or float")


def waitLight(time : int, i : int, step : int, on : bool):
    timer.reset()

    if on == False:
        while timer.now() < time:
            hub.light_matrix.show_image("SQUARE_SMALL", brightness = i)
            i -= step
    if on == True:
        while timer.now() < time:
            hub.light_matrix.show_image("SQUARE_SMALL", brightness = i)
            i += step
    else:
        raise ValueError("Bad")


def resetYawAngle():
    hub.motion_sensor.reset_yaw_angle()


def resetMotors():
    rightMotor.set_degrees_counted(0)
    leftMotor.set_degrees_counted(0)
    arm.set_degrees_counted(0)


def clear():
    for i in range(10):
        print("")


def count(time : int = 1):
    resetMotors()
    timer.reset()

    while timer.now() < time:
        print("Left Motor: " + str(leftMotor.get_degrees_counted()) + " | Right Motor: " + str(rightMotor.get_degrees_counted()) + "| Arm: " + str(arm.get_degrees_counted()) + "| Left Colour Sensor: " + str(colourL.get_color()) + "| Right Colour Sensor: " + str(colourR.get_color()))
    clear()


def motion():
    yaw = hub.motion_sensor.get_yaw_angle()
    roll = hub.motion_sensor.get_roll_angle()
    pitch = hub.motion_sensor.get_pitch_angle()

    print("Yaw: " + yaw + "| Pitch: " + pitch + "| Roll: " + roll)


def move(distance : int, direction : str, speed : int = defaultSpeed):
    error.template.distance.norm(distance)
    error.template.direction.forwardAndBackward(direction)
    error.template.speed(speed)

    resetMotors()
    resetYawAngle()

    if direction == "forward":
        movepair.move(distance, "cm", 0, speed)
    else:
        movepair.move(-distance, "cm", 0, speed)

    movepair.stop()


def moveWithCorrection(cm : float or int):
    error.template.distance.cm(cm)

    resetMotors()
    resetYawAngle()

    newDegrees = cm / 0.077

    while rightMotor.get_degrees_counted() < newDegrees or leftMotor.get_degrees_counted() > newDegrees:
        correction = 0 - hub.motion_sensor.get_yaw_angle()
        movepair.start_tank_at_power((defaultSpeed + correction), (defaultSpeed - correction))
    movepair.stop()


def turn(deg : int, direction : str, aggressive : bool = False):
    error.template.direction.leftAndRight(direction)

    remainder = None

    if type(aggressive) != bool:
        error.throw(aggressive, "Aggressive mode must be a boolien")

    if deg <= 0:
        error.throw(deg, "Deg must be an integer > 0")

    resetMotors()
    resetYawAngle()

    if aggressive == True:
        turnSpeed = 100
    else:
        turnSpeed = 45

    times = 1
    i = 0

    if deg <= 90 and direction == "left":
        while hub.motion_sensor.get_yaw_angle() > -deg:
            movepair.start_tank_at_power(-turnSpeed, turnSpeed)
        movepair.stop()
        return
    if deg <= 90 and direction == "right":
        while hub.motion_sensor.get_yaw_angle() < deg:
            movepair.start_tank_at_power(turnSpeed, -turnSpeed)
        movepair.stop()  
        return

    while deg >= 90:
        times += 1
        deg -= 45

    # deg is now remainder
    if deg > 45:
        times = 0
        remainder = deg - 45

    var = 45

    if direction == "left":
        while i < times:
            while hub.motion_sensor.get_yaw_angle() > -var:
                movepair.start_tank_at_power(-turnSpeed, turnSpeed)
            i += 1
            movepair.stop()
            resetYawAngle()
        if remainder != None:
            while hub.motion_sensor.get_yaw_angle() > -remainder:
                movepair.start_tank_at_power(-turnSpeed, turnSpeed)
            movepair.stop()
            resetYawAngle()
        return

    if direction == "right":
        while i < times:
            while hub.motion_sensor.get_yaw_angle() < var:
                movepair.start_tank_at_power(turnSpeed, -turnSpeed)
            i += 1
            movepair.stop()
            resetYawAngle()
        if remainder != None:
            while hub.motion_sensor.get_yaw_angle() < var:
                movepair.start_tank_at_power(turnSpeed, -turnSpeed)
            movepair.stop()
            resetYawAngle()
        return


def followLine(sensor : str, cm : int or float):
    error.template.distance.cm(cm)
    error.template.sensor(sensor)

    resetMotors()

    deg = cm / 0.077
    kp = 0.2
    ki = 0
    kd = 0.22
    integral = 0
    lastError = 0
    error = 0
    speed = 30

    if sensor == "left":
        while abs(leftMotor.get_degrees_counted()) < deg or abs(rightMotor.get_degrees_counted()) < deg:
            light = ((colourL.get_reflected_light() - 20) / (87 - 10)) * 100
            error = light - 52
            integral = (integral + error) * 0.5
            correction = int((kp * error)+(ki * integral) +(kd * (error - lastError)))
            left = speed - correction
            right = speed + correction
            lastError = error
            movepair.start_tank_at_power(left, right)
    elif sensor == "right":
        while abs(leftMotor.get_degrees_counted()) < deg or abs(rightMotor.get_degrees_counted()) < deg:
            light = ((colourR.get_reflected_light() - 20) / (87 - 10)) * 100
            error = light - 52
            integral = (integral + error) * 0.5
            correction = int((kp * error)+(ki * integral) +(kd * (error - lastError)))
            left = speed - correction
            right = speed + correction
            lastError = error
            movepair.start_tank_at_power(left, right)

    movepair.stop()


def moveArm(direction : str, speed : int, distance : int or float):
    error.template.direction.arm(direction)
    error.template.speed(speed)
    error.template.distance.norm(distance)

    resetMotors()

    if direction == "down":
        arm.run_for_rotations(distance, speed)
        return
    else:
        arm.run_for_rotations(-distance, speed)


def moveToLine(sensor : str, direction : str):
    error.template.sensor(sensor)
    error.direction.leftAndRight(direction)

    resetMotors()
    resetYawAngle()

    if sensor == "right" and direction == "forward":
        while colourR.get_color() != "black":
            correction = 0 - hub.motion_sensor.get_yaw_angle()
            speed = 30
            movepair.start_tank_at_power( (speed + correction), (speed - correction))
        movepair.stop()
        return

    if sensor == "right" and direction == "backward":
        while colourR.get_color() != "black":
            correction = 0 - hub.motion_sensor.get_yaw_angle()
            speed = -30
            movepair.start_tank_at_power((speed + correction), (speed - correction))
        movepair.stop()
        return

    if sensor == "left" and direction == "forward":
        while colourL.get_color() != "black":
            correction = 0 - hub.motion_sensor.get_yaw_angle()
            speed = 30
            movepair.start_tank_at_power((speed + correction), (speed - correction))
        movepair.stop()
        return

    if sensor == "left" and direction == "backward":
        while colourL.get_color() != "black":
            correction = 0 - hub.motion_sensor.get_yaw_angle()
            speed = -30
            movepair.start_tank_at_power((speed + correction), (speed - correction))
        movepair.stop()
        return


def start(direction : str):
    if direction == "example":
        pass


def missionTester():
    print("Test Stuff In Here Without Going Through The Misison Selector")


def executeMission(missionId : int):
    waitLight(1, 100, 3, False)
    waitLight(2, 0, 3, True)

    hub.status_light.on("green")
    hub.light_matrix.show_image("SQUARE_SMALL", brightness = 100)

    if missionId == 0:
        pass

def missionSelector():
    missionId = 0
    maxMissions = 3
    turn = 10

    exit = False

    while True:
        resetMotors()

        if hub.right_button.was_pressed() and missionId >= maxMissions and missionId != maxMission + 1:
            missionId += 1
            exit = True
        else:
            exit = False
            missionId += 1
            
        if hub.left_button.was_pressed() and missionId != 0:
            missionId -= 1
            exit = False
            
        if abs(rightMotor.get_degrees_counted()) >= turn and exit == True and missionId >= maxMissions:
            clear()
            waitLight(1.5, 1, 100, False)
            raise SystemExit("Exiting...")
        else:
            executeMission(missionId)
            
        if exit == True:
            hub.light_matrix.show_image("SQUARE_SMALL", brightness = 100)
        else:
            hub.light_matrix.write(str(missionId))
        hub.status_light.on("blue")


# Begin mission execution.
missionSelector()
#missionTester()
