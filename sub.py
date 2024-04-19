import paho.mqtt.client as mqtt
import time

# a callback function
def on_message_temperature(client, userdata, msg):
    print('Received a new temperature data ', msg.payload.decode('utf-8'))


def on_message_humidity(client, userdata, msg):
    print('Received a new humidity data ', str(msg.payload.decode('utf-8')))


client = mqtt.Client("greenhouse_server_123")

client.username_pw_set(username="Nhan", password="01212861566nhan")
client.connect('localhost', 1883, 60)
client.subscribe("greenhouse/#")
client.subscribe("odoo/uid/#")

client.message_callback_add('greenhouse/temperature', on_message_temperature)
client.message_callback_add('greenhouse/humidity', on_message_humidity)
# start a new thread
client.loop_start()

while True:
    time.sleep(6)
    # do something you like