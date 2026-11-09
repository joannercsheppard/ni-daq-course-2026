"""
Exercise 06: Fan experiment, record the photodiode                (about 10 min)
==================================================

Task
----
Make one finite, hardware-timed recording of the photodiode and save it as a
CSV file in data/. Exercise 07 analyses it. Keeping recording and analysis
separate is normal practice: you can re-analyse your data later without going
back to the rig.

No trigger is needed: the fan spins all the time, so it doesn't matter where
in a rotation the recording starts.

Before you start
----------------
* Align the beam with exercise 05 first. Same wiring: photodiode on AI0, no
  loopback wire.
* No hardware? Set SIMULATE = True to make a fake recording of a fan with
  15 mm blades, then check that exercise 07 gets the right answer.

Run from the repository's root folder:
    uv run python exercises/06_fan_record.py

Expected behaviour
------------------
* The script prints the file it saved and the signal's dark and light levels:
      Saved data/fan_20261109_141502_20000Hz.csv  dark 0.02 V, light 2.01 V
* A plot shows the first 100 ms: a regular train of dips, as in the live view.

Investigation questions
-----------------------
1. Zoom in on one edge of a dip. How many samples does the signal take to go
   from light to dark? Is that limited by the sample rate, or by something
   else, such as the beam's width or the photodiode amplifier?
2. Run this script and exercise 07 two more times. Does the fan's rpm change
   between recordings? Does the blade width? Why should the width stay the
   same even when the speed doesn't?
"""

import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import nidaqmx
import nidaqmx.system
from nidaqmx.constants import AcquisitionType, TerminalConfiguration

# ---------------------------------------------------------------------------
# Settings: change these to match your setup
# ---------------------------------------------------------------------------
DEV = "Dev1"            # device name, as shown in NI MAX
PD_CHAN = f"{DEV}/ai0"  # photodiode

RATE = 20_000           # samples/s. Check your device's maximum (e.g. USB-6001: 20 kS/s)
DURATION = 1.0          # seconds

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


def fake_photodiode(n, rate):
    """Fake fan: 7 blades 15 mm wide, beam 1 mm wide at 30 mm radius, ~20 rev/s."""
    rng = np.random.default_rng()
    t = np.arange(n) / rate
    angle = 2 * np.pi * 20.0 * (1 + rng.normal(0, 0.03)) * t + rng.uniform(0, 2 * np.pi)
    blocked = (angle % (2 * np.pi / 7)) < (15.0 + 1.0) / 30.0
    return np.where(blocked, 0.05, 2.0) + rng.normal(0, 0.02, n)


# ---------------------------------------------------------------------------
# The recording
# ---------------------------------------------------------------------------
def record(rate, duration):
    """One finite, hardware-timed photodiode recording. Returns (t, pd) in s and V."""
    n = int(rate * duration)
    t = np.arange(n) / rate

    if SIMULATE:
        return t, fake_photodiode(n, rate)

    with nidaqmx.Task() as task:
        # TODO 1: Add PD_CHAN as an AI voltage channel (RSE, -10 V to +10 V).

        # TODO 2: Configure FINITE sampling of n samples at `rate`.

        # TODO 3: Replace None with a read of all n samples. Give the read a
        #         timeout longer than the recording (e.g. duration + 5).
        pd = None

    require(pd, "TODO 3")
    return t, np.asarray(pd)


def main():
    if not SIMULATE:
        check_device(DEV, RATE)

    t, pd = record(RATE, DURATION)

    DATA_DIR.mkdir(exist_ok=True)
    prefix = "sim_fan" if SIMULATE else "fan"
    path = DATA_DIR / f"{prefix}_{time.strftime('%Y%m%d_%H%M%S')}_{RATE}Hz.csv"
    np.savetxt(path, np.column_stack([t, pd]), delimiter=",",
               header="time_s,volts", comments="", fmt="%.7g")

    dark, light = np.percentile(pd, [5, 95])
    print(f"Saved {path.relative_to(DATA_DIR.parent)}  dark {dark:.2f} V, light {light:.2f} V")
    if light - dark < 0.1:
        print("⚠️  Very little contrast: is the fan spinning and the beam aligned?")

    show = t < 0.1
    plt.figure(figsize=(10, 3))
    plt.plot(t[show] * 1000, pd[show], ".-", ms=2, lw=0.8)
    plt.xlabel("Time (ms)")
    plt.ylabel("Photodiode (V)")
    plt.title("First 100 ms of the recording")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
