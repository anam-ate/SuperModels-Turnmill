import RPi.GPIO as GPIO
import os
import sys
import signal
import time
import threading

from omxplayer.player import OMXPlayer

button_lock = threading.Lock() #declare local variable lock to use lock instance of class lock, use 2 methods acquire to lock and release to release lock
button_running = True
button_state = False

GPIO.setmode(GPIO.BCM)
#==============================variables============================================

running = True

state = 0
delay_period = 0.01
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM) # means that i am referring to the pins
buttonPin = 5
buttonPress = True
GPIO_TRIGGER = 12
GPIO_ECHO = 24
GPIO.setup(buttonPin,GPIO.IN,pull_up_down = GPIO.PUD_UP)

GPIO.setup(GPIO_TRIGGER,GPIO.OUT)
GPIO.setup(GPIO_ECHO,GPIO.IN)


#GPIO.output(RELAY_1_GPIO, GPIO.LOW) # out
GPIO.setup(buttonPin,GPIO.IN,pull_up_down = GPIO.PUD_UP)#set pin 10 to input and set initial value to low



def distance():
    # set Trigger to HIGH
    GPIO.output(GPIO_TRIGGER, True)

    # set Trigger after 0.01ms to LOW
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)

    StartTime = time.time()
    StopTime = time.time()

    # save StartTime
    while GPIO.input(GPIO_ECHO) == 0:
        StartTime = time.time()

    # save time of arrival
    while GPIO.input(GPIO_ECHO) == 1:
        StopTime = time.time()

    # time difference between start and arrival
    TimeElapsed = StopTime - StartTime
    # multiply with the sonic speed (34300 cm/s)
    # and divide by 2, because there and back
    distance = (TimeElapsed * 34300) / 2

    return distance


def buttonPressed(): # the state of the button
    return not GPIO.input(buttonPin)

def button_thread_function():
    global button_running, button_lock, button_state
    while(button_running):
        try:
            button_lock.acquire() # DOM: acquire, not aquire
            button_state = buttonPressed()
        finally:
            button_lock.release()
        time.sleep(0.005) # DOM: one more tab





def signal_handler(signal, frame):
    global running, button_running
    print("Stopping program")
    running = False
    button_running = False

# register signal handler
signal.signal(signal.SIGINT, signal_handler)

movie1 = ("/home/pi/Videos/TurnmillContent.mp4")

video_lengths = [5,102,5]#[9,102]
video_timestamps = [0,10,0]
current_video = 0
next_video_to_play = 1
number_of_videos = 3 #counter for videos

last_button_state = False
local_button_state = False # DOM: declare this here

quit_video = True

player = False
buttonPress= False
playing = False

player = OMXPlayer(movie1, args=['--no-osd','-b'])
button_thread = threading.Thread(target = button_thread_function, args = ())# DOM: no parentheses after the function name. if you have parentheses then you're alling thr function in the main thread, not in the new thread.
button_thread.start()


while running:

    time.sleep(0.0005)

    if (current_video == 0):
        try:
            button_lock.acquire() # DOM: acquire, not aquire
            local_button_state = button_state
        finally:
            button_lock.release()


    if ((current_video == 0) and (local_button_state == True)):

        player.seek(-player.position() + video_timestamps[next_video_to_play]) #0 + next video in array 10 seconds
        current_video = next_video_to_play
        next_video_to_play += 1

        if(next_video_to_play >= number_of_videos ): # -1 number of videos because the last one plays with the sensor state
            print('revert to default')
            current_video = 0            
            next_video_to_play = 1
            player.seek(-player.position())


    #if the player pos is greater than the video stamp plus the length of the video then revert to default content
    if (player.position() >= (video_timestamps[current_video] + video_lengths[current_video])):
        print('default content')
        player.seek(-player.position())
        current_video = video_timestamps[0]
        current_video = 0

    #if the videos are all complete after the last button press then play default supermodels video
    last_button_state = local_button_state

# Cleanup
print("Cleanup")
button_thread.join() #exit thread
if (player.is_playing()):
    player.stop()

GPIO.cleanup()
