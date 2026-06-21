#include <Adafruit_GFX.h>
#include <Adafruit_LEDBackpack.h>
#include <Wire.h>

Adafruit_8x8matrix matrices[4] = {
  Adafruit_8x8matrix(),
  Adafruit_8x8matrix(),
  Adafruit_8x8matrix(),
  Adafruit_8x8matrix()
};

const uint8_t ADDRESSES[4] = {0x70, 0x71, 0x72, 0x73};
String currentStatus = "BOOT";
int currentRisk = 0;
unsigned long lastFrameMs = 0;
int scrollX = 32;

void setup() {
  Serial.begin(115200);
  Wire.begin();

  for (int i = 0; i < 4; i++) {
    matrices[i].begin(ADDRESSES[i]);
    matrices[i].setBrightness(6);
    matrices[i].setRotation(0);
    matrices[i].clear();
    matrices[i].writeDisplay();
  }

  drawStatus("BOOT", 0);
}

void loop() {
  readSerialCommand();
  if (millis() - lastFrameMs > 90) {
    drawStatus(currentStatus, currentRisk);
    lastFrameMs = millis();
  }
}

void readSerialCommand() {
  if (!Serial.available()) {
    return;
  }

  String line = Serial.readStringUntil('\n');
  line.trim();
  if (!line.startsWith("STATUS:")) {
    return;
  }

  int secondColon = line.indexOf(':', 7);
  if (secondColon < 0) {
    currentStatus = line.substring(7);
    currentRisk = 0;
  } else {
    currentStatus = line.substring(7, secondColon);
    currentRisk = line.substring(secondColon + 1).toInt();
  }
  currentStatus.toUpperCase();
  scrollX = 32;
}

void drawStatus(String status, int risk) {
  clearAll();
  String label = status;
  if (status == "ALERT") {
    label = "ALRT";
  }
  if (label.length() > 4) {
    drawScrolling(label + " " + String(risk));
  } else {
    drawFourChars(label);
  }
  drawRiskBar(risk);
  flushAll();
}

void drawFourChars(String text) {
  while (text.length() < 4) {
    text += " ";
  }
  for (int i = 0; i < 4; i++) {
    matrices[i].setTextSize(1);
    matrices[i].setTextWrap(false);
    matrices[i].setTextColor(LED_ON);
    matrices[i].setCursor(1, 0);
    matrices[i].print(text.substring(i, i + 1));
  }
}

void drawScrolling(String text) {
  clearAll();
  for (int i = 0; i < 4; i++) {
    matrices[i].setTextSize(1);
    matrices[i].setTextWrap(false);
    matrices[i].setTextColor(LED_ON);
    matrices[i].setCursor(scrollX - (i * 8), 0);
    matrices[i].print(text);
  }
  scrollX--;
  if (scrollX < -(int)(text.length() * 6)) {
    scrollX = 32;
  }
}

void drawRiskBar(int risk) {
  int width = map(constrain(risk, 0, 100), 0, 100, 0, 32);
  for (int x = 0; x < width; x++) {
    int block = x / 8;
    int localX = x % 8;
    matrices[block].drawPixel(localX, 7, LED_ON);
  }
}

void clearAll() {
  for (int i = 0; i < 4; i++) {
    matrices[i].clear();
  }
}

void flushAll() {
  for (int i = 0; i < 4; i++) {
    matrices[i].writeDisplay();
  }
}
