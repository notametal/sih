/*
  Offline TinyML drying controller — Arduino Uno R3
  ---------------------------------------------------
  No WiFi, no cloud, no laptop required after upload.
  Inference is a compiled decision tree (see model_tree.h).

  Wiring:
    DHT11   VCC   -> 5V
    DHT11   DATA  -> Pin 2
    DHT11   GND   -> GND

    Red LED   Anode -> Pin 5 (through 220-330 ohm resistor)
    Red LED   Cathode -> GND
    Green LED Anode -> Pin 6 (through 220-330 ohm resistor)
    Green LED Cathode -> GND

    Relay module VCC -> 5V
    Relay module GND -> GND
    Relay IN1 -> Pin 8   (Fan power path #1)
    Relay IN2 -> Pin 9   (PTC heater power path)
    Relay IN3 -> Pin 10  (Fan power path #2, ganged with #1)
    Relay IN4 -> Pin 11  (spare, not driven by this firmware)

  Library required: "DHT sensor library" by Adafruit, plus its
  dependency "Adafruit Unified Sensor" (Library Manager).
*/

#include <DHT.h>
#include "model_tree.h"   // dryingCompletePredict(...) lives here

#define DHTPIN 2
#define DHTTYPE DHT11

#define RED_LED_PIN   5
#define GREEN_LED_PIN 6

#define RELAY_FAN1_PIN 8
#define RELAY_PTC_PIN  9
#define RELAY_FAN2_PIN 10
// #define RELAY_SPARE_PIN 11   // spare relay, wired but unused for now

// Most cheap 4-channel relay modules are active-LOW: a LOW signal
// closes the relay. Flip these two if yours behaves the opposite way.
#define RELAY_ON_STATE  LOW
#define RELAY_OFF_STATE HIGH

// Safety cutoff: PTC heater relay forces OFF above this temperature
// regardless of what the model says, so a stuck reading can't cook
// whatever's drying. Adjust to whatever's safe for your material.
#define MAX_SAFE_TEMP_C 60.0

DHT dht(DHTPIN, DHTTYPE);

float previousTemperature = 0;
float previousHumidity = 0;
bool firstReading = true;

unsigned long startTime = 0;

void setFan(bool on) {
  digitalWrite(RELAY_FAN1_PIN, on ? RELAY_ON_STATE : RELAY_OFF_STATE);
  digitalWrite(RELAY_FAN2_PIN, on ? RELAY_ON_STATE : RELAY_OFF_STATE);
}

void setHeater(bool on) {
  digitalWrite(RELAY_PTC_PIN, on ? RELAY_ON_STATE : RELAY_OFF_STATE);
}

void setStatusLED(bool complete) {
  digitalWrite(RED_LED_PIN, complete ? LOW : HIGH);
  digitalWrite(GREEN_LED_PIN, complete ? HIGH : LOW);
}

void setup() {
  Serial.begin(9600);
  dht.begin();

  pinMode(RED_LED_PIN, OUTPUT);
  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(RELAY_FAN1_PIN, OUTPUT);
  pinMode(RELAY_PTC_PIN, OUTPUT);
  pinMode(RELAY_FAN2_PIN, OUTPUT);

  // Fail-safe startup state: everything off, red LED on, until the
  // first valid sensor reading comes in.
  setFan(false);
  setHeater(false);
  setStatusLED(false);

  startTime = millis();
}

void loop() {
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("Sensor read failed, skipping this cycle.");
    delay(1000);
    return;
  }

  if (firstReading) {
    previousTemperature = temperature;
    previousHumidity = humidity;
    firstReading = false;
  }

  float temperatureChange = temperature - previousTemperature;
  float humidityChange = humidity - previousHumidity;
  float elapsedTime = (millis() - startTime) / 1000.0;

  int dryingComplete = dryingCompletePredict(
    temperature,
    humidity,
    humidityChange,
    temperatureChange,
    elapsedTime
  );

  bool overTemp = temperature >= MAX_SAFE_TEMP_C;

  setFan(dryingComplete == 0);                      // fan runs while drying
  setHeater(dryingComplete == 0 && !overTemp);       // heater off once done OR too hot
  setStatusLED(dryingComplete == 1);                 // green = done, red = in progress

  Serial.print("Temperature: ");
  Serial.print(temperature, 2);
  Serial.println(" C");

  Serial.print("Humidity: ");
  Serial.print(humidity, 2);
  Serial.println(" %");

  Serial.print("dryingComplete: ");
  Serial.println(dryingComplete);

  Serial.print("Fan: ");
  Serial.println(dryingComplete == 0 ? "ON" : "OFF");

  Serial.print("Heater: ");
  Serial.println((dryingComplete == 0 && !overTemp) ? "ON" : "OFF");

  if (overTemp) {
    Serial.println("WARNING: over safe temperature, heater forced OFF");
  }

  Serial.println("---");

  previousTemperature = temperature;
  previousHumidity = humidity;

  delay(1000);
}