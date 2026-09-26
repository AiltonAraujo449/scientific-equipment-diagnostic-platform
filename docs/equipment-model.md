# SEDP Equipment Model

## Equipment

ID: SEDP-SEM-001

Type: Scanning Electron Microscope

## Subsystems

### Vacuum System

Components:
- Vacuum Pump
- Vacuum Sensor
- Valve

### Cooling System

Components:
- Cooling Pump
- Flow Sensor
- Temperature Sensor

### Motion System

Components:
- Stage Controller
- X Axis
- Y Axis
- Z Axis

### Power System

Components:
- Power Supply
- Power Controller

### Detector System

Components:
- Detector
- Detector Controller

### Control Software

Components:
- Main Controller
- Communication
- Acquisition

## Event Model

Each equipment event contains:

- timestamp
- equipment_id
- subsystem
- component
- event_code
- severity
- value
- unit

## Severity Levels

- INFO
- WARNING
- ERROR
- CRITICAL