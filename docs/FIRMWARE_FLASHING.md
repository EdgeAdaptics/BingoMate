# Firmware Flashing

This project keeps firmware flashing reproducible with `arduino-cli`.

## Installed Tool Check

```powershell
arduino-cli version
python scripts\firmware.py list
```

## Arduino Nano 33 BLE Sense

Install core and libraries:

```powershell
python scripts\firmware.py install --sketch arduino_nano33_ble_sense
```

Compile:

```powershell
python scripts\firmware.py compile --sketch arduino_nano33_ble_sense
```

Upload after finding the serial port:

```powershell
python scripts\inventory_serial.py --probe
python scripts\firmware.py upload --sketch arduino_nano33_ble_sense --port COMx
```

On Jetson, the Nano usually appears as `/dev/ttyACM0`.

## ESP32 Matrix Status Display

Install ESP32 core and display libraries:

```powershell
python scripts\firmware.py install --sketch esp32_matrix_status
```

Compile:

```powershell
python scripts\firmware.py compile --sketch esp32_matrix_status
```

Upload:

```powershell
python scripts\inventory_serial.py --probe
python scripts\firmware.py upload --sketch esp32_matrix_status --port COMx
```

On Jetson, the ESP32 usually appears as `/dev/ttyUSB0`.

## Command Preview

Print compile and upload commands without running them:

```powershell
python scripts\firmware.py command --sketch esp32_matrix_status --port COM4
```

## Arduino IDE Fallback

If CLI upload fails, open the sketch folder in Arduino IDE:

- `firmware/arduino_nano33_ble_sense`
- `firmware/esp32_matrix_status`

Then select the matching board, install the listed libraries, choose the detected serial port, and upload.
