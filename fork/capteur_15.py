import time
import board
import adafruit_dht


dhtDevice = adafruit_dht.DHT11(board.D23)


while True:
    try:
        temperature_c = dhtDevice.temperature
        temperature_f = temperature_c * (9 / 5) + 32
        humidity = dhtDevice.humidity
        file = open("data.txt", "w");
        file.write(str(temperature_f) + " " + str(temperature_c) + " " + str(humidity));
        file.close;
        print("Temp: {:.1f} F / {:.1f} C    Humidity: {}% ".format(temperature_f, temperature_c, humidity))
        exit(0)

    except RuntimeError as error:
        print(error.args[0])
        time.sleep(2.0)
        continue
    except Exception as error:
        dhtDevice.exit()
        raise error

    time.sleep(2.0)
