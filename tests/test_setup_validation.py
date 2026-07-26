import pytest
import sys
import importlib.util
from pathlib import Path


def test_python_imports():
    """Test that Python can import basic modules."""
    import json
    import os
    import platform
    assert True


def test_pytest_installed():
    """Test that pytest is properly installed."""
    import pytest
    assert hasattr(pytest, "main")


def test_coverage_installed():
    """Test that coverage tools are installed."""
    try:
        import coverage
        assert True
    except ImportError:
        pytest.fail("Coverage module not installed")


def test_mock_installed():
    """Test that pytest-mock is installed."""
    import pytest_mock
    assert hasattr(pytest_mock, "MockerFixture")


def test_project_structure():
    """Test that the project has the expected structure."""
    project_root = Path(__file__).parent.parent
    
    assert (project_root / "platform.py").exists()
    assert (project_root / "platform.json").exists()
    assert (project_root / "pyproject.toml").exists()
    assert (project_root / "tests").is_dir()
    assert (project_root / "tests" / "__init__.py").exists()
    assert (project_root / "tests" / "conftest.py").exists()


def test_platform_module_importable():
    """Test that the platform module can be imported."""
    project_root = Path(__file__).parent.parent
    platform_path = project_root / "platform.py"
    
    spec = importlib.util.spec_from_file_location("platform", platform_path)
    module = importlib.util.module_from_spec(spec)
    
    try:
        spec.loader.exec_module(module)
        assert hasattr(module, "RaspberrypiPlatform")
    except ImportError as e:
        pytest.skip(f"Platform module requires PlatformIO dependencies: {e}")


def test_fixtures_available(temp_dir, mock_platform_variables):
    """Test that shared fixtures are working."""
    assert temp_dir.exists()
    assert temp_dir.is_dir()
    assert isinstance(mock_platform_variables, dict)
    assert "board" in mock_platform_variables


@pytest.mark.unit
def test_unit_marker():
    """Test that unit test marker works."""
    assert True


@pytest.mark.integration  
def test_integration_marker():
    """Test that integration test marker works."""
    assert True


@pytest.mark.slow
def test_slow_marker():
    """Test that slow test marker works."""
    assert True