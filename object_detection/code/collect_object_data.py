import time
import os
import logging
import cv2
import picar
from datetime import datetime


class PiCamera:
    __SCREEN_WIDTH = 640
    __SCREEN_HEIGHT = 480
    
    def __init__(self):
        picar.setup()
        self.camera = cv2.VideoCapture(-1)
        self.camera.set(3, self.__SCREEN_WIDTH)
        self.camera.set(4, self.__SCREEN_HEIGHT)
        self.pan_servo = picar.Servo.Servo(1)
        self.pan_servo.offset = -40 # calibrate servo to center (left, right)
        self.pan_servo.write(90)

        self.tilt_servo = picar.Servo.Servo(2)
        self.tilt_servo.offset = -120  # calibrate servo to center (up, down)
        self.tilt_servo.write(90)
    
    def __enter__(self):
        """ Entering a with statement """
        return self

    def __exit__(self, _type, value, traceback):
        """ Exit a with statement"""
        if traceback is not None:
            # Exception occurred:
            logging.error('Exiting with statement with exception %s' % traceback)

        self.camera.release()
    
    def capture(self, path, frame):
        filename = datetime.now().strftime("%m-%d-%y-%H:%M:%S:%f") + "_objects.png"
        cv2.imwrite(os.path.join(path, filename), frame)
        logging.info("Saved image " + filename + " to " + path)
    
    def run(self):
        path = os.path.join("..", "data", "my_images")
        while self.camera.isOpened():
            _, frame = self.camera.read()
            cv2.imshow("View", frame)
            # need to focus on viewer to capture image
            key_val = cv2.waitKey(1) & 0xFF
            if key_val == ord(" "):
                self.capture(path, frame)
            elif key_val == ord("q"):
                self.camera.release()
                break
                
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)-5s:%(asctime)s: %(message)s')
    with PiCamera() as camera:
        camera.run()
