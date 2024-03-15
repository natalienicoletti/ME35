import sys
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
# Import the dock action
from irobot_create_msgs.action import RotateAngle
from geometry_msgs.msg import Twist
from keras.models import load_model  # TensorFlow is required for Keras to work
import cv2  # Install opencv-python
import numpy as np
from picamera2 import Picamera2
from libcamera import controls
from collections import Counter
import time
from rclpy.qos import qos_profile_sensor_data
from irobot_create_msgs.msg import IrIntensityVector
# Disable scientific notation for clarity
np.set_printoptions(suppress=True)
# Load the model and labels
model = load_model("keras_model.h5", compile=False)
class_names = open("labels.txt", "r").readlines()
# dictionary for directions - input correct directions once determined
object_directions = {
    'Kiwi': 'right',
    'Elephant': 'right',
    'Bear': 'right',
    'Cube': 'right',
    'Vader': 'left',
    'Mug': 'left',
    'Mario': 'left',
    'Floor': 'straight' 
}

# setup for picam
picam2 = Picamera2() # assigns camera variable
picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous}) # sets auto focus mode
picam2.start() # activates camera
time.sleep(1) # wait for camera to start up

num_avg = 5

# Define the class DockActionClient as a subclass of Node
class RotateAngleClient(Node):

    # Define a function to initalize the node
    def __init__(self):

        # Initialize a node the name dock_action_client
        super().__init__('rotate_angle_action_client')
        
        # Create an action client using the action type 'RotateAngle' that we imported above 
        # with the action name 'rotate_angle' which can be found by running ros2 action list -t
        self._action_client = ActionClient(self, RotateAngle, 'rotate_angle')
        # initalize publisher to drive
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        self.object_list = []
        self.count_confirmed = []
        # set timer 
        timer_period = 1 
        #creates timer that triggers a callback function
        self.timer = self.create_timer(timer_period, self.timer_callback)
        # initialize timer to be zero
        self.i = 0 
        
        # initialize a subscriber to read distance values
        #super().__init__('IR_subscriber')
        self.subscription = self.create_subscription(IrIntensityVector, '/ir_intensity', self.listener_callback, qos_profile_sensor_data)

    def listener_callback(self, msg:IrIntensityVector):
        '''
        The subscriber's callback listens and as soon as it receives the message,
        this function runs. 
        This callback function is basically printing what it hears. It runs the data
        it receives in your terminal (msg).  
        '''
        print('Now listening to IR sensor readings it hears...')

        self.printIR(msg)

    def printIR(self, msg):
        '''
        This function is used in the above function. Its purpose is to determine 
        which parts of the info are worth showing.
        :type msg: IrIntensity
        :rtype: None
        The msg is returned from our topic '/ir_intensity.'
        To get components of a message, use the '.' dot operator. 
        '''
        print('Printing IR sensor readings:')
        i = 0
        for reading in msg.readings: 
            val = reading.value
            if i == 3:
                val = reading.value
            i = i +1
        print(val) 
        return val

    def timer_callback(self):
        
        # Assigns message type "Twist" that has been imported from the std_msgs module above
        msg = Twist() 
        msg.linear.x = .1
        # Publishes `msg` to topic 
        self.publisher.publish(msg)
        # Prints `msg.data` to console
        self.get_logger().info('Publishing: "%s"' % msg.linear.x)
        # go back to processing and respond 
        self.process_and_respond() 
    # Define a function to send the goal to the action server which is already
    # running on the Create 3 robot. Since this action does not require any request value
    # as part of the goal message, the only argument of this function is self. 
    # For more details on this action, review  
    # https://github.com/iRobotEducation/irobot_create_msgs/blob/humble/action/Dock.action
    def send_goal(self, direction):

        # Create a variable for the goal request message to be sent to the action server
        goal_msg = RotateAngle.Goal()
        if direction == 'right': 
            goal_msg.angle = (-3.1415/2)
            goal_msg.max_rotation_speed = .1      
        elif direction == 'left': 
            goal_msg.angle = (3.1415/2) 
            goal_msg.max_rotation_speed = .1    
        

        # Instruct the action client to wait for the action server to become available
        self._action_client.wait_for_server()

        # Sends goal request to the server, returns a future object to the _send_goal_future
        # attribute of the class, and creates a feedback callback as a new function which
        # we will define below as 'feedback_callback' 
        self._send_goal_future = self._action_client.send_goal_async(goal_msg, feedback_callback=self.feedback_callback)
        # Creates a callback that executes a new function 'goal_response_callback'
        # when the future is complete. This function is defined below.
        # This happens when the action server accepts or rejects the request
        self._send_goal_future.add_done_callback(self.goal_response_callback)
        self.process_and_respond()
    
    # Define a response callback for when the future is complete. This will 
    # tell us if the goal request has been accepted or rejected by the server.
    # Note that because we have a future object we need to pass that in as 
    # an argument of this function.
    def goal_response_callback(self, future):

        # Store the result of the future as a new variable named 'goal_handle'
        goal_handle = future.result()

        # Perform an initial check to simply see if the goal was accepted or rejected 
        # and print this to the logger.
        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected :(')
            return

        self.get_logger().info('Goal accepted :)')

        # Now that we know the goal was accepted and we should expect a result,
        # ask for that result and return a future when received. 
        self._get_result_future = goal_handle.get_result_async()

        # Creates a callback that executes a new function 'get_result_callback'
        # when the future is complete. This function is defined below.
        # This happens when the action server accepts or rejects the request
        self._get_result_future.add_done_callback(self.get_result_callback)
    
    # Define a result callback for when the future is complete. This will 
    # tell us the result sent to us from the server.
    # Note that because we have a future object we need to pass that in as 
    # an argument of this function.
    def get_result_callback(self, future):

        # Store the result from the server in a 'result' variable
        result = future.result().result

        # Print the result to the logger. We know what to ask for 'result.is_docked'
        # based on the action documentation for the dock action
        self.get_logger().info('Result: {0}'.format(result.pose))
        # check imgage here
        # Shut down rclpy
        rclpy.shutdown()

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().info('Received feedback: {0}'.format(feedback.remaining_angle_travel))

    # def identify(self, object_list):
    #     count_dict = Counter(object_list)
    #     most_common_object = count_dict.most_common(1)[0][0]
    #     return most_common_object, count_dict
    
    def process_and_respond(self):
        while True:
            # Grab the picam's image.
            image = picam2.capture_array("main")
            # Discard alpha channel
            image_3_channel = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
            # Resize the image
            image_resized = cv2.resize(image_3_channel, (224, 224), interpolation=cv2.INTER_AREA)
            # check image size is as expected 
            # Show the image in a window
            cv2.imshow("Picam Image", image)
            
            # Make the image a numpy array and reshape it to the models input shape.
            image = np.asarray(image_resized, dtype=np.float32).reshape(1, 224, 224, 3)
            # Normalize the image array
            image = (image / 127.5) - 1
            # Predicts the model
            prediction = model.predict(image)
            index = np.argmax(prediction)
            class_name = class_names[index]
            confidence_score = prediction[0][index]
            rounded_confidence_score = np.round(confidence_score * 100)
            # creates list of 10 most recent objects
            self.object_list.append(class_name[2:].rstrip('\n')) 
            # the rstrip gets rid of the /n and makes list compatible with dictionary
            if len(self.object_list) > num_avg:
                self.object_list.pop(0)    
            print("last ", num_avg, " objects: ", self.object_list)
            # Print prediction and confidence score
            print("Object:", class_name[2:])
            print("Confidence Score:", str(np.round(confidence_score * 100))[:-2], "%")
            # run function to identify most common object
            count_dict = Counter(self.object_list)
            most_common_object = count_dict.most_common(1)[0][0]
            print("count: ", count_dict[most_common_object])
            print("must be greater than: ", np.round(.9*num_avg))
            '''
            CHANGE CONFIDENCE VALUE IN IF STATEMENT!!! (currently 68)
            # can also tune value for average check (currently .9)
            '''
            # statement to check that object is confirmed 
            #if count_dict[most_common_object] > (np.round(.9*num_avg)) and rounded_confidence_score > 90: 
            if count_dict[most_common_object] > 4 and rounded_confidence_score > 90: 
                object_confirmed = True
            else: 
                object_confirmed = False
            print("object confirmed", object_confirmed)
            '''
            code to check object distance goes here and in if statement below 
            '''
            self.count_confirmed.append(object_confirmed)
            if len(self.count_confirmed) > 2:
                self.count_confirmed.pop(0)  
            confirmed_num = Counter(self.count_confirmed)    
            print("count confirmed: ", self.count_confirmed)
            print("confirmed_num: ", confirmed_num[True])
            if object_confirmed: #and confirmed_num[True] != 2:
                #print("go straight")
            # elif object_confirmed and confirmed_num[True] == 2: # and 6 inches away [INSERT CODE HERE]
                print("it's time to turn")
                direction = object_directions[most_common_object]
                if direction == 'right': 
                    print('turning right')
                    # code to turn right
                    self.send_goal(direction)
                elif direction == 'left': 
                    print('turning left')
                    # code to turn left
                    self.send_goal(direction)
                elif direction == 'straight':
                    print('go straight')
                    # code to go straight
                    self.timer_callback()
                else:
                    print('something weird is happening, check directions')
            else: 
                print('go straight')
                # code to go straight
                self.timer_callback()
            # Listen to the keyboard for presses.
            keyboard_input = cv2.waitKey(1)
            # 27 is the ASCII for the esc key on your keyboard.
            if keyboard_input == 27:
                break

def main(args=None):
    rclpy.init(args=args)
    rotate_class = RotateAngleClient() # making an instance of rotateangle
    rotate_class.process_and_respond()
    rclpy.spin(rotate_class)
    picam2.release()
    cv2.destroyAllWindows()

    # action_client = RotateAngleClient()
    # #action_client.send_goal()
    # rclpy.spin(action_client)

if __name__ == '__main__':
    main()
