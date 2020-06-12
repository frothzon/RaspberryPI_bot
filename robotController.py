# Rayu and Lexis cat toy control script
import RPi.GPIO as GPIO # Pin input library
import time             # Timing library
import pygame as pg     # Audio library
import sys

# Setup Audio
#-----------------
# sudo apt-get update
# sudo apt-get upgrade
#-----------------
pg.init()
pg.mixer.init()

# Laser Motor Move Time
motor_time 		= 0.3

# Setup Pins -> sensor, laser, moving motors, laser rotate motor
GPIO.setmode(GPIO.BCM)
pin_sensorIn    = 24
pin_sensorOut   = 23
pin_laser       = 17
pin_motorMove   = 27
pin_motorLaser1 = 22
pin_motorLaser2 = 10	# HOOK up pin 10 to second relay
pin_onSwitch 	= 9	# HOOK up pin 9 to start button
pin_speaker     = 11

# State Machine Variables
state_time      = -1    # Counter
state           = -1    # Current state
wait_time       = 3     # Wait time for toy
state_start     = 1     # First frame of state\
motor_dir 	= 1	# Starting Direction

# Designate Pin Assignments
GPIO.setup(pin_onSwitch, GPIO.IN)
GPIO.setup(pin_sensorIn, GPIO.IN)
GPIO.setup(pin_sensorOut, GPIO.OUT)
GPIO.setup(pin_laser, GPIO.OUT)
GPIO.setup(pin_motorMove, GPIO.OUT)
GPIO.setup(pin_motorLaser1, GPIO.OUT)
GPIO.setup(pin_motorLaser2, GPIO.OUT)
GPIO.setup(pin_speaker, GPIO.OUT)


#----------------------- Setup state-machine ------------------- #
# spinLaser(dir)
# dir -1 = reverse
# dir  1 = forward
# dir  0 = stop
def playSound(freq, playTime):
    global pin_speaker
    period = 1/freq
    loops = playTime
    while loops > 0:
        #print(loops)
        loops = loops - period
        GPIO.output(pin_speaker, GPIO.HIGH)
        time.sleep(period*0.5)
        GPIO.output(pin_speaker, GPIO.LOW)
        time.sleep(period*0.5)
        
def spinLaser(dir):
    # Get global variables
    global pin_motorLaser1
    global pin_motorLaser2
    # Set together
    if dir == -1:
        GPIO.output(pin_motorLaser1, GPIO.LOW)
        GPIO.output(pin_motorLaser2, GPIO.HIGH)
    if dir == 1:
        GPIO.output(pin_motorLaser1, GPIO.HIGH)
        GPIO.output(pin_motorLaser2, GPIO.LOW)
    if dir == 0:
        GPIO.output(pin_motorLaser1, GPIO.LOW)
        GPIO.output(pin_motorLaser2, GPIO.LOW)
	
# Get current time
def getTime():
    return round(time.time(),2)
# check the time
def timeCheck():
    global state_time
    change = getTime() - state_time
    return change
# Switch to a new state
def switch_state(new_state):
    # Grab global variables
    global state
    global state_time
    global state_start
    # Set variables
    state = new_state
    state_time = getTime()
    state_start = 1
# Run State -- starting with default state     
def update_state(default):
    # Grab global variables
    global state_time
    global state
    global state_start
    # Set variables
    state_time = state_time + 1
    if(state == -1):
        state = default
    state()
    state_start = 0
#-----------------------  State Machine Methods ------------------ #
# Set all pins to LOW
def Startup():
    print("STATE = Setup")
    # Grab global variables
    global pin_laser
    global pin_motorMove
    global pin_motorLaser1
    global pin_sensorOut
    # Set Pins
    GPIO.output(pin_laser, GPIO.LOW)
    GPIO.output(pin_motorMove, GPIO.HIGH) # N.C. switch
    GPIO.output(pin_motorLaser1, GPIO.HIGH) # N.C. switch
    GPIO.output(pin_sensorOut, GPIO.LOW)
    GPIO.output(pin_motorLaser2, GPIO.HIGH)
    switch_state(TurnOnLaser)
    
# Laster Startup
def TurnOnLaser():
    print("STATE = Turn on Laser")
    # Grab global variables
    global pin_laser
    # Set variables
    GPIO.output(pin_laser, GPIO.HIGH)
    switch_state(CheckSensor)

# Check laser for blockage
def CheckSensor():
    print("STATE = Check Sensor")
    # Grab global variables
    global pin_sensorIn
    global wait_time
    # Check Sensor
    distance = SenseDistance()
    # If sensor is blocked, move laser
    if distance < 15:
        print("Rotate Laser")
        switch_state(RotateLaser)
    # If sensor not blocked for 3 seconds, move toy
    if timeCheck() > wait_time:
        print("Move Toy")
        switch_state(MoveForward)

# Rotate the laser for a short time
def RotateLaser():
    print("STATE = Rotate Laser")
    # global variables
    global motor_dir
    global motor_time
    # Turn laser in motor direction
    spinLaser(motor_dir)
    print(motor_dir)
    # Wait short period of time
    time.sleep(motor_time)
    # Stop spinning Laser
    spinLaser(0)
    # Reverse Direction
    if motor_dir == 1:
        motor_dir = -1
    else:
        motor_dir = 1
    # Change State
    switch_state(CheckSensor)

# Move the Toy Forward
def MoveForward():
    print("STATE = Move Forward")
    # Grab global variables
    global pin_motorMove
    GPIO.output(pin_motorMove, GPIO.LOW)
    print("Moving Wheels")
    time.sleep(3)
    GPIO.output(pin_motorMove, GPIO.HIGH)
    print("Stopped Wheels")
    switch_state(CheckSensor)
#------------------------- Sensor Distance Calculator -------------#
def SenseDistance():
    # Set pin to low
    GPIO.output(pin_sensorOut, False)
    print("Waiting for Sensor to Settle")
    time.sleep(2)
    #Creating Trigger Pulse
    GPIO.output(pin_sensorOut, True)
    time.sleep(0.00001)
    GPIO.output(pin_sensorOut, False)
    while GPIO.input(pin_sensorIn) == 0:
        pulse_start = time.time()
    while GPIO.input(pin_sensorIn) == 1:
        pulse_end = time.time()
    pulse_duration = pulse_end - pulse_start
    distance = round(pulse_duration*17150, 2)
    print(distance)
    return distance

def SetMotor(ids):
    GPIO.output(pin_motorMove, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(pin_motorMove, GPIO.LOW)

def play_music(music_file):
    '''
    stream music with mixer.music module in blocking manner
    this will stream the sound from disk while playing
    '''
    clock = pg.time.Clock()
    try:
        pg.mixer.music.load(music_file)
        print("Music file {} loaded!".format(music_file))
    except pygame.error:
        print("File {} not found! {}".format(music_file, pg.get_error()))
        return

    pg.mixer.music.play()

    # If you want to fade in the audio...
    # for x in range(0,100):
    # pg.mixer.music.set_volume(float(x)/100.0)
    # time.sleep(.0075)
    # # check if playback has finished
    while pg.mixer.music.get_busy():
        clock.tick(30)

while  1:
    if GPIO.input(pin_onSwitch):
        print("Get Rickity Rickity Wrecked, son")
        # Play Chirp
        for x in range(15):
            playSound(1000*(x+1),0.004)
        # Run State Machine
        update_state(Startup)


GPIO.cleanup()


