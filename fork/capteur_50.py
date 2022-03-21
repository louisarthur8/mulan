# coding=utf-8
import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

Trigger_AusgangsPin = 17
Echo_EingangsPin    = 27

sleeptime = 0.8

GPIO.setup(Trigger_AusgangsPin, GPIO.OUT)
GPIO.setup(Echo_EingangsPin, GPIO.IN)
GPIO.output(Trigger_AusgangsPin, False)

try:
    while True:
        GPIO.output(Trigger_AusgangsPin, True)
        time.sleep(0.00001)
        GPIO.output(Trigger_AusgangsPin, False)

        EinschaltZeit = time.time()
        while GPIO.input(Echo_EingangsPin) == 0:
            EinschaltZeit = time.time()
 
        while GPIO.input(Echo_EingangsPin) == 1:
            AusschaltZeit = time.time()

        Dauer = AusschaltZeit - EinschaltZeit
        Abstand = (Dauer * 34300) / 2

        if Abstand < 2 or (round(Abstand) > 300):
            print("Distance hors de la plage de mesure")
            print("------------------------------")
        else:
            Abstand = format((Dauer * 34300) / 2, '.2f')
            print("La distance est de " + Abstand + "cm")
            print("------------------------------")
            file = open("data.txt", "w");
            file.write(Abstand);
            file.close;
            exit(0)

        time.sleep(sleeptime)

except KeyboardInterrupt:
    GPIO.cleanup()