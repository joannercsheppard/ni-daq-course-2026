# Exercises

Seven exercises in two parts:

- **Part 1, warm-up (01–04):** a refresher of things you should already know. If a step
  is unfamiliar, look it up in `notebooks/nidaqmx_tutorial.ipynb` before the class.
- **Part 2, fan blade experiment (05–07):** use those skills on a real measurement.

Each script is a standalone program, written the way you'd write a script for a real
experiment. The setup, settings, plotting and safety code are already there. You fill
in the TODOs.

## Part 1: Warm-up

Wiring: loopback, **AO0 → AI0** and AO GND → AI GND.

| Script | Refreshes | Time |
|---|---|---|
| `01_analog_input.py` | on-demand and hardware-timed AI | ~10 min |
| `02_analog_output.py` | on-demand AO, a timed waveform, returning outputs to 0 V | ~10 min |
| `03_synchronised_ao_ai.py` | starting AO and AI together with a start trigger (needs real hardware) | ~15 min |
| `04_continuous_acquisition.py` | continuous AI read in chunks, as used again in exercise 05 | ~10 min |

## Part 2: Fan blade experiment

A laser beam passes through a spinning fan onto a photodiode. Each time a blade passes,
it blocks the beam and the photodiode signal jumps up (this rig reads near 0 V while the
beam is clear). You record 1000 blade arrivals and how long each blade blocks the beam,
then use two Gaussian fits: one to the rising edge (which measures the beam), and one to the
histogram of 1000 widths (which gives the blade width). From how long each blade blocks the
beam (τ) and the time between blades (T), you work out how wide the blades are, without
touching the fan.

```
          laser ───────────────► ┃ ◄─ fan blade ─► photodiode ──► AI0
                                  (beam at radius r from the hub)
```

This is a small model of two everyday neuroscience instruments:

- **Scanning microscope:** time is converted into position (size = speed × time), as when
  a two-photon microscope builds an image from a single PMT.
- **Ephys rig:** the blade passes are captured like spikes: a short snippet around each
  threshold crossing, overlaid and averaged to show the waveform's shape.

The full background, and a worked version of exercises 05–07 (sections 1–3), is in
[`notebooks/fan_blade_width.ipynb`](../notebooks/fan_blade_width.ipynb).

### Wiring and safety

| Signal | Connection |
|---|---|
| Photodiode | `AI0` (RSE), photodiode ground to AI GND |
| Fan | Its own power supply, fixed speed. **Not** connected to the DAQ. |
| Laser | Its own power supply. **Not** connected to the DAQ. |

**Remove the AO0 → AI0 loopback wire from Part 1 before you start.** Otherwise AI0 measures
the AO output instead of your photodiode.

⚠️ **Laser:** never look into the beam, and watch out for reflections off the blades.
⚠️ **Fan:** keep fingers clear. It keeps spinning when your script stops, so switch it off
at its supply before reaching near it.

### Procedure

| Step | Do | Script | Time |
|---|---|---|---|
| 1 | Set up the live view (1 TODO) and align the laser and photodiode until the pulses are as tall as possible | `05_fan_live_view.py` | 20 min |
| 2 | Count the blades and measure the beam's distance from the hub. Enter them in `07_fan_analyse.py`. | — | 5 min |
| 3 | Fill in the 3 TODOs and record 1000 blade passes | `06_fan_record.py` | 15 min |
| 4 | Fill in the 6 analysis TODOs and fit the blade width (and the beam's diameter) | `07_fan_analyse.py` | 30 min |
| 5 | Switch off the laser and the fan at their supplies | — | — |

The times include the investigation questions, which have you re-run 06 and 07 with
different thresholds. Recordings are saved in `data/` as `.npz` files (the snippets, when
each blade arrived, how long it blocked the beam, and the sample rate), so you can re-analyse them later:

```bash
uv run python exercises/07_fan_analyse.py                     # newest recording
uv run python exercises/07_fan_analyse.py data/<file>.npz     # a particular recording
```

**No rig yet?** Set `SIMULATE = True` in `06_fan_record.py` to make a fake recording of a fan
with 15 mm blades and a 1 mm beam, and use it to check your analysis before the lab.

## How to work through a script

1. Read the docstring at the top: the task, the wiring and the expected behaviour.
2. Set `DEV` in the settings block to your device's name.
3. Find the TODOs and do them in order. Replace each `None` with your code.
4. Run the script from the repository's root folder:
   ```bash
   uv run python exercises/01_analog_input.py       # all parts
   uv run python exercises/01_analog_input.py B     # just Part B
   ```
   If a TODO isn't finished yet, the script stops and tells you which one.
5. When everything runs, answer the **investigation questions** at the top of the file in
   your lab notebook. The times above include them.

## Tips

- Every DAQ operation follows the same pattern: create a task → add channels → configure
  timing → read/write → close. `with nidaqmx.Task() as task:` closes the task for you.
- An error saying the task has no channels usually means you skipped an "add channel" TODO.
- Error -50103 ("resource is reserved") usually means a notebook kernel or another script
  still holds the device. Close it first.
- Stuck? Find the matching section of `notebooks/nidaqmx_tutorial.ipynb` and the
  [nidaqmx documentation](https://nidaqmx-python.readthedocs.io/).
