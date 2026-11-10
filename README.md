# Data acquisition with NI-DAQmx and Python

Course materials for controlling National Instruments DAQ hardware from Python with the
[`nidaqmx`](https://github.com/ni/nidaqmx-python) package, aimed at neuroscientists.

## Course structure

| Stage | What | Where |
|---|---|---|
| 1. Warm-up | Exercises 01–04: analog input, analog output, synchronisation, continuous acquisition | [`exercises/`](exercises/) |
| 2. Check the rig | Confirm the photodiode is wired and sees the blades | [`rig_checks/`](rig_checks/) |
| 3. Experiment | Exercises 05–07: measure fan blade width with a laser and photodiode | [`exercises/`](exercises/) |
| Reference | Worked walkthroughs of the API and the experiment | [`notebooks/`](notebooks/) |

## Timetable (~2½ hours)

| Time | Block |
|---|---|
| 0:00 | Setup check: device name, loopback wiring (AO0 → AI0) |
| 0:15 | Warm-up: exercises 01–04 |
| 1:00 | Break |
| 1:10 | Rewire (photodiode on AI0), run `rig_checks/check_photodiode.py`, align the beam (exercise 05) |
| 1:30 | Record and analyse (exercises 06–07) |
| 2:15 | Discussion |
| 2:30 | End |

## Setup

```bash
pip install uv
uv sync
```

Set `DEV` at the top of each script to your device name from NI MAX (e.g. `Dev1`), then run
scripts from the repository root:

```bash
uv run python exercises/01_analog_input.py
uv run jupyter lab notebooks/
```

No hardware? Create a simulated device in NI MAX (*Devices and Interfaces → Create New →
Simulated NI-DAQmx Device*). Its inputs return a synthetic signal rather than echoing outputs.

## Wiring

| Used in | Connection |
|---|---|
| Tutorial and exercises (loopback) | AO0 → AI0, AO GND → AI GND. Exercise 01 Part C also reads AI1. |
| Fan experiment | Photodiode on AI0 (RSE) only. The fan runs from its own power supply at a fixed speed and is **not** connected to the DAQ. |

## Safety

- **Laser:** never look into the beam; watch for reflections off the blades.
- **Fan:** keep fingers clear. It has its own supply, so it keeps spinning when your script stops.
- **Outputs:** scripts return every analog output to 0 V when they finish. Don't remove that step.

## Common errors

| Code | Meaning | What to do |
|---|---|---|
| -50103 | Resource is reserved | Another task (often a crashed script or notebook cell) holds the channels. Close it or restart Python. |
| -200279 | Samples no longer available | A continuous read fell behind. Read larger chunks or enlarge the buffer. |
| -200284 | Requested samples not acquired | A read timed out. Check the trigger fires, e.g. that the AO task was started. |

## Further reading

- [SWC Python_DAQmx_examples](https://github.com/SWC-Advanced-Microscopy/Python_DAQmx_examples)
- [nidaqmx-python docs](https://nidaqmx-python.readthedocs.io/) and [examples](https://github.com/ni/nidaqmx-python/tree/master/examples)
