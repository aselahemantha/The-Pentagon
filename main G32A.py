# import pyfirmata,time and math libraries

import pyfirmata
import time
import math
import paho.mqtt.client as mqtt

# Setup
group = "G32A"
topic_1 = "G32A/CDR/TEMP"
topic_2 = "G32A/CDR/PRES"
topic_3 = "G32A/CDR/LIGHT"
topic_4 = "G32A/CDR/SEQ"

topic_5 = "G32A/CDR/ALARM"
topic_6 = "G32A/CDR/CDRE"

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
    client.subscribe(topic_5)
    client.subscribe(topic_6)

# The callback for when a PUBLISH message is received from the server.

ccs_enter = 0
ccs_alarm = 0

def on_message(client, userdata, msg):
    #print(msg.topic+" "+str(msg.payload))
    if msg.topic == "G32A/CDR/ALARM":
        global ccs_alarm
        ccs_alarm = msg.payload.decode('utf-8')
        print(ccs_alarm)
    if msg.topic == "G32A/CDR/CDRE":
        global ccs_enter
        ccs_enter = msg.payload.decode('utf-8')

client = mqtt.Client(group)  # Controll Centre Room)


try:
    client.connect(mqttBroker, mqttPort)
    client.on_connect = on_connect
    client.on_message = on_message
    client.loop_start()
except:
    print("Connection to MQTT broker failed!")
    exit(1)

# port that connected
board = pyfirmata.Arduino("COM4")

it = pyfirmata.util.Iterator(board)
it.start()

# pin of thermistor
tempt = board.get_pin('a:1:i')


# pins of secret code
sq = board.get_pin('d:7:i')
b1 = board.get_pin('d:12:i')
b2 = board.get_pin('d:13:i')
led_green = board.get_pin('d:4:o')
led_red = board.get_pin('d:5:o')

# pin of pressure
fpressure = board.get_pin('d:8:i')


# pins of ldr
LDR = board.get_pin('a:0:i')
led_orange = board.get_pin('d:11:o')

# pin of buzzer
buzzer = board.get_pin('d:9:o')

# pin of reset
rst = board.get_pin('d:2:i')


def pushbutton():
    '''defined a function for secret code'''
    print("keep enter the password")

    lock = []

    # delay times
    t = 1
    T = 3

    while True:

        # digital input from the push buttons
        push1 = b1.read()
        push2 = b2.read()
        print("Enter password")
        time.sleep(t)
        if push1 == True:

            # append caractor for the push button
            lock.append('A')
            time.sleep(t)

        elif push2 == True:
            # append caractor for the push button
            lock.append('B')
            time.sleep(t)

        if len(lock) == 4:
            # print the input password
            print(lock)
            lock_st = ''
            for i in lock:
                lock_st = lock_st + str(i)
            client.publish(topic_4, lock_st)

            # compare the input password which is correct or not
            if ccs_enter == '1':

                print('Checking....')
                time.sleep(T)
                print(
                    'verified password\nSecurity Clearance Category[Confidential] --> YOU ARE WELCOME!')
                led_green.write(1)
                buzzer.write(1)
                time.sleep(t)
                led_green.write(0)
                buzzer.write(0)
                break

            elif ccs_enter == '2':

                print('Checking....')
                time.sleep(T)
                print(
                    'verified password\nSecurity Clearance Category[Secret] --> YOU ARE WELCOME!')
                led_green.write(1)
                buzzer.write(1)
                time.sleep(t)
                led_green.write(0)
                buzzer.write(0)
                break

            elif ccs_enter == '3':

                print('Checking....')
                time.sleep(T)
                print(
                    'verified password\nSecurity Clearance Category[Top Secret] --> YOU ARE WELCOME!')
                led_green.write(1)
                buzzer.write(1)
                time.sleep(t)
                led_green.write(0)
                buzzer.write(0)
                break

            # if the password is wrong giving a warning to the control unit
            elif ccs_enter == '4':
                print('Checking....')
                time.sleep(T)
                print('access denied\nWARNING!!!')
                led_red.write(1)
                buzzer.write(1)
                reset = rst.read()
                if reset == 1:
                    reset1()
                    break
            elif ccs_enter == '5':
                pass


def pressure():
    '''defined a function for floor pressure sensor'''
    print("Pressure sensor")
    # reading weather there is a pressure difference
    if fpressure.read() == None:
        pass
    elif fpressure.read() == 1:
        client.publish(topic_2, 1)
        if ccs_alarm == "1":
            for i in range(10):
                # if there is a pressure difference giving a warning
                print('!!!WARNING!!!')
                led_orange.write(1)
                buzzer.write(1)
                time.sleep(1)
    else:
        print('Safe')
        time.sleep(1)


def ldr():
    '''defined a function for light intensity sensor'''
    print("light intensity sensor")
    # reading that if there is a difference of light intensity beacause of a motion
    sensval = LDR.read()
    client.publish(topic_3, sensval)

    if ccs_alarm == "1":
        while True:
            # found a motion and giving warning

            led_orange.write(1)
            buzzer.write(1)
            reset = rst.read()
            if reset == 1:
                reset1()
                break
    time.sleep(1)


def tem():
    '''defined a function for temperature sensor'''
    print("temperature sensor")

   # values of the constant that include in the Temp equation

    A = 0.00604
    B = -0.0008
    C = 0.0000079

    # calculate the temperature

    v = tempt.read()
    if isinstance(v, float):
        r = 1000*(1-v)/v
        Temp = round(((A + B*math.log(r) + C*(math.log(r))**3)**(-1)-273), 3)
        print('Temperature', Temp, 'C')
        client.publish(topic_1, Temp)

        # weather there is a fire gives warning
        if ccs_alarm == "1":
            print('FIRE ALARM WARNING!!!')
            buzzer.write(1)
            led_orange.write(1)

    time.sleep(1)


def reset1():
    led_green.write(0)
    led_red.write(0)
    led_orange.write(0)
    buzzer.write(0)


while True:

    tem()
    pressure()
    ldr()

    if ccs_alarm == "1":
            for i in range(10):
                # if there is a pressure difference giving a warning
                print('!!!WARNING!!!')
                led_orange.write(1)
                buzzer.write(1)
                time.sleep(1)
    

    # if someone try to enter to the room by entering password, giving space to enter it.
    if sq.read() == True:
        pushbutton()

        while True:
            tem()
