# Copyright 2014-present PlatformIO <contact@platformio.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
from platform import system
from os import makedirs
from os.path import isdir, join
import re
import time

from platformio.util import get_serial_ports

from SCons.Script import (ARGUMENTS, COMMAND_LINE_TARGETS, AlwaysBuild,
                          Builder, Default, DefaultEnvironment)


def BeforeUpload(target, source, env):  # pylint: disable=W0613,W0621
    upload_options = {}
    if "BOARD" in env:
        upload_options = env.BoardConfig().get("upload", {})

    env.AutodetectUploadPort()
    before_ports = get_serial_ports()

    if upload_options.get("use_1200bps_touch", False):
        env.TouchSerialPort("$UPLOAD_PORT", 1200)

    if upload_options.get("wait_for_upload_port", False):
        env.Replace(UPLOAD_PORT=env.WaitForNewSerialPort(before_ports))


def generate_uf2(target, source, env):
    elf_file = target[0].get_path()
    env.Execute(
        " ".join(
            [
                "elf2uf2",
                '"%s"' % elf_file,
                '"%s"' % elf_file.replace(".elf", ".uf2"),
            ]
        )
    )


env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()

env.Replace(
    AR="arm-none-eabi-ar",
    AS="arm-none-eabi-as",
    CC="arm-none-eabi-gcc",
    CXX="arm-none-eabi-g++",
    GDB="arm-none-eabi-gdb",
    OBJCOPY="arm-none-eabi-objcopy",
    RANLIB="arm-none-eabi-ranlib",
    SIZETOOL="arm-none-eabi-size",

    ARFLAGS=["rc"],

    MKFSTOOL="mklittlefs",
    PICO_FS_IMAGE_NAME=env.get("PICO_FS_IMAGE_NAME", "littlefs"),

    SIZEPROGREGEXP=r"^(?:\.text|\.data|\.rodata|\.text.align|\.ARM.exidx)\s+(\d+).*",
    SIZEDATAREGEXP=r"^(?:\.data|\.bss|\.noinit)\s+(\d+).*",
    SIZECHECKCMD="$SIZETOOL -A -d $SOURCES",
    SIZEPRINTCMD='$SIZETOOL -B -d $SOURCES',

    PROGSUFFIX=".elf"
)

# Allow user to override via pre:script
if env.get("PROGNAME", "program") == "program":
    env.Replace(PROGNAME="firmware")

env.Append(
    BUILDERS=dict(
        ElfToBin=Builder(
            action=env.VerboseAction(" ".join([
                "$OBJCOPY",
                "-O",
                "binary",
                "$SOURCES",
                "$TARGET"
            ]), "Building $TARGET"),
            suffix=".bin"
        ),
        ElfToHex=Builder(
            action=env.VerboseAction(" ".join([
                "$OBJCOPY",
                "-O",
                "ihex",
                "-R",
                ".eeprom",
                "$SOURCES",
                "$TARGET"
            ]), "Building $TARGET"),
            suffix=".hex"
        )
    )
)

if not env.get("PIOFRAMEWORK"):
    env.SConscript("frameworks/_bare.py")


def convert_size_expression_to_int(expression):
    conversion_factors = {
        "M": 1024*1024,
        "MB": 1024*1024,
        "K": 1024,
        "KB": 1024,
        "B": 1,
        "": 1 # giving no conversion factor is factor 1.
    }
    # match <floating pointer number><conversion factor>.
    extract_regex = r'^((?:[0-9]*[.])?[0-9]+)([mkbMKB]*)$'
    res = re.findall(extract_regex, expression)
    # unparsable expression? Warning.
    if len(res) == 0:
        sys.stderr.write(
            "Error: Could not parse filesystem size expression '%s'."
            " Will treat as size = 0.\n" % str(expression))
        return 0
    # access first result
    number, factor = res[0]
    number = float(number)
    number *= conversion_factors[factor.upper()]
    return int(number)

def fetch_fs_size(env):
    # follow generation formulas from makeboards.py for Earle Philhower core
    # given the total flash size, a user can specify
    # the amount for the filesystem (0MB, 2MB, 4MB, 8MB, 16MB)
    # via board_build.filesystem_size,
    # and we will calculate the flash size and eeprom size from that.
    flash_size = board.get("upload.maximum_size")
    filesystem_size = board.get("build.filesystem_size", "0MB")
    filesystem_size_int = convert_size_expression_to_int(filesystem_size)

    maximum_size = flash_size - 4096 - filesystem_size_int

    print("Flash size: %.2fMB" % (flash_size / 1024.0 / 1024.0))
    print("Sketch size: %.2fMB" % (maximum_size / 1024.0 / 1024.0))
    print("Filesystem size: %.2fMB" % (filesystem_size_int / 1024.0 / 1024.0))

    flash_length = maximum_size
    eeprom_start = 0x10000000 + flash_size - 4096
    fs_start = 0x10000000 + flash_size - 4096 - filesystem_size_int
    fs_end = 0x10000000 + flash_size - 4096

    if maximum_size <= 0:
        sys.stderr.write(
            "Error: Filesystem too large for given flash. "
            "Can at max be flash size - 4096 bytes. "
            "Available sketch size with current "
            "config would be %d bytes.\n" % maximum_size)
        sys.stderr.flush()
        env.Exit(-1)

    env["PICO_FLASH_LENGTH"] = flash_length
    env["PICO_EEPROM_START"] = eeprom_start
    env["FS_START"] = fs_start
    env["FS_END"] = fs_end
    # LittleFS configuration paramters taken from
    # https://github.com/earlephilhower/arduino-pico-littlefs-plugin/blob/master/src/PicoLittleFS.java
    env["FS_PAGE"] = 256
    env["FS_BLOCK"] = 4096

    print("Maximium size: %d Flash Length: %d "
        "EEPROM Start: %d Filesystem start %d "
        "Filesystem end %s" % 
        (maximum_size,flash_length, eeprom_start, fs_start, fs_end))


def __fetch_fs_size(target, source, env):
    fetch_fs_size(env)
    return (target, source)

env.Append(
    BUILDERS=dict(
        DataToBin=Builder(
            action=env.VerboseAction(" ".join([
                '"$MKFSTOOL"',
                "-c", "$SOURCES",
                "-p", "$FS_PAGE",
                "-b", "$FS_BLOCK",
                "-s", "${FS_END - FS_START}",
                "$TARGET"
            ]), "Building file system image from '$SOURCES' directory to $TARGET"),
            emitter=__fetch_fs_size,
            source_factory=env.Dir,
            suffix=".bin"
        )
    )
)

# store function to get infno about filesystems for builder scripts.
env["fetch_fs_size"] = fetch_fs_size

#
# Target: Build executable and linkable firmware
#

target_elf = None
if "nobuild" in COMMAND_LINE_TARGETS:
    target_elf = join("$BUILD_DIR", "${PROGNAME}.elf")
    target_firm = join("$BUILD_DIR", "${PROGNAME}.bin")
else:
    target_elf = env.BuildProgram()
    if set(["buildfs", "uploadfs"]) & set(COMMAND_LINE_TARGETS):
        target_firm = env.DataToBin(
            join("$BUILD_DIR", "${PICO_FS_IMAGE_NAME}"), "$PROJECTDATA_DIR")
        AlwaysBuild(target_firm)
    else:
        target_firm = env.ElfToBin(join("$BUILD_DIR", "${PROGNAME}"), target_elf)
        env.Depends(target_firm, "checkprogsize")

env.AddPlatformTarget("buildfs", target_firm, target_firm, "Build Filesystem Image")
AlwaysBuild(env.Alias("nobuild", target_firm))
target_buildprog = env.Alias("buildprog", target_firm, target_firm)

env.AddPostAction(
    target_elf, env.VerboseAction(generate_uf2, "Generating UF2 image")
)

def _update_max_upload_size(env):
    fetch_fs_size(env)
    env.BoardConfig().update("upload.maximum_size", env["PICO_FLASH_LENGTH"])

# update max upload size based on CSV file
if env.get("PIOMAINPROG"):
    env.AddPreAction(
        "checkprogsize",
        env.VerboseAction(
            lambda source, target, env: _update_max_upload_size(env),
            "Retrieving maximum program size $SOURCE"))
# remove after PIO Core 3.6 release
elif set(["checkprogsize", "upload"]) & set(COMMAND_LINE_TARGETS):
    _update_max_upload_size(env)

#
# Target: Print binary size
#

target_size = env.Alias(
    "size", target_elf,
    env.VerboseAction("$SIZEPRINTCMD", "Calculating size $SOURCE"))
AlwaysBuild(target_size)

def DelayBeforeUpload(target, source, env):  # pylint: disable=W0613,W0621
    time.sleep(0.5)

def RebootPico(target, source, env): 
    time.sleep(0.5)
    env.Execute(
        '"%s" reboot' %
            join(platform.get_package_dir("tool-rp2040tools") or "", "picotool")
    )
#
# Target: Upload by default .bin file
#

debug_tools = env.BoardConfig().get("debug.tools", {})
upload_protocol = env.subst("$UPLOAD_PROTOCOL") or "picotool"
upload_actions = []
upload_source = target_firm

if upload_protocol == "mbed":
    upload_actions = [
        env.VerboseAction(env.AutodetectUploadPort, "Looking for upload disk..."),
        env.VerboseAction(env.UploadToDisk, "Uploading $SOURCE")
    ]
elif upload_protocol == "picotool":
    env.Replace(
        UPLOADER='"%s"' % join(platform.get_package_dir("tool-rp2040tools") or "", "rp2040load"),
        UPLOADERFLAGS=["-v", "-D"],
        UPLOADCMD="$UPLOADER $UPLOADERFLAGS $SOURCES"
    )

    if "uploadfs" in COMMAND_LINE_TARGETS:
        env.Replace(
            UPLOADER=join(platform.get_package_dir("tool-rp2040tools") or "", "picotool"),
            UPLOADERFLAGS=[
                "load",
                "--verify"
            ],
            UPLOADCMD="$UPLOADER $UPLOADERFLAGS $SOURCES --offset ${hex(FS_START)}",
        )

    upload_actions = [
        env.VerboseAction(BeforeUpload, "Looking for upload port..."),
        env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE"),
    ]

    # picotool seems to need just a tiny bit of delay, but rp2040 load not..
    if "uploadfs" in COMMAND_LINE_TARGETS:
        upload_actions.insert(1, env.VerboseAction(DelayBeforeUpload, "Delaying a tiny bit..."))
        # reboot after filesystem upload
        upload_actions.append(env.VerboseAction(RebootPico, "Rebooting device..."))

    upload_source = target_elf

elif upload_protocol.startswith("jlink"):

    def _jlink_cmd_script(env, source):
        build_dir = env.subst("$BUILD_DIR")
        if not isdir(build_dir):
            makedirs(build_dir)
        script_path = join(build_dir, "upload.jlink")
        commands = [
            "h",
            "loadbin %s, %s" % (source, board.get(
                "upload.offset_address", "0x0")),
            "r",
            "q"
        ]
        with open(script_path, "w") as fp:
            fp.write("\n".join(commands))
        return script_path

    env.Replace(
        __jlink_cmd_script=_jlink_cmd_script,
        UPLOADER="JLink.exe" if system() == "Windows" else "JLinkExe",
        UPLOADERFLAGS=[
            "-device", board.get("debug", {}).get("jlink_device"),
            "-speed", env.GetProjectOption("debug_speed", "4000"),
            "-if", ("jtag" if upload_protocol == "jlink-jtag" else "swd"),
            "-autoconnect", "1",
            "-NoGui", "1"
        ],
        UPLOADCMD='$UPLOADER $UPLOADERFLAGS -CommanderScript "${__jlink_cmd_script(__env__, SOURCE)}"'
    )
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]
    upload_source = env.ElfToHex(join("$BUILD_DIR", "${PROGNAME}"), target_elf)

elif upload_protocol in debug_tools:
    openocd_args = [
        "-d%d" % (2 if int(ARGUMENTS.get("PIOVERBOSE", 0)) else 1)
    ]
    openocd_args.extend(
        debug_tools.get(upload_protocol).get("server").get("arguments", []))
    if env.GetProjectOption("debug_speed"):
        openocd_args.extend(
            ["-c", "adapter speed %s" % env.GetProjectOption("debug_speed")]
        )
    if "uploadfs" in COMMAND_LINE_TARGETS:
        # filesystem upload. use FS_START.
        openocd_args.extend([
            "-c", "program {$SOURCE} ${hex(FS_START)} verify reset; shutdown;"
        ])
    else:
        # normal firmware upload. flash starts at 0x10000000
        openocd_args.extend([
            "-c", "program {$SOURCE} %s verify reset; shutdown;" %
            board.get("upload.offset_address", "0x10000000")
        ])
    openocd_args = [
        f.replace("$PACKAGE_DIR", platform.get_package_dir(
            "tool-openocd-raspberrypi") or "")
        for f in openocd_args
    ]
    # use ELF file for upload, not bin (target_firm). otherwise needs
    # offset 0x10000000
    #upload_source = target_elf
    env.Replace(
        UPLOADER="openocd",
        UPLOADERFLAGS=openocd_args,
        UPLOADCMD="$UPLOADER $UPLOADERFLAGS")
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]

# custom upload tool
elif upload_protocol == "custom":
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]

if not upload_actions:
    sys.stderr.write("Warning! Unknown upload protocol %s\n" % upload_protocol)

AlwaysBuild(env.Alias("upload", upload_source, upload_actions))
env.AddPlatformTarget("uploadfs", target_firm, upload_actions, "Upload Filesystem Image")
#
# Default targets
#

Default([target_buildprog, target_size])
