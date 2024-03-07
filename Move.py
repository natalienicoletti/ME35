import sys
import rclpy
from rclpy.node import Node
import random
import requests
import json 
from geometry_msgs.msg import Twist #the movement topic

#let's create a function that will move 
class MovePublisher(Node):
    #This class let's us create nodes

    def __init__(self):
        #creating the node
        super().__init__('moving')

        # Creates a publisher based on the message type "Vector3" that has been imported from the std_msgs module above
        # Sets the publisher to publish on the 'my_publisher' topic
        # Sets a queue size of 10 - essentially a backlog of messages if the subscriber isn't receiving them fast enough
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)

        # Set delay in seconds
        timer_period = .3 

        # Creates a timer that triggers a callback function after the set timer_period
        self.timer = self.create_timer(timer_period, self.timer_callback)

        # Sets initial counter to zero
        self.i = 0

    def timer_callback(self):
        #airtable links
        URL = 'https://api.airtable.com/v0/appQD42E9ZkCnflEQ/Table%201'
        Headers = {'Authorization':'Bearer pataHGmUWZLaadsen.47ce907579f6bf5491444d62c8f2da66e6411cb06343cf10bcc251f3c93d56c8'}

        r = requests.get(url = URL, headers = Headers, params = {})
        data = r.json()
        
        # Assigns message type "Twist" that has been imported from the std_msgs module above
        msg = Twist() 
        msg.linear.x = float(data['records'][0]['fields']['Value'])
        msg.angular.z = float(data['records'][1]['fields']['Value'])

        # Publishes `msg` to topic 
        self.publisher.publish(msg) 

        # Prints `msg.data` to console
        self.get_logger().info('Publishing: "%s"' % msg.linear.x) 

def main(args=None):
    rclpy.init(args=args)

    try:
        
        moving = MovePublisher()
        rclpy.spin(moving)

    except KeyboardInterrupt:
        print('\nCaught Keyboard Interrupt')

    finally:
        print("Done")  # Destroy the node explicitly
        #move_publisher.reset()
        moving.destroy_node()
        print('shutting down')
        rclpy.shutdown()
    
if __name__ == '__main__':
    main()