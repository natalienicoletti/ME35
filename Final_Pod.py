import RPi.GPIO as GPIO
import time
import requests 
import json 
GPIO.setmode(GPIO.BOARD)

# Define the GPIO pins for the L298N motor driver
OUT1 = 12
OUT2 = 11
OUT3 = 13
OUT4 = 15

# Set the GPIO pins as output
GPIO.setup(OUT1, GPIO.OUT)
GPIO.setup(OUT2, GPIO.OUT)
GPIO.setup(OUT3, GPIO.OUT)
GPIO.setup(OUT4, GPIO.OUT)

GPIO.output(OUT1,GPIO.LOW)
GPIO.output(OUT2,GPIO.LOW)
GPIO.output(OUT3,GPIO.LOW)
GPIO.output(OUT4,GPIO.LOW)
global num_steps
num_steps= 30 #30 
step_delay = 0.02 




id_lid = 'rec6fXBaEC66YP9Jv'
id_pod = 'recatsvIkEZPjXhbS'
id_coffee_done = 'recGzal1MiC7xAezn'

URL = 'https://api.airtable.com/v0/applK0NRaebYim73c/Control_Table'

Headers = {'Authorization':'Bearer patdq1umq6dz00Wjg.1fa65436b75bc5e22d7d04d39029973f64a8cc0c2057984e84e58a1947f50132'}

def get_airtable_value(index):
    try:
        response2 = requests.get(URL, headers=Headers)
        data2 = response2.json()
        value2 = data2['records'][index]['fields']['Value']

        
        if value2 == 1:
            #print(value2)
            return int(value2)
        elif value2 == 0:
            #print(value2)
            return int(value2)
        elif value2 != 1:
            print("Have not received close lid")
            return None
    except Exception as e:
        print("Exception occurred:", str(e))
        return None

def update_airtable_value(id,new_value, URL):
    try:
        # Construct the data payload for updating the record
        data = {'fields': {'Value': str(new_value)}}
        
        
        # Make a PATCH request to update the record with the new value
     
        response = requests.patch(f'{URL}/{id}', headers=Headers, json=data)
        
        # Check if the update was successful
        if response.status_code == 200:
            print("Airtable value updated successfully")
        else:
            print("Error updating Airtable value:", response.status_code)
    except Exception as e:
        print("Exception occurred while updating Airtable:", str(e))

try:
    pod_in = 0
    update_airtable_value(id_pod, pod_in, URL)
    while True:   
        r = requests.get(url = URL, headers = Headers, params = {})
        data = r.json()
        #print(data)
        lid_open = get_airtable_value(0)
        print("lid", lid_open)
        print("pod", pod_in)
        print(type(pod_in))
        print(type(lid_open))

        button_status = get_airtable_value(5)
        current_step = 0
        if ((lid_open == 1) and (pod_in == 0)):
             # current_step = 0
             for x in range(num_steps):
                if current_step == 0:
                    GPIO.output(OUT1,GPIO.HIGH)
                    GPIO.output(OUT2,GPIO.LOW)
                    GPIO.output(OUT3,GPIO.LOW)
                    GPIO.output(OUT4,GPIO.HIGH)
                    time.sleep(step_delay)
                    #print("step 0")
                elif current_step == 1:
                    GPIO.output(OUT1,GPIO.LOW)
                    GPIO.output(OUT2,GPIO.HIGH)
                    GPIO.output(OUT3,GPIO.LOW)
                    GPIO.output(OUT4,GPIO.HIGH)
                    time.sleep(step_delay)
                    #print("step 1")
                elif current_step == 2:
                    GPIO.output(OUT1,GPIO.LOW)
                    GPIO.output(OUT2,GPIO.HIGH)
                    GPIO.output(OUT3,GPIO.HIGH)
                    GPIO.output(OUT4,GPIO.LOW)
                    time.sleep(step_delay)
                elif current_step == 3:
                    GPIO.output(OUT1,GPIO.HIGH)
                    GPIO.output(OUT2,GPIO.LOW)
                    GPIO.output(OUT3,GPIO.HIGH)
                    GPIO.output(OUT4,GPIO.LOW)
                    time.sleep(step_delay)
                if current_step == 3:
                    current_step = 0
                    continue 
                current_step = current_step + 1
                #print(x)
                #print(num_steps -1) 
                if x == (num_steps-1):
                    pod_in = 1
                    print("hello", pod_in)
                    update_airtable_value(id_pod, pod_in, URL)
        elif (lid_open == 0 and button_status == 1):
            pod_in = 0
            update_airtable_value(id_pod, pod_in, URL)
        # GPIO.cleanup()
        # break    
                    
except KeyboardInterrupt:
    GPIO.cleanup()
