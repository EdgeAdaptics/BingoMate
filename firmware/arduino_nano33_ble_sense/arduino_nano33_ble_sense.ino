#include <Arduino_HTS221.h>
#include <Arduino_LSM9DS1.h>
#include <PDM.h>

volatile int samplesRead = 0;
short sampleBuffer[256];
float soundLevel = 0.0;
unsigned long lastSampleMs = 0;

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 4000) {
  }

  if (!IMU.begin()) {
    Serial.println("{\"error\":\"imu_init_failed\"}");
  }

  if (!HTS.begin()) {
    Serial.println("{\"error\":\"hts221_init_failed\"}");
  }

  PDM.onReceive(onPDMdata);
  if (!PDM.begin(1, 16000)) {
    Serial.println("{\"error\":\"pdm_init_failed\"}");
  }
}

void loop() {
  if (millis() - lastSampleMs < 1000) {
    return;
  }
  lastSampleMs = millis();

  float ax = 0.0;
  float ay = 0.0;
  float az = 0.0;
  if (IMU.accelerationAvailable()) {
    IMU.readAcceleration(ax, ay, az);
  }

  float temperatureC = HTS.readTemperature();
  float humidityPct = HTS.readHumidity();

  Serial.print("{\"temperature_c\":");
  Serial.print(temperatureC, 2);
  Serial.print(",\"humidity_pct\":");
  Serial.print(humidityPct, 2);
  Serial.print(",\"ax\":");
  Serial.print(ax, 3);
  Serial.print(",\"ay\":");
  Serial.print(ay, 3);
  Serial.print(",\"az\":");
  Serial.print(az, 3);
  Serial.print(",\"sound_level\":");
  Serial.print(soundLevel, 3);
  Serial.println("}");
}

void onPDMdata() {
  int bytesAvailable = PDM.available();
  PDM.read(sampleBuffer, bytesAvailable);
  int sampleCount = bytesAvailable / 2;
  long sum = 0;
  for (int i = 0; i < sampleCount; i++) {
    sum += abs(sampleBuffer[i]);
  }
  if (sampleCount > 0) {
    float average = (float)sum / sampleCount;
    soundLevel = min(1.0, average / 32768.0);
  }
}
