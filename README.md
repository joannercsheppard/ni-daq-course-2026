# Data acquisition with NI-DAQmx and Python

Course materials for controlling National Instruments DAQ hardware from Python
with the [`nidaqmx`](https://github.com/ni/nidaqmx-python) package. The course is
aimed at neuroscientists: every step is linked to how the same idea is used on
real rigs (two-photon microscopes, electrophysiology and optogenetics).

## Course structure

The course assumes you already know the basics of NI-DAQmx in Python. The exercises are a
short warm-up refresher (exercises 01–04); the main activity is the fan blade experiment
(exercises 05–07).

| Stage | What | Where |
|---|---|---|
| 1. Warm-up | Exercises 01–04: a refresher of analog input, analog output, synchronisation and continuous acquisition | [`exercises/`](exercises/) |
| 2. Check the rig | A quick check that the photodiode is wired and sees the blades | [`rig_checks/`](rig_checks/) |
| 3. Experiment | Exercises 05–07: measure the width of a fan blade with a laser and a photodiode (align, record, analyse) | [`exercises/`](exercises/) |
| Reference | Worked walkthroughs of the API and of the experiment | [`notebooks/`](notebooks/) |

## Timetable

About 2½ hours including a break. These are estimates; adjust them after a trial run.

| Time | Block |
|---|---|
| 0:00 | Setup check: driver, device name, loopback wiring (AO0 → AI0) |
| 0:15 | Warm-up: exercises 01–04 |
| 1:00 | Break |
| 1:10 | Rewire for the experiment (remove the loopback, photodiode on AI0), `rig_checks/check_photodiode.py`, align the beam (exercise 05) |
| 1:30 | Experiment: measure the rig, record and analyse (exercises 06–07) |
| 2:15 | Discussion of the investigation questions |
| 2:30 | End |

**For a 2-hour version**, skip the warm-up investigation questions and do warm-up 03 as an
instructor demo.

## Repository layout

```
ni-daq-course-2026/
├── README.md
├── pyproject.toml                   # dependencies, for uv
├── uv.lock                          # exact package versions (commit this)
├── requirements.txt                 # the same dependencies, for plain pip
├── notebooks/
│   ├── nidaqmx_tutorial.ipynb       # reference: the API step by step
│   └── fan_blade_width.ipynb        # reference: the experiment, worked through
├── exercises/                       # student scripts with TODOs
│   ├── README.md
│   ├── 01_analog_input.py
│   ├── 02_analog_output.py
│   ├── 03_synchronised_ao_ai.py
│   ├── 04_continuous_acquisition.py
│   ├── 05_fan_live_view.py          # fan experiment: align the beam
│   ├── 06_fan_record.py             # fan experiment: record to data/
│   └── 07_fan_analyse.py            # fan experiment: blade width
├── rig_checks/                      # hardware sanity checks for the experiment
│   ├── check_fan.py
│   └── check_photodiode.py
└── data/                            # recordings are saved here (not tracked by git)
```

## Setup

The Python environment is managed with [uv](https://docs.astral.sh/uv/). It installs the
right Python version and the exact package versions in `uv.lock`, so every computer in the
class has the same setup.

1. **Install uv** (once per computer):
   ```bash
   # Windows (PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   # Linux / macOS
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   Then open a new terminal so the `uv` command is found.
2. **Create the environment.** From the repository's root folder:
   ```bash
   uv sync
   ```
   This creates a `.venv` folder with Python 3.12 and all the packages. Run it again
   whenever `pyproject.toml` or `uv.lock` change.
3. **Install the NI-DAQmx driver** (Windows or Linux; there is no macOS driver). The
   `nidaqmx` Python package is only a wrapper around it. Either download it from NI, or run
   ```bash
   uv run python -m nidaqmx installdriver
   ```
4. **Find your device name** in NI MAX (for example `Dev1`), and set `DEV` at the top of
   each script or notebook to match.

Run every script from the repository's root folder with `uv run`, which uses the
environment without having to activate it:

```bash
uv run python exercises/01_analog_input.py
uv run jupyter lab notebooks/          # the reference notebooks
```

In VS Code, choose the interpreter in `.venv` (*Python: Select Interpreter*) to run
scripts with the Run button instead.

<details>
<summary>Without uv (plain pip)</summary>

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python exercises/01_analog_input.py
```
</details>

No hardware? Create a **simulated device** in NI MAX
(*Devices and Interfaces → Create New → Simulated NI-DAQmx Device*, for example a
PCIe-6321). It runs everything in the tutorial and exercises, but its inputs return
a synthetic signal instead of echoing your outputs.

## Wiring

| Used in | Connection |
|---|---|
| Tutorial and exercises (loopback) | AO0 → AI0, AO GND → AI GND. Exercise 01 Part C also reads AI1. |
| Fan experiment | Photodiode on AI0 (RSE) only. The fan runs from its own power supply at a fixed speed and is **not** connected to the DAQ. |

## Safety

- **Laser:** never look into the beam, and watch out for reflections off the fan blades.
  Use a class 2 (or lower) module and keep the beam below eye level.
- **Fan:** keep fingers clear while it spins. It has its own power supply, so it keeps
  spinning when your script stops.
- **Outputs:** the scripts return every analog output to 0 V when they finish. Don't
  remove that step.

## Common errors

| Code | Meaning | What to do |
|---|---|---|
| -50103 | The resource is reserved | Another task (often from a crashed script or notebook cell) still holds the channels. Close it, or restart Python. |
| -200279 | Samples are no longer available | A continuous read fell behind. Read larger chunks or make the buffer bigger. |
| -200284 | The requested samples haven't been acquired | A read timed out. Check that the trigger fires, e.g. that the AO task was started. |

## Further reading

- [SWC Python_DAQmx_examples](https://github.com/SWC-Advanced-Microscopy/Python_DAQmx_examples):
  the examples this course follows, including live plotting with pyqtgraph
- [nidaqmx-python documentation](https://nidaqmx-python.readthedocs.io/) and its
  [examples](https://github.com/ni/nidaqmx-python/tree/master/examples)
