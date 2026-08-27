![Logo](https://www.woehler.de/shop/static/version1724252505/frontend/Woehler/de/de_DE/images/logo.svg)

# QR-Code Scanner

## Overview

This tool enables the interpretation of Wöhler QR codes through a web-based user interface. The application uses NiceGUI and can be run both locally and in containers.

## Functionality

- **QR-Code Scanner**: Interactive web interface for reading QR codes
- **Data Interpretation**: Automatic analysis and structuring of QR code contents
- **Field Definitions**: Uses `field_names_en.json` or `field_names_de.json` for correct interpretation


## Project Structure

```
<root>/
├── field_name/                 # Submodule containing field definitions (English and German)
├── main.py                     # Main application
├── Containerfile               # Podman container configuration
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Python development dependencies
├── start-container.ps1         # PowerShell script for NiceGUI container
├── README.md                   # Project documentation
├── LICENSE                     # License file
└── ruff.toml                   # Ruff configuration file
```

## Installation and Usage

First init submodules to get the field definitions. Make sure that the directory for the submodule is named `field_name` to match the code. Otherwise, you will need to adjust the code in the `Containerfile` or the environment variable accordingly.
But by default, the submodule has the correct directory name `field_name`.

```powershell
git submodule update --init --recursive
```

### Option 1: Local Python Environment
This instruction assumes you are using Windows PowerShell. If you are using a different shell, please adjust the commands accordingly.
Make sure you have Python `3.10` or higher installed.

```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows PowerShell

# Install dependencies
pip install -r requirements.txt

# (Optional) Install development dependencies
pip install -r requirements-dev.txt

# Set environment variable for field definitions
$env:FIELD_NAMES_FILE = "field_name/field_names_en.json"  # Or "field_name/field_names_de.json" for German

# Start application
python main.py
```

### Option 2: NiceGUI Container
Make sure you have Podman installed. The container will automatically use the field definition from the submodule `field_name/field_names_en.json`. If you want to use another field definition, you can adjust the `Containerfile`.

```powershell
# Build and start custom image
.\start-container.ps1
```

The application is then accessible at http://localhost:8080.
