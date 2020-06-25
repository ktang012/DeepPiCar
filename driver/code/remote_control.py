import logging
import cv2
import os
import picar
import argparse
from datetime import datetime
from pynput import keyboard

class PiCar:
    __SCREEN_WIDTH = 640
    __SCREEN_HEIGHT = 480
    
    def __init__(self):
        picar.setup()
        self.camera = cv2.VideoCapture(-1)
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        # self.capture_out = cv2.VideoWriter("")
        # self.angles_fname = ""
        
        self.camera.set(3, self.__SCREEN_WIDTH)
        self.camera.set(4, self.__SCREEN_HEIGHT)
        self.pan_servo = picar.Servo.Servo(1)
        self.pan_servo.offset = -40 # calibrate servo to center (left, right)
        self.pan_servo.write(90)

        self.tilt_servo = picar.Servo.Servo(2)
        self.tilt_servo.offset = -120  # calibrate servo to center (up, down)
        self.tilt_servo.write(90)

        logging.debug('Set up back wheels')
        self.back_wheels = picar.back_wheels.Back_Wheels()
        self.back_wheels.speed = 0  # Speed Range is 0 (stop) - 100 (fastest)

        logging.debug('Set up front wheels')
        self.front_wheels = picar.front_wheels.Front_Wheels()
        self.front_wheels.turning_offset = 20# calibrate servo to center
        self.front_wheels.turn(90)  # Steering Range is 45 (left) - 90 (center) - 135 (right)

class RemoteControlPiCar:
    def __init__(self, steer_step_size=5, speed=80, save_img=False):
        logging.info("Creating RemoteControl...")
        self.car = PiCar()
        self.steer_step_size = steer_step_size
        self.curr_steering_angle = 90
        self.speed = 60
        self.save_img = save_img
        self.key_map = {
            "w": "forward",
            "s": "backward",
            "a": "left",
            "d": "right"
        }
        
    def __enter__(self):
        """ Entering a with statement """
        return self

    def __exit__(self, _type, value, traceback):
        """ Exit a with statement"""
        if traceback is not None:
            # Exception occurred:
            logging.error('Exiting with statement with exception %s' % traceback)

        self.cleanup()

    def cleanup(self):
        """ Reset the hardware"""
        logging.info('Stopping the car, resetting hardware.')
        self.car.back_wheels.speed = 0
        self.car.front_wheels.turn(90)
        self.car.camera.release()
        cv2.destroyAllWindows()
    
    def steer(self, key):
        if isinstance(key, keyboard.KeyCode):
            if key.char == "a" or key.char == "d":
                direction = self.key_map[key.char]
                new_angle = self.curr_steering_angle
                if direction == "left":
                    new_angle -= self.steer_step_size
                    self.curr_steering_angle = max(45, new_angle)
                else:
                    new_angle += self.steer_step_size
                    self.curr_steering_angle = min(135, new_angle)

                self.car.front_wheels.turn(self.curr_steering_angle)
            elif key.char == "q":
                return False
        
    def move(self, key):
        if isinstance(key, keyboard.KeyCode):
            if key.char == "w" or key.char == "s":
                direction = self.key_map[key.char]
                self.car.back_wheels.speed = self.speed
                if direction == "forward":
                    self.car.back_wheels.backward() #swapped??
                else:
                    self.car.back_wheels.forward()

                
            elif key.char == "q":
                return False
    
    def stop(self, key):
        if isinstance(key, keyboard.KeyCode):
            if key.char == "w" or key.char == "s":
                self.car.back_wheels.speed = 0
            elif key.char == "q":
                return False
        
    def save_frame_and_angle(self, frame, path):
        filename = datetime.now().strftime("%m-%d-%y-%H:%M:%S:%f") + "_angle-" + str(self.curr_steering_angle) + "_speed-" + str(self.speed) + ".png"
        cv2.imwrite(os.path.join(path, filename), frame)
        print("saved to ", os.path.join(path, filename))
    
    def drive(self):
        DATA_DIR = os.path.join("..", "data", "lane_navigation")
        front_listener = keyboard.Listener(on_press=self.steer)
        back_listener = keyboard.Listener(on_press=self.move, on_release=self.stop)
        
        front_listener.start()
        back_listener.start()
        print("Started remote control!")
        while self.car.camera.isOpened():
            _, frame = self.car.camera.read()
            cv2.imshow("View", frame)
            
            # self.capture_out.write(frame)
            # append to self.angles_fname
            
            cv2.waitKey(1)
            if self.save_img:
                self.save_frame_and_angle(frame, DATA_DIR)
            
            if not (front_listener.running or back_listener.running):
                self.cleanup()
                break
            
            

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Set speed, angle change rate, and whether to save images")
    parser.add_argument("-s", "--speed", default=40, type=int, help="speed of backwheels")
    parser.add_argument("-a", "--angle", default=2, type=int, help="rate of change of steering angle in degrees")
    parser.add_argument("-i", "--image", default=False, type=bool, help="saving images")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)-5s:%(asctime)s: %(message)s')
    with RemoteControlPiCar(steer_step_size=args.angle, speed=args.speed, save_img=args.image) as car:
        car.drive()
    
            
        
