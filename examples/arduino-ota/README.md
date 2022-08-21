How to build PlatformIO based project
=====================================

1. [Install PlatformIO Core](https://docs.platformio.org/page/core.html)
2. Download [development platform with examples](https://github.com/platformio/platform-raspberrypi/archive/develop.zip)
3. Extract ZIP archive
4. Run these commands:

```shell
# Change directory to example
$ cd platform-raspberrypi/examples/arduino-ota

# Build project
$ pio run

# Upload firmware
$ pio run --target upload

# Clean build files
$ pio run --target clean
```

## Notes

This examples showcases the usage of Over-The-Air (OTA) updates with the Raspberry Pi Pico W.

For more details, see the [documentation](https://arduino-pico.readthedocs.io/en/latest/ota.html).

For the initial firmware update, use the `rpipicow_via_usb` environment.

Then, open the serial monitor and note down the IP of the Pico that it outputs.

Use this IP as the `upload_port` in the `rpipicow_via_ota` environment and use the "Upload" project task there.