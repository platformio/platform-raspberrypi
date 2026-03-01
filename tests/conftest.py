import os
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_platform_variables():
    """Mock platform variables for testing."""
    return {
        "board": "pico",
        "upload_protocol": "picotool",
        "debug_tool": "cmsis-dap"
    }


@pytest.fixture
def mock_board_config():
    """Mock board configuration."""
    config = Mock()
    config.get.return_value = {
        "debug.default_tools": ["cmsis-dap"],
        "upload.protocol": "picotool"
    }
    return config


@pytest.fixture
def sample_board_manifest():
    """Sample board manifest data for testing."""
    return {
        "debug": {
            "jlink_device": "RP2040_M0_0",
            "openocd_target": "rp2040.cfg",
            "onboard_tools": ["cmsis-dap"]
        },
        "upload": {
            "protocols": ["cmsis-dap", "jlink", "raspberrypi-swd"]
        }
    }


@pytest.fixture
def mock_debug_config():
    """Mock debug configuration."""
    config = Mock()
    config.speed = "5000"
    config.server = {
        "arguments": ["-f", "interface/cmsis-dap.cfg"],
        "executable": "openocd"
    }
    return config


@pytest.fixture
def platform_json_content():
    """Sample platform.json content for testing."""
    return {
        "name": "raspberrypi",
        "title": "Raspberry Pi RP2040",
        "version": "1.17.0",
        "frameworks": {
            "arduino": {
                "package": "framework-arduino-mbed"
            }
        },
        "packages": {
            "toolchain-gccarmnoneeabi": {
                "type": "toolchain",
                "version": "~1.90201.0"
            },
            "tool-jlink": {
                "type": "uploader",
                "optional": True
            }
        }
    }


@pytest.fixture
def mock_platformio_board():
    """Mock PlatformIO board object."""
    board = Mock()
    board.id = "pico"
    board.manifest = {
        "debug": {
            "jlink_device": "RP2040_M0_0",
            "openocd_target": "rp2040.cfg"
        },
        "upload": {
            "protocols": ["cmsis-dap", "jlink"]
        }
    }
    return board


@pytest.fixture(autouse=True)
def clean_environment():
    """Clean environment variables before each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_file_system(temp_dir):
    """Create a mock file system structure for testing."""
    structure = {
        "platform.json": '{"name": "raspberrypi", "version": "1.17.0"}',
        "platform.py": "# Platform implementation",
        "boards": {
            "pico.json": '{"name": "Raspberry Pi Pico"}',
            "nanorp2040connect.json": '{"name": "Arduino Nano RP2040 Connect"}'
        },
        "builder": {
            "main.py": "# Builder main",
            "frameworks": {
                "arduino": {
                    "mbed-core": {
                        "arduino-core-mbed.py": "# Arduino core"
                    }
                }
            }
        }
    }
    
    def create_structure(base_path, structure_dict):
        for name, content in structure_dict.items():
            path = base_path / name
            if isinstance(content, dict):
                path.mkdir(parents=True, exist_ok=True)
                create_structure(path, content)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
    
    create_structure(temp_dir, structure)
    return temp_dir