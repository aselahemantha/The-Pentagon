from pyfirmata import Arduino, util, INPUT, OUTPUT, PWM
import paho.mqtt.client as mqtt

# Setup to  communicate with MQTT broker

group = "G32C"

# Initiate topics

topic_0 = "G32A/CDR/TEMPOUT"
topic_1 = "G32A/CDR/LIGHTOUT"
topic_2 = "G32A/CDR/PRESOUT"
topic_3 = "G32A/CDR/SEQOUT"

topic_4 = "G32B/PO/TEMPOUT"
topic_5 = "G32B/PO/KNOCKOUT"
topic_6 = "G32B/PO/PANICSOUT"

topic_7 = "G32C/CCC/TEMPOUT"
topic_8 = "G32C/CCC/SMOKEOUT"
topic_9 = "G32C/CCC/MORSEOUT"

topic_10 = "G32A/CCS/ALARM"
topic_11 = "G32B/CCS/ALARM"
topic_12 = "G32C/CCS/ALARM"
topic_13 = "G32A/CDR/CDRENTER"

mqttBroker = "vpn.ce.pdn.ac.lk"  # Must be connected to the vpn
mqttPort = 8883

# The callback for when the client receives a CONNACK response from the server.

tempCDR, light_intensity, pressure, tempPO, panic, tempCCC = 0, 0, 0, 0, 0, 0
seq, knock, decrypt_code = '', '', ''


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(topic_0)
    client.subscribe(topic_1)
    client.subscribe(topic_2)
    client.subscribe(topic_3)
    client.subscribe(topic_4)
    client.subscribe(topic_5)
    client.subscribe(topic_6)
    client.subscribe(topic_7)
    client.subscribe(topic_8)
    client.subscribe(topic_9)
    client.subscribe(topic_10)
    client.subscribe(topic_11)
    client.subscribe(topic_12)
    client.subscribe(topic_13)


# The callback for when a PUBLISH message is received from the server.


def on_message(client, userdata, msg):
    '''
    Get relevant data using the MQTT broker according to the topic.

    '''

    if msg.topic == "G32A/CDR/TEMPOUT":
        global tempCDR
        tempCDR = msg.payload.decode('utf-8')
    if msg.topic == "G32A/CDR/LIGHTOUT":
        global light_intensity
        light_intensity = msg.payload.decode('utf-8')
    if msg.topic == "G32A/CDR/PRESOUT":
        global pressure
        pressure = msg.payload.decode('utf-8')
    if msg.topic == "G32A/CDR/SEQOUT":
        global seq
        seq = msg.payload.decode('utf-8')
    if msg.topic == "G32B/PO/TEMPOUT":
        global tempPO
        tempPO = msg.payload.decode('utf-8')
    if msg.topic == "G32B/PO/KNOCKOUT":
        global knock
        knock = msg.payload.decode('utf-8')
    if msg.topic == "G32B/PO/PANICSOUT":
        global panic
        panic = msg.payload.decode('utf-8')
    if msg.topic == "G32C/CCC/TEMPOUT":
        global tempCCC
        tempCCC = msg.payload.decode('utf-8')
    if msg.topic == "G32C/CCC/SMOKEOUT":
        global smoke
        smoke = msg.payload.decode('utf-8')
    if msg.topic == "G32C/CCC/MORSEOUT":
        global decrypt_code
        decrypt_code = msg.payload.decode('utf-8')


client = mqtt.Client(group)  # Controll Centre Room


try:
    client.connect(mqttBroker, mqttPort)
    client.on_connect = on_connect
    client.on_message = on_message
    client.loop_start()
except:
    print("Connection to MQTT broker failed!")
    exit(1)


board = Arduino("COM5")


it = util . Iterator(board)
it . start()


while True:

    '''
    If the temperature value is greater than 50 C in any room, this will send a request to the 
    relevant room to call the alarm function and buzz the alarm and blink the LEDs.
    '''

    try:
        if tempCDR > 50:
            print('Temperture is HIgh in CDR')
            client.publish(topic_10, 1)

        if tempPO > 50:
            print('Temperture is HIgh in PO')
            client.publish(topic_11, 1)

        if tempCCC > 50:
            print('Temperture is HIgh in CCC')
            client.publish(topic_12, 1)
    except:
        pass

    ''' 
    Checking whether the entered password is correct. In our case
    our password is EEE
    '''

    if decrypt_code == 'EEE':

        '''
        In case of someone entered the correct password, this will 
        send a request to CCC to call the unlock function and open the door.
        '''

        print("Your password is correct\n Door Unlocked")
        client.publish(topic_12, 0)

    else:

        '''
        In case of someone entered the correct password, this will 
        send a request to CCC to call the alarm function and lock the CCC.

        '''

        print("Security Issue! Wrong password")
        client.publish(topic_12, 2)

    '''
    If the light intensity of the CDR is unusual, this will 
    send a request to CDR to call the alarm function and lock the CDR.

    '''

    if light_intensity == None:
        pass

    elif 0.05 < float(light_intensity) < 0.2:
        print('Safe Here')

    else:
        print('Security Isuue !')
        client.publish(topic_10, 1)

    '''
    If the pressure sensor detect any value from the CDR, this will 
    send a request to CDR to call the alarm function and lock the CDR.

    '''

    if pressure == '1':
        client.publish(topic_10, 1)
    else:
        print('Safe')
        client.publish(topic_10, 0)

    '''
    This reads the Entred sequence and checks whether is it a password according to the clearance categories. If it is a password, this sends a request to the CDR to open the door. Else  
    send a request to CDR to call the alarm function and lock the CDR.

    '''

    # passswords for clearance categories
    psw1 = 'AABB'
    psw2 = 'ABAB'
    psw3 = 'BBAA'

    print(seq)
    if seq == psw1:
        client.publish(topic_13, 1)
    elif seq == psw2:
        client.publish(topic_13, 2)
    elif seq == psw3:
        client.publish(topic_13, 3)
    elif seq == '':
        client.publish(topic_13, 5)
    else:
        client.publish(topic_13, 4)

    '''
    This reads the Entred Knock in PO and checks whether is it corrected or not. If it is correct, this sends a request to the PO to open the door. Else  
    send a request to PO to call the alarm function and lock the CDR.
    '''

    req_knock = 'AKBAR'

    if knock == req_knock:
        print('ACCESS GRANTED')
        client.publish(topic_11, 0)

    else:
        print("WARNING UNAUTHORIZED ACCESS")
        client.publish(topic_11, 1)

    '''
    This continuously reads the panic button state to identify is there any suspicious activity in PO. If so the person in the Po can push the panic button and then, sends 
    a request to the PO to indicate it and buzz the alarm in the PO.
    '''

    if panic != '0.0':
        print("PB")
        client.publish(topic_11, 1)
