"""
Exercise 06: Fan experiment, record blade passes                  (about 15 min)
================================================

Task
----
Record the photodiode around every blade pass and overlay them. The DAQ
streams continuously, as in warm-up 04. Each time the signal falls through
THRESHOLD_V (a blade arriving at the beam), the script keeps the PRE samples
before the crossing and the POST samples after it. After N_SNIPPETS blade
passes it saves them to data/ for exercise 07, and plots them all on top of
each other, lined up on the crossing.

This is how many ephys systems store spikes: a short "snippet" of voltage
around each threshold crossing, overlaid to show the waveform's shape.

Before you start
----------------
* Align the beam with exercise 05 first. Same wiring: photodiode on AI0, no
  loopback wire.
* Set THRESHOLD_V to roughly halfway between the dark and light levels that
  exercise 05 showed.
* No hardware? Set SIMULATE = True to make fake blade passes from a fan with
  15 mm blades, then check that exercise 07 gets the right answer.

Run from the repository's root folder:
    uv run python exercises/06_fan_record.py

Expected behaviour
------------------
* A running count that reaches N_SNIPPETS within a few seconds, then the file
  it saved and the signal's dark and light levels:
      1000 / 1000 blade passes
      Saved data/fan_snippets_20261109_141502_20000Hz.npz  dark 0.05 V, light 2.00 V
* A plot of all the snippets overlaid, with their mean in black. At t = 0
  every trace falls through the threshold together, so that edge is sharp.

Investigation questions
-----------------------
1. The edge at t = 0 is sharp. Why are the edges further away from t = 0
   blurred? What does the blurring tell you about the fan?
2. Change THRESHOLD_V (keep it between dark and light) and record again. What
   moves in the plot, and what doesn't?
3. Zoom in on the edge at t = 0. How many samples does the signal take to go
   from light to dark? Is that limited by the sample rate, or by something
   else, such as the beam's width?
"""

import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.special import erf

import nidaqmx
import nidaqmx.system
from nidaqmx.constants import AcquisitionType, TerminalConfiguration

# ---------------------------------------------------------------------------
# Settings: change these to match your setup
# ---------------------------------------------------------------------------
DEV = "Dev1"            # device name, as shown in NI MAX
PD_CHAN = f"{DEV}/ai0"  # photodiode

RATE = 20_000           # samples/s. Check your device's maximum (e.g. USB-6001: 20 kS/s)
CHUNK = 2_000           # samples per read (10 reads per second)

THRESHOLD_V = 1.0       # a blade arriving makes the signal fall through this (V)
PRE = 500               # samples kept before each crossing
POST = 500              # samples kept after each crossing
N_SNIPPETS = 1000       # blade passes to record
MIN_GAP_S = 0.5e-3      # ignore crossings this soon after the last one (noise on the same edge)
MAX_SECONDS = 30.0      # give up if there aren't enough blade passes by then

SIMULATE = False        # True: make fake data instead of using the DAQ

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# ---------------------------------------------------------------------------
# Helpers (provided: you don't need to change these)
# ---------------------------------------------------------------------------
def check_device(name, rate):
    """Stop with a clear message if the device is missing or too slow for `rate`."""
    devices = {d.name: d for d in nidaqmx.system.System.local().devices}
    for d in devices.values():
        sim = ", SIMULATED" if d.dev_is_simulated else ""
        print(f"Device found: {d.name} ({d.product_type}{sim})")
    if name not in devices:
        raise SystemExit(f"'{name}' not found. Set DEV at the top of this file to one of {list(devices)}.")
    if devices[name].dev_is_simulated:
        print(f"Note: '{name}' is simulated, so it records a synthetic signal, not your photodiode.")
    max_rate = devices[name].ai_max_single_chan_rate
    if rate > max_rate:
        raise SystemExit(f"{name} can sample at most {max_rate:.0f} samples/s. Lower RATE.")


def require(value, todo):
    """Stop with a friendly message if a TODO hasn't been filled in yet."""
    if value is None:
        raise SystemExit(f"\n{todo} isn't finished yet. Fill it in and run the script again.")


def fake_reader(rate, chunk):
    """For SIMULATE: returns a function that reads `chunk` samples of a fake fan.

    7 blades about 15 mm wide, a Gaussian laser beam 1 mm across (1/e² diameter)
    at 30 mm radius, about 20 rev/s with a slight wobble in speed.
    """
    rng = np.random.default_rng()
    n_blades, radius_mm, beam_mm = 7, 30.0, 1.0
    blade_mm = 15.0 + rng.normal(0, 0.15, n_blades)  # the blades differ slightly
    speed = 2 * np.pi * radius_mm * 20.0 * (1 + rng.normal(0, 0.03))  # mm/s
    pitch = 2 * np.pi * radius_mm / n_blades  # mm from one blade to the next
    start = rng.uniform(0, 100 * pitch)
    sigma = beam_mm / 4
    n_done = 0

    def read_chunk():
        nonlocal n_done
        t = (n_done + np.arange(chunk)) / rate
        n_done += chunk
        x = start + speed * t + 0.01 * speed / (2 * np.pi) * np.sin(2 * np.pi * t)  # mm travelled
        k = np.floor((x + (pitch - 15.0) / 2) / pitch)  # nearest blade
        s = x - k * pitch                                # beam position from its leading edge
        w = blade_mm[k.astype(int) % n_blades]
        blocked = (erf(s / (np.sqrt(2) * sigma)) - erf((s - w) / (np.sqrt(2) * sigma))) / 2
        return 2.0 - 1.95 * blocked + rng.normal(0, 0.02, chunk)

    return read_chunk


# ---------------------------------------------------------------------------
# Your code
# ---------------------------------------------------------------------------
def find_crossings(signal, threshold):
    """Sample indices where `signal` falls through `threshold` (a blade arriving)."""
    # TODO 3: Replace None with the indices i where signal[i - 1] >= threshold
    #         and signal[i] < threshold.
    #         Hint: compare signal[:-1] and signal[1:], combine the two with &,
    #         then np.flatnonzero(...) + 1.
    crossings = None
    require(crossings, "TODO 3")
    return crossings


def collect(read_chunk, rate):
    """Read chunks until there are N_SNIPPETS complete snippets.

    Returns (snippets, crossings, data): snippets has one row per blade pass,
    crossings are the sample indices of the crossings in data.
    """
    data = np.empty(0)
    crossings = np.empty(0, dtype=int)
    t_end = time.time() + MAX_SECONDS
    while time.time() < t_end:
        data = np.concatenate([data, read_chunk()])
        crossings = find_crossings(data, THRESHOLD_V)
        # Like a refractory period in spike detection: noise on one edge can
        # cross the threshold several times, so keep only the first.
        crossings = crossings[np.diff(crossings, prepend=-10**9) > MIN_GAP_S * rate]
        # Keep only crossings with PRE samples before and POST samples after.
        crossings = crossings[(crossings >= PRE) & (crossings + POST <= data.size)]
        print(f"\r{len(crossings)} / {N_SNIPPETS} blade passes", end="")
        if len(crossings) >= N_SNIPPETS:
            print()
            crossings = crossings[:N_SNIPPETS]
            snippets = np.stack([data[c - PRE:c + POST] for c in crossings])
            return snippets, crossings, data

    dark, light = np.percentile(data, [5, 95])
    raise SystemExit(f"\nOnly {len(crossings)} blade passes in {MAX_SECONDS:.0f} s. Set THRESHOLD_V "
                     f"between the dark ({dark:.2f} V) and light ({light:.2f} V) levels.")


def main():
    if SIMULATE:
        snippets, crossings, data = collect(fake_reader(RATE, CHUNK), RATE)
    else:
        check_device(DEV, RATE)
        with nidaqmx.Task() as task:
            # TODO 1: Add PD_CHAN as an AI voltage channel (RSE, -10 V to +10 V),
            #         configure CONTINUOUS sampling at RATE with a buffer of
            #         10 * CHUNK samples, and start the task (as in exercise 05).

            require(task.channel_names or None, "TODO 1")

            def read_chunk():
                # TODO 2: Replace None with a read of CHUNK samples.
                chunk = None
                require(chunk, "TODO 2")
                return np.asarray(chunk)

            snippets, crossings, data = collect(read_chunk, RATE)

    DATA_DIR.mkdir(exist_ok=True)
    prefix = "sim_fan_snippets" if SIMULATE else "fan_snippets"
    path = DATA_DIR / f"{prefix}_{time.strftime('%Y%m%d_%H%M%S')}_{RATE}Hz.npz"
    np.savez(path, snippets=snippets, crossings=crossings, rate=RATE, pre=PRE,
             threshold=THRESHOLD_V)

    dark, light = np.percentile(data, [5, 95])
    print(f"Saved {path.relative_to(DATA_DIR.parent)}  dark {dark:.2f} V, light {light:.2f} V")

    t_ms = np.arange(-PRE, POST) / RATE * 1000
    plt.figure(figsize=(10, 4))
    plt.plot(t_ms, snippets.T, color="tab:blue", lw=0.5, alpha=0.05)
    plt.plot(t_ms, snippets.mean(axis=0), color="k", lw=1.5, label="mean")
    plt.axhline(THRESHOLD_V, color="gray", ls=":", label="threshold")
    plt.xlabel("Time from threshold crossing (ms)")
    plt.ylabel("Photodiode (V)")
    plt.title(f"{len(snippets)} blade passes, overlaid")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
