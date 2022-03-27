#Modules required are imported and set up
import RPi. GPIO  as  GPIO
import time
 
GPIO.setmode (GPIO.BCM) 
 
# Here the input pin to which the sensor is connected is declared.
GPIO_PIN = 24
GPIO.setup (GPIO_PIN, GPIO.IN , pull_up_down = GPIO.PUD_UP) 
 
# Pause between output is defined (in seconds) 
delayTime  =  0.5
 
print ("Sensor test [push CTRL+C to stop the test]") 
 
# Main program loop
try:
    while True:
        file = open("data.txt", "w");
        file.write("Obstacle ? : " + str(GPIO.input(GPIO_PIN)));
        file.close;
        if GPIO.input(GPIO_PIN) == True:
            print ("No obstacle") 
        else:
            print ("obstacle detected")
        exit(0)
    
 
        # Reset + Delay
        time.sleep (delayTime) 
 
# Tidying up after the program has been terminated
except KeyboardInterrupt:
    GPIO.cleanup ()