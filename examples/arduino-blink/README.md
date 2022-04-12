How to build PlatformIO based project
=====================================

<<<<<<< HEAD
1. [Install PlatformIO Core](http://docs.platformio.org/page/core.html)
=======
1. [Install PlatformIO Core](https://docs.platformio.org/page/core.html)
>>>>>>> e08da697f0a750d5ebdd17d299d262b729e67c42
2. Download [development platform with examples](https://github.com/platformio/platform-raspberrypi/archive/develop.zip)
3. Extract ZIP archive
4. Run these commands:

```shell
# Change directory to example
$ cd platform-raspberrypi/examples/arduino-blink

# Build project
$ pio run

# Upload firmware
$ pio run --target upload

# Clean build files
$ pio run --target clean
```
