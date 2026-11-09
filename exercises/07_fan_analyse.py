"""
Exercise 07: Fan experiment, measure the blade width              (about 30 min)
====================================================

Task
----
Turn a photodiode recording into a blade width. Each time a blade passes, it
blocks the beam and the signal dips:

    photodiode   ─────┐     ┌─────────┐     ┌─────────┐     ┌────
    signal            │     │         │     │         │     │
                      └─────┘         └─────┘         └─────┘
                      ◄─ τ ─►
                      ◄────── T ──────►

  1. Pulses (TODOs 1-2): the threshold is halfway between the dark and light
     levels (provided). Find where the signal crosses it, which gives each
     pulse's start and width τ. This is how spikes are detected in ephys.
  2. Width (TODOs 3-4): time becomes distance, as in a scanning microscope.
         blade period         T = median time between pulse starts
         rotation frequency   f = 1 / (N_BLADES * T)
         blade speed at beam  v = 2π * BEAM_RADIUS_MM * f
         blade width          w = v * τ - BEAM_DIAMETER_MM

Before you start
----------------
* Record with exercise 06. (With SIMULATE = True there, the true width is
  15 mm, using the settings below as they are.)
* Measure your fan and optics and enter them in the settings below.

Run from the repository's root folder:
    uv run python exercises/07_fan_analyse.py                     # newest recording in data/
    uv run python exercises/07_fan_analyse.py data/<file>.csv     # a particular recording

Expected behaviour
------------------
* Prints the number of pulses found, the fan's speed in rpm and the median
  blade width with its spread. With simulated data, the width is close to 15 mm.
* Plots the first 100 ms with the detected pulses shaded orange: each shaded
  region should line up with a dip.

Investigation questions
-----------------------
1. Measure a blade with a ruler and compare. Fan blades are angled (pitched):
   which width does the beam actually measure?
2. Set RATE = 2_000 in exercise 06, record and analyse again. How many samples
   long is each pulse now? An edge can only be placed to the nearest sample:
   how many mm of blade width is one sample worth at 2 kS/s, and at 20 kS/s?
   An action potential lasts about 1 ms: what sample rate would you need to
   measure spike widths?
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------------------
# Settings: measure these on your rig!
# ---------------------------------------------------------------------------
N_BLADES = 7
BEAM_RADIUS_MM = 30.0     # distance from the fan's axis to the laser beam
BEAM_DIAMETER_MM = 1.0    # laser spot size at the fan

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# ---------------------------------------------------------------------------
# Helpers (provided: you don't need to change these)
# ---------------------------------------------------------------------------
def require(value, todo):
    """Stop with a friendly message if a TODO hasn't been filled in yet."""
    if value is None:
        raise SystemExit(f"\n{todo} isn't finished yet. Fill it in and run the script again.")


def load_recording():
    """Load the CSV named on the command line, or the newest one in data/. Returns (t, pd, rate)."""
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        files = sorted(DATA_DIR.glob("*.csv"), key=lambda p: p.stat().st_mtime)
        if not files:
            raise SystemExit("No recordings found. Record one with exercises/06_fan_record.py first.")
        path = files[-1]
    data = np.loadtxt(path, delimiter=",", skiprows=1)
    t, pd = data[:, 0], data[:, 1]
    rate = round(1 / (t[1] - t[0]))
    print(f"File: {path.name} ({len(pd)} samples at {rate} samples/s)")
    return t, pd, rate


# ---------------------------------------------------------------------------
# Your analysis
# ---------------------------------------------------------------------------
def find_pulses(signal, threshold, rate):
    """Find the intervals where signal < threshold. Returns (starts, widths) in seconds."""
    # TODO 1: Replace None with `blocked`: an array of 0s and 1s, 1 where
    #         signal < threshold.
    #         Hint: a comparison gives True/False; .astype(int) turns it into 1/0.
    blocked = None
    require(blocked, "TODO 1")

    # TODO 2: np.diff(blocked) is +1 where a blade arrives (0 -> 1) and -1
    #         where it leaves (1 -> 0). Replace the Nones with the sample indices
    #         of the arrivals (`starts`) and the departures (`ends`).
    #         Hint: np.flatnonzero(condition) gives the indices where it's true.
    #         Add 1, because np.diff is one sample shorter than its input.
    starts = None
    ends = None
    require(starts, "TODO 2")
    require(ends, "TODO 2")

    # Provided: keep only complete pulses (drop one already underway when the
    # recording started, and one still underway when it ended), and ignore
    # "pulses" shorter than 0.2 ms, which are noise near the threshold.
    if starts.size == 0 or ends.size == 0:
        return np.array([]), np.array([])
    ends = ends[ends > starts[0]]
    n = min(starts.size, ends.size)
    starts, ends = starts[:n], ends[:n]
    keep = (ends - starts) / rate >= 0.2e-3
    return starts[keep] / rate, (ends - starts)[keep] / rate


def blade_widths(starts, widths):
    """Per-pulse blade width (mm) and the rotation frequency (Hz)."""
    # TODO 3: Replace the Nones with the blade period T (the median time
    #         between successive pulse starts; np.diff helps again) and the
    #         rotation frequency f = 1 / (N_BLADES * T).
    blade_period = None
    rot_freq = None
    require(blade_period, "TODO 3")
    require(rot_freq, "TODO 3")

    # TODO 4: Replace the Nones with the blade speed at the beam,
    #         v = 2π * BEAM_RADIUS_MM * f (mm/s), and the width of every pulse
    #         in mm: v * widths - BEAM_DIAMETER_MM.
    speed_mm_s = None
    w_mm = None
    require(speed_mm_s, "TODO 4")
    require(w_mm, "TODO 4")
    return w_mm, rot_freq


# ---------------------------------------------------------------------------
def main():
    t, pd, rate = load_recording()

    dark, light = np.percentile(pd, [5, 95])
    threshold = (dark + light) / 2
    if light - dark < 0.1:
        raise SystemExit("Very little contrast between light and dark. Check the alignment (exercise 05).")

    starts, widths = find_pulses(pd, threshold, rate)
    if len(starts) < 2:
        raise SystemExit("Fewer than 2 pulses found. Is the fan spinning and the beam aligned?")
    w_mm, rot_freq = blade_widths(starts, widths)

    print(f"Pulses:      {len(widths)} found, median width {np.median(widths) * 1e3:.3f} ms")
    print(f"Fan speed:   {rot_freq * 60:.0f} rpm")
    print(f"Blade width: {np.median(w_mm):.2f} mm (median, spread ±{np.std(w_mm):.2f} mm)")

    show = t < 0.1
    plt.figure(figsize=(10, 3))
    plt.plot(t[show] * 1000, pd[show], lw=0.8)
    plt.axhline(threshold, color="k", ls=":", label="threshold")
    for s, w in zip(starts, widths):
        if s < 0.1:
            plt.axvspan(s * 1000, (s + w) * 1000, color="orange", alpha=0.3)
    plt.xlabel("Time (ms)")
    plt.ylabel("Photodiode (V)")
    plt.title("Detected pulses (first 100 ms)")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
