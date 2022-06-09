# Raspberry Pi RP2040: development platform for [PlatformIO](https://platformio.org)

[![Build Status](https://github.com/platformio/platform-raspberrypi/workflows/Examples/badge.svg)](https://github.com/platformio/platform-raspberrypi/actions)

RP2040 is a low-cost, high-performance microcontroller device with a large on-chip memory, symmetric dual-core processor complex, deterministic bus fabric, and rich peripheral set augmented with a unique Programmable I/O (PIO) subsystem, it provides professional users with unrivalled power and flexibility.

* [Home](https://registry.platformio.org/platforms/platformio/raspberrypi) (home page in the PlatformIO Registry)
* [Documentation](https://docs.platformio.org/page/platforms/raspberrypi.html) (advanced usage, packages, boards, frameworks, etc.)

# Usage

1. [Install PlatformIO](https://platformio.org)
2. Create PlatformIO project and configure a platform option in [platformio.ini](https://docs.platformio.org/page/projectconf.html) file:

## Stable version

```ini
[env:stable]
platform = raspberrypi
board = ...
...
```

## Development version

```ini
[env:development]
platform = https://github.com/platformio/platform-raspberrypi.git
board = ...
...
```

# Configuration

Please navigate to [documentation](https://docs.platformio.org/page/platforms/raspberrypi.html).
