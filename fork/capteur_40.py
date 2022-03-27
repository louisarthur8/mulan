#!/usr/bin/python
# coding=utf-8
 
# Les modules nécessaires sont importés et mis en place
import RPi.GPIO as GPIO
import time
 
GPIO.setmode(GPIO.BCM)
 
# Déclaration des broches d'entrée auxquelles est raccordé le capteur
PIN_CLK = 16
PIN_DT = 15
BUTTON_PIN = 14
 
GPIO.setup(PIN_CLK, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(PIN_DT, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down = GPIO.PUD_UP)
 
# Les variables nécessaires sont initialisées
Counter = 0
Direction = True
PIN_CLK_LETZTER = 0
PIN_CLK_AKTUELL = 0
delayTime = 0.01
 
# Lecture initiale de Pin_CLK
PIN_CLK_LETZTER = GPIO.input(PIN_CLK)
 
# Cette fonction de sortie est exécutée par détection d'un signal
def ausgabeFunktion(null):
    global Counter
 
    PIN_CLK_AKTUELL = GPIO.input(PIN_CLK)
 
    if PIN_CLK_AKTUELL != PIN_CLK_LETZTER:
 
        if GPIO.input(PIN_DT) != PIN_CLK_AKTUELL:
            Counter += 1
            Direction = True;
        else:
            Direction = False
            Counter = Counter - 1
 
        print("Rotation détectée: ")
        
        file = open("data.txt", "w");
 
        if Direction:
            print("Sens de rotation: sens des aiguilles d'une montre")
            file.write("Sens de rotation: sens des aiguilles d'une montre, Position actuelle: " + str(Counter));
            file.write("------------------------------");
        else:
            print("Sens de rotation: sens contraire des aiguilles d'une montre")
            file.write("Sens de rotation: sens contraire des aiguilles d'une montre, Position actuelle: " + str(Counter));
            file.write("------------------------------");
            
        file.close;
 
        print("Position actuelle: " + str(Counter))
        print("------------------------------")
        if Counter > 10 or Counter < -10:
            exit(0)
 
def CounterReset(null):
    global Counter
 
    print("Position remise à 0!")
    print("------------------------------")
    Counter = 0
 
# Pour intégrer directement un temps de stabilisation, on initialise
# les GPIO au moyen de l'option CallBack
GPIO.add_event_detect(PIN_CLK, GPIO.BOTH, callback=ausgabeFunktion, bouncetime=50)
GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=CounterReset, bouncetime=50)
 
 
print("Sensor-Test [Appuyez sur Ctrl + C pour terminer le test]")
 
# Boucle de programme principale
try:
        while True:
            time.sleep(delayTime)
 
# réinitialisation de tous les GPIO en entrées
except KeyboardInterrupt:
    GPIO.cleanup()