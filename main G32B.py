# GP106 Project
# Group B - President's Room
# Authors -
# I.W.C.Nandasiri(E/19/252)
# W.S.N.Nemindara(E/19/259)
# M.S.N.Perera(E/19/283)
# T.B.Meegahakotuwa(E/19/239)

# Importing required Libraries
import pyfirmata
import time
import math
import numpy as np
from threading import Thread, Event

import paho.mqtt.client as mqtt

# Setup
group = "G32B"
topic_1 = "G32B/PO/TEMP"
topic_2 = "G32B/PO/PANIC"
topic_3 = "G32B/PO/KNOCK"

topic_4 = "G32B/PO/ALARM"

mqttBroker = "vpn.ce.pdn.ac.lk"  # Must be connected to the vpn
mqttPort = 8883


# The callback for when the client receives a CONNACK response from the server.


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(topic_1)
    client.subscribe(topic_2)
    client.subscribe(topic_3)
    client.subscribe(topic_4)


# The callback for when a PUBLISH message is received from the server.


def on_message(client, userdata, msg):
    # print(msg.topic+" "+str(msg.payload))
    if msg.topic == "G32B/PO/ALARM":
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

# ports and pins
port = 'COM3'
board = pyfirmata.Arduino(port)
pin = 8
pin1 = 9
Green = 11
Blue = 10
Red = 12

# Temperature value (Analog) input
Tv1 = board.get_pin('a:0:i')

# Panic button (Analog) input
ir1 = board.get_pin('a:1:i')

# Inputs for secret knock (Digital Port)
i1 = board.get_pin('d:2:i')
i2 = board.get_pin('d:3:i')
i3 = board.get_pin('d:4:i')
i4 = board.get_pin('d:5:i')

# start the utilization service
# this service will handle communication overflows while communicating,
# with the Arduino board via USB intrface .

iterator = pyfirmata.util.Iterator(board)
iterator.start()

# Required password defined for Secret Knock
Req_Password = ['A', 'K', 'B', 'A', 'R']

# initial Counter Value
q, m, n, p = 0, 0, 0, 0

# Event object used to send signals from one thread to another


while True:
    # Coding for Temperature Sensor
    while q < 5:
        time.sleep(0.02)
        # Calculated Resistance of the Thermister due to Temperature differances
        a = 10000 * (1 - Tv1.read()) / Tv1.read()
        # Temperature in Kelvin units
        TK = 1 / ((1 / (1599.472) * np.log(a / 918) + (1 / 298.15)))
        # Temperature in Celcius units(Int val)
        TC = int(TK - 273.15)
        client.publish(topic_1, TC)

        # When there is no Fire Situation
        if ccs_alarm != '1':
            print(TC, 'FIRE ALERT')
            board.digital[Green].write(1)
            time.sleep(0.1)
            board.digital[Green].write(0)
            q = 6

        # When there is a Fire Situation
        else:
            # Output of the Buzzer
            led_pin = 8
            board.digital[led_pin].mode = pyfirmata.OUTPUT

            print(TC, "NO DANGER")
            board.digital[led_pin].write(1)
            board.digital[Red].write(1)
            time.sleep(1)
            board.digital[led_pin].write(0)
            board.digital[Red].write(0)
            time.sleep(0.2)
            q = 6

        q = q + 1

    # Code for Panic Button
    while m < 5:
        Value = str(ir1.read())  # Input of the Panic Button
        # When Panic Button Gives None
        if Value == 'None':
            pass
        else:
            client.publish(topic_2, 1)
            # When Panic Button has a value other than 0.0
            if ccs_alarm != '0.0':
                print('PB')
                client.publish(topic_2, 1)
                board.digital[pin].write(1)
                board.digital[Red].write(1)
                time.sleep(3)
                board.digital[pin].write(0)
                board.digital[Red].write(0)
                m = 6

            else:
                print(Value)
                client.publish(topic_2, 0)
                board.digital[Blue].write(1)
                time.sleep(0.1)
                board.digital[Blue].write(0)

                m = 6
    q = 0
    m = 0

    # Check conditions whether Secrect Knock is Started or Not
    if str(i4.read()) == 'True':  # Convert Digital Input to String and Check
        Input_password = []
        while p < 5:
            stop_event = Event()


            def do_actions():
                """
                Function that should timeout after 5 seconds. It simply prints a number and waits 1 second.
                :return:
                """
                n = 0
                print("START ENTERING SECRECT KNOCK KNOCK")
                board.digital[pin1].write(1)
                time.sleep(1)

                while n < 5:
                    Value1 = str(i1.read())
                    Value2 = str(i2.read())
                    Value3 = str(i3.read())
                    Value4 = str(i4.read())
                    time.sleep(0.5)

                    if Value1 == 'True':
                        Input_password.append('A')
                        print('Done 1')
                        n += 1
                    elif Value2 == 'True':
                        Input_password.append('B')
                        print('Done 2')
                        n += 1
                    elif Value3 == 'True':
                        Input_password.append('K')
                        print('Done 3')
                        n += 1
                    elif Value4 == 'True':
                        Input_password.append('R')
                        print('Done 4')
                        n += 1

                    # Here we make the check if the other thread sent a signal to stop execution.
                    if stop_event.is_set():
                        break


            if __name__ == '__main__':
                # We create another Thread
                action_thread = Thread(target=do_actions)

                # Here we start the thread and we wait 30 seconds before the code continues to execute.
                action_thread.start()
                action_thread.join(timeout=30)

                # We send a signal that the other thread should stop.
                stop_event.set()
                in_str=''
                for i in Req_Password:
                    client.publish(topic_3,in_str)

                if ccs_alarm == '0':
                    print('ACCESS GRANTED')
                    board.digital[Green].write(1)
                    time.sleep(3)
                    board.digital[Green].write(0)
                else:
                    board.digital[pin].write(1)
                    board.digital[Red].write(1)
                    print("WARNING UNAUTHORIZED ACCESS")
                    time.sleep(3)
                    board.digital[pin].write(0)
                    board.digital[Red].write(0)
                p, n = 5, 5
        n, p = 0, 0
        board.digital[pin1].write(0)
    else:
        pass

