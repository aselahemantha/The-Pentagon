'''
Import Modules

pyfirmata - a prebuilt library package of python program which can be installed in Arduino to allow serial communication
            between a python script on any computer and an Arduino

time - module that provides ways to representing time in code
math - To use mathematical functions in our program
morse_code - user defined module to decrypt the morse code
paho.mqtt.client - Python language client library under the Eclipse Paho project, 
                    which can connect to MQTT Broker to publish messages, subscribe to topics and receive Published message.

'''

from pyfirmata import Arduino, util, INPUT, OUTPUT, PWM
import morse_code
import time
import math
import paho.mqtt.client as mqtt

# Setup
group = "G32C"
topic_1 = "G32C/CCC/TEMP"
topic_2 = "G32C/CCC/SMOKE"
topic_3 = "G32C/CCC/MORSE"

topic_4 = "G32C/CCC/ALARM"

mqttBroker = "vpn.ce.pdn.ac.lk"  # Must be connected to the vpn
mqttPort = 8883

# The callback for when the client receives a CONNACK response from the server.


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(topic_1)
    client.subscribe(topic_2)
    client.subscribe(topic_3)
    client.subscribe(topic_4)

# The callback for when a PUBLISH message is received from the server.


def on_message(client, userdata, msg):

    # Get values according to the corresponding to the topic

    if msg.topic == "G32C/CCC/ALARM":
        global ccs_alarm
        ccs_alarm = msg.payload.decode('utf-8')


client = mqtt.Client(group)  # Controll Centre Room)


try:
    client.connect(mqttBroker, mqttPort)
    client.on_connect = on_connect
    client.on_message = on_message
    client.loop_start()
except:
    print("Connection to MQTT broker failed!")
    exit(1)

ccs_alarm = 0

# Defining the arduino board

board = Arduino("COM5")

# Initiating the pins

ldr_pin = 0         # LDR --> A0 pin

ther_pin = 1        # Thermistor --> A1 pin

smoke_analog_pin = 2      # MQ-2 Smoke Sensor analog input --> A2 pin

button1_pin = 2     # Button 1 --> D2 pin

button2_pin = 3     # Button 2 --> D3 pin

button3_pin = 4     # Button 3 --> D4 pin

button4_pin = 5     # Button 4 --> D5 pin

smoke_digital_pin = 6       # MQ-2 Smoke Sensor digital input --> D2 pin

# LED to indicate getting the '.' as the morse code input --> D7 pin
led_morseleft_pin = 7

# LED to indicate the system is ready to get the morse code input --> D8 pin
led_morsermiddle_pin = 8

# LED to indicate getting the '-' as the morse code input --> D9 pin
led_morseright_pin = 9

buz_pin = 10        # Buzzer --> D10 pin

led_warning_pin = 11        # LED to indicate alarming --> D12 pin

led_unlock_pin1 = 12     # LED to indicate Unlocking --> D12 pin

led_unlock_pin2 = 13     # LED to indicate Unlocking --> D13 pin


'''
Defining the Pins (Whether they are Input, Output, Analog or Digital)
'''

# Define ldr_pin as a analog input
board.analog[ldr_pin].mode = INPUT

# Define ther_pin as a analog input
board.analog[ther_pin].mode = INPUT

# Define smoke_analog_pin as a analog input
board.analog[smoke_analog_pin].mode = INPUT

# Define button1_pin as a digital input
board.digital[button1_pin].mode = INPUT

# Define button2_pin as a digital input
board.digital[button2_pin].mode = INPUT

# Define button3_pin as a digital input
board.digital[button3_pin].mode = INPUT

# Define button4_pin as a digital input
board.digital[button4_pin].mode = INPUT

# Define smoke_digital_pin as a digital input
board.digital[smoke_digital_pin].mode = INPUT

# Define buz_pin as a digital PWM output
board.digital[buz_pin].mode = PWM

# Define led_morseleft_pin as a digital output
board.digital[led_morseleft_pin].mode = OUTPUT

# Define led_morsermiddle_pin as a digital output
board.digital[led_morsermiddle_pin].mode = OUTPUT

# Define led_morseright_pin as a digital output
board.digital[led_morseright_pin].mode = OUTPUT

# Define led_warning_pin as a digital output
board.digital[led_warning_pin].mode = OUTPUT

# Define led_unlock_pin1 as a digital output
board.digital[led_unlock_pin1].mode = OUTPUT

# Define led_unlock_pin2 as a digital output
board.digital[led_unlock_pin2].mode = OUTPUT


# Starting Iterator thread

it = util . Iterator(board)
it . start()

# Unable serial monitor for get the ldr value
board.analog[ldr_pin].enable_reporting()
# Unable serial monitor for get the thermal value
board.analog[ther_pin].enable_reporting()
# Unable serial monitor for get the smoke sensor value
board.analog[smoke_analog_pin].enable_reporting()


def alarm():
    '''
    Buzzes the alarm and horns the siren in case of someone entered the wrong password or 
    the temperature of the room exceeds the fire alarm temperature.

    '''

    print("Alarm is ON !")
    for i in range(10):

        # Turn on the Buzzer
        board.digital[buz_pin].write(1)

        # Turn on the warning LEDs
        board.digital[led_warning_pin].write(1)

        # Wait 0.3 seconds
        time.sleep(.3)

        # Turn off the Buzzer
        board.digital[buz_pin].write(0)

        # Turn off the warning LEDs
        board.digital[led_warning_pin].write(0)

        # Wait 0.1 seconds
        time.sleep(.1)


def unlock_tone():
    '''
    Turn on LEDs and buzzes a small beep in case of  someone entered the correct password
    '''

    for i in range(3):

        # Turn on the buzzer and set its sound level to low
        board.digital[buz_pin].write(0.2)

        # Turn on the alerting LEDs
        board.digital[led_unlock_pin1].write(1)
        board.digital[led_unlock_pin2].write(1)

        # Wait 0.2 seconds
        time.sleep(0.2)

        # Turn off the buzzer
        board.digital[buz_pin].write(0)

        # Turn off the alerting LEDs
        board.digital[led_unlock_pin1].write(0)
        board.digital[led_unlock_pin2].write(0)

        # Wait 0.2 seconds
        time.sleep(0.2)


def thermal_value():
    '''
    Reads the values of the resistance with the variation of the temperature

    This function takes the analog value from the thermistor and converts it into a temperature value by using Stainhat- Hart equation.


    '''

    # Initiating the values for the Stainhat-Hart constants

    A = 6.046511*10**(-3)  # 0.006046511
    B = -7.9065*10**(-4)  # -0.00079065
    C = 8.4061*10**(-6)  # 0.0000084061

    # Geting the analog reading for measuring the temperature
    voltage_value = board.analog[ther_pin].read()

    # Calculating the temperature value by using Stainhat- Hart equation
    if isinstance(voltage_value, float):

        try:
            resistance = 1000*(1-voltage_value)/voltage_value
            Temperature = round(
                ((A + B*math.log(resistance) + C*(math.log(resistance))**3)**(-1)-273), 3)
            print('Temperature is', Temperature, 'C')

            # Sent Temperaure to Central Control Server

            client.publish(topic_1, Temperature)

        except:
            pass

        # If the temperature is geter than 50 C, calling the alarm function

        if ccs_alarm == '1':
            print('Temperture is HIgh')

            # Call the alarm function
            alarm()

        '''
        The MQ-2 gas sensor detects whether there is any inflammable gas inside the room or any smoke that occurred due to any fire.
        A digital signal & analog signal can be obtain from the MQ-2 smoke sensor. 

        If there is any smoke in the room, MQ-2 smoke sensor gives the digital input as False. Thus, it it gets False, the fire can be detected.
        '''

        # read the digital and analog inputs from the smoke sensor
        smoke_analog = board.analog[smoke_analog_pin].read()
        smoke_digital = board.digital[smoke_digital_pin].read()
        print(smoke_analog)

        if smoke_analog > 0.4650:
            print('Smoke Detected')
            client.publish(topic_2, 1)
            alarm()
        else:
            print('No Smoke Detected')
            client.publish(topic_2, 0)

    # Wait 0.2 seconds
    time.sleep(0.2)


def read_morse():
    '''
    Reads the morse code entered by the person and converts it into a string.
    While the morse code function is being executed, the temperature is also being measured continuously to check whether the
    temperature is below the fire alarming temperature.

    If button 2 is pressed, the program is ready to take the Morse Code. It is indicated by blinking Green LED

            Get the LDR value and time duration, create the morse code according to the time duration
            If LDR time duration is higher than 1 second  ---> Morse code character is '.' ---> To Indicate blink left LED
            If LDR time duration is higher than 3 seconds ---> Morse code character is '-' ---> To Indicate blink right LED
            If LDR time duration is lower  than 1 second  ---> Morse code character is ' '(space)

    Press button 2 to submit the password.
    '''

    # Define empty variables
    vaule_list = []
    morse = ''

    while True:

        # Reads the LDR value and button 2 value
        ldr_val = board.analog[ldr_pin].read()  # read the value
        b2_val = board.digital[button2_pin].read()

        if isinstance(ldr_val, float):
            print('LDR value :', ldr_val, "Button Value :", b2_val)

            # Check whether the LDR value is greater than 0.4(The program identifies that the light source is on when the resistnat value of the LDR is greater than 0.4)

            if ldr_val > 0.5:
                vaule_list.append(ldr_val)

            #  Entering the morse code character to the string.
            else:

                # Adding the morse code character according to the
                if 6 >= len(vaule_list) >= 3:
                    morse = morse + '-'
                    board.digital[led_morseleft_pin].write(1)
                    time.sleep(1)
                    board.digital[led_morseleft_pin].write(0)
                elif 3 > len(vaule_list) >= 1:
                    morse = morse + '.'
                    board.digital[led_morseright_pin].write(1)
                    time.sleep(1)
                    board.digital[led_morseright_pin].write(0)
                else:

                    morse = morse + ' '

                vaule_list = []

            print(morse)
            board.digital[led_morsermiddle_pin].write(1)
            time.sleep(0.4)
            board.digital[led_morsermiddle_pin].write(0)
            time.sleep(0.4)

            # Call the temperature function again

            thermal_value()

            # Submit the morse code to decrypt the password
            if b2_val == True:
                return (morse)


'''
Main code --->
To check the temperature in the room.
To check is there any smoke in the room
To open the door if the entered password is correct and buzz the alarm in case of the password is incorrect.

Four buttons are used to implement the algorithm

    Button 1 ---> To enable & disabled the security system
    Button 2 ---> To Enter the morse code
    Button 3 ---> If someone saw a small fire in the room, that person can buzz the alarm using this button
    Button 4 ---> To shutdown the security system for system maintenance. Should start the algorithm again to start the security system

'''
while True:

    # Read the value from button 1, button 3 and button 4
    b1_val = board.digital[button1_pin].read()
    b3_val = board.digital[button3_pin].read()
    b4_val = board.digital[button4_pin].read()

    print("CCC Security system is not initiated")

    # Wait for 0.05 second
    time.sleep(0.05)

    # Starting the security system
    if b1_val == True:

        print("CCC Security system is initiated")

        # Blink LEDs to indicate the starting of the security system
        board.digital[11].write(1)
        board.digital[12].write(1)
        board.digital[13].write(1)
        board.digital[buz_pin].write(0.1)
        time.sleep(0.5)
        board.digital[11].write(0)
        board.digital[12].write(0)
        board.digital[13].write(0)
        board.digital[buz_pin].write(0)

        while True:

            '''
            Reading the button1 value and button2 value
            Button 1 ---> To disabled the security system
            Button 2 ---> To Enter the password
            Button 3 ---> If someone saw a small fire in the room, that person can buzz the alarm using this button
            Button 4 ---> To shutdown the security system for system maintenance. Should start the algorithm again to start the security system
            '''

            # Read the value from button 1, button 2, button 3 and button 4

            b1_val = board.digital[button1_pin].read()
            b2_val = board.digital[button2_pin].read()
            b3_val = board.digital[button3_pin].read()
            b4_val = board.digital[button4_pin].read()

            time.sleep(0.05)

            # Measures the temperature inside the room and if it is higher than the fire alarming temperature, the alarm is buzzed.

            thermal_value()

            # If button 2 is pressed, the 'enter Morse Code' Function is called.

            if b2_val == True:

                # Getting the morse code
                code = read_morse()
                # Decrypting the morse code
                decrypt_code = morse_code.decrypt(code)
                print(str(decrypt_code))
                client.publish(topic_3, decrypt_code)
                print(code, ' - ', decrypt_code)

                # Checking whether the entered password is correct.

                if ccs_alarm == '1':
                    '''

                    In the case of someone entered the wrong password, it will call the alarm function

                    '''

                    print("Security Issue! Wrong password")
                    alarm()

                elif ccs_alarm == '2':

                    '''

                    In the case of someone entered  the correct password, it will call the unlock function and open the door.

                    '''

                    print("Your password is correct")
                    print("Door Unlocked")
                    unlock_tone()

            # To tempory disable the Security system
            if b1_val == True:
                print("CCC Security system is disabled")
                break

            # Read the button 3 value
            if b3_val == True:

                '''
                In the case of, if someone saw a small fire in the room, that person can buzz the alarm using this button.
                '''

                print("There is a Small fire in the room")
                alarm()

    # Read the button 4 value
    if b4_val == True:

        '''
        To shutdown the security system for system maintenance. Should start the algorithm again to start the security system.
        '''

        print('''
        System is down for security maintenance !!!
        Remember that you should re-run the security system after the maintenance.
        ''')
        break
