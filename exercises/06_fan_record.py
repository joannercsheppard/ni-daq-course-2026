"""
Exercise 06: Fan experiment, record blade passes                  (about 15 min)
================================================

Task
----
Record the photodiode around every blade arriving at the beam, and overlay
them. The DAQ streams continuously, as in warm-up 04. On this rig the signal
is near 0 V while the beam is clear and jumps up while a blade blocks it.

Each time the signal rises through THRESHOLD_V (a blade arriving), the script
keeps the PRE samples before the crossing and the POST samples after it, so
every snippet looks like this:

    0, 0, 0, 0, ... gradual rise ..., top, top, top, ...
                          ↑ t = 0, the threshold crossing

It also notes how long the signal stays above THRESHOLD_V before dropping back
(how long that blade blocked the beam). After N_SNIPPETS blade passes it saves
the snippets and those times to data/ for exercise 07, and plots the snippets
on top of each other, lined up on the crossing.

This is how many ephys systems store spikes: a short "snippet" of voltage
around each threshold crossing, overlaid to show the waveform's shape.
Reference: notebooks/fan_blade_width.ipynb, section 2.

Before you start
----------------
* Align the beam with exercise 05 first. Same wiring: photodiode on AI0, no
  loopback wire.
* Set THRESHOLD_V to roughly halfway between the clear and blocked levels
  that exercise 05 showed.
* No hardware? Set SIMULATE = True to make fake blade passes from a fan with
  15 mm blades, then check that exercise 07 gets the right answer.

Run from the repository's root folder:
    uv run python exercises/06_fan_record.py

Expected behaviour
------------------
* A running count that reaches N_SNIPPETS within a few seconds, then how long
  the blades blocked the beam, and the file it saved:
      1000 / 1000 blade passes
      Each blade blocked the beam for 3.91 ms on average (3.80 to 4.05 ms)
      Saved data/fan_snippets_20261109_141502_20000Hz.npz  clear 0.05 V, blocked 2.00 V
* A plot of all the snippets overlaid, with their mean in black: flat near
  0 V, rising through the threshold at t = 0, then flat at the top.
* If PRE reaches back to the previous blade, or POST runs on until this blade
  leaves, the script stops and suggests new values.

Investigation questions
-----------------------
1. Zoom in on the edge. How many samples does the signal take to rise? Is
   that limited by the sample rate, or by something else, such as the beam's
   width?
2. Change THRESHOLD_V (keep it between the two levels) and record again. What
   moves in the plot, and what doesn't? Does the average time blocked change?
   Why?
3. The time blocked isn't the same for every blade pass. Give two reasons why
   it varies.
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

THRESHOLD_V = 1.0       # a blade arriving makes the signal rise through this (V)
PRE = 40                # samples kept before each crossing } short enough that a snippet
POST = 40               # samples kept after each crossing  } holds only the rising edge
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


def find_falls(signal, threshold):
    """Sample indices where `signal` drops back through `threshold` (a blade leaving)."""
    return find_crossings(-signal, -threshold)


def check_window(rises, blocked):
    """Stop if PRE and POST would show more than the rising edge.

    `rises` are where blades arrive, `blocked` how many samples each one blocked the beam.
    """
    if len(blocked) < 10:
        return
    period = np.mean(np.diff(rises))  # samples from one blade to the next
    on = np.median(blocked)           # samples the beam stays blocked
    off = period - on                 # samples the beam is clear between blades
    if PRE > 0.8 * off or POST > 0.8 * on:
        raise SystemExit(
            f"\nThe beam is clear for about {off:.0f} samples, then blocked for about {on:.0f}.\n"
            f"With PRE = {PRE} and POST = {POST} a snippet would reach the previous blade or "
            f"this blade leaving.\nTry PRE = {0.6 * off:.0f} and POST = {0.6 * on:.0f}.")


def fake_reader(rate, chunk):
    """For SIMULATE: returns a function that reads `chunk` samples of a fake fan.

    7 blades about 15 mm wide, a Gaussian laser beam 1 mm across (1/e² diameter)
    at 30 mm radius, about 20 rev/s with a slight wobble in speed. Like the rig,
    the signal is near 0 V when the beam is clear and 2 V when it's blocked.
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
        return 0.05 + 1.95 * blocked + rng.normal(0, 0.02, chunk)

    return read_chunk


# ---------------------------------------------------------------------------
# Your code
# ---------------------------------------------------------------------------
def find_crossings(signal, threshold):
    """Sample indices where `signal` rises through `threshold` (a blade arriving)."""
    # TODO 3: Replace None with the indices i where signal[i - 1] < threshold
    #         and signal[i] >= threshold.
    #         Hint: compare signal[:-1] and signal[1:], combine the two with &,
    #         then np.flatnonzero(...) + 1.
    crossings = None
    require(crossings, "TODO 3")
    return crossings


def collect(read_chunk, rate):
    """Read chunks until there are N_SNIPPETS complete snippets.

    Returns (snippets, rises, blocked, data): one row of snippets per blade
    pass, the sample index in data where each blade arrived, and how many
    samples each one kept the signal above THRESHOLD_V.
    """
    data = np.empty(0)
    rises = np.empty(0, dtype=int)
    gap = MIN_GAP_S * rate
    t_end = time.time() + MAX_SECONDS
    while time.time() < t_end:
        data = np.concatenate([data, read_chunk()])
        rises = find_crossings(data, THRESHOLD_V)
        falls = find_falls(data, THRESHOLD_V)
        # Like a refractory period in spike detection: noise can make the signal
        # cross the threshold several times on one edge. Only count a rise if the
        # signal has been below the threshold for at least MIN_GAP_S.
        prev_fall = np.searchsorted(falls, rises) - 1
        rises = rises[(prev_fall < 0) | (rises - falls[np.maximum(prev_fall, 0)] > gap)]
        # The first drop at least MIN_GAP_S after each rise is that blade leaving.
        nxt = np.searchsorted(falls, rises + gap)
        rises = rises[nxt < falls.size]
        blocked = falls[nxt[nxt < falls.size]] - rises
        check_window(rises, blocked)
        # Keep only rises with PRE samples before and POST samples after.
        keep = (rises >= PRE) & (rises + POST <= data.size)
        rises, blocked = rises[keep], blocked[keep]
        print(f"\r{len(rises)} / {N_SNIPPETS} blade passes", end="")
        if len(rises) >= N_SNIPPETS:
            print()
            rises, blocked = rises[:N_SNIPPETS], blocked[:N_SNIPPETS]
            snippets = np.stack([data[r - PRE:r + POST] for r in rises])
            return snippets, rises, blocked, data

    low, high = np.percentile(data, [5, 95])
    raise SystemExit(f"\nOnly {len(rises)} blade passes in {MAX_SECONDS:.0f} s. Set THRESHOLD_V "
                     f"between the clear ({low:.2f} V) and blocked ({high:.2f} V) levels.")


def main():
    if SIMULATE:
        snippets, rises, blocked, data = collect(fake_reader(RATE, CHUNK), RATE)
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

            snippets, rises, blocked, data = collect(read_chunk, RATE)

    DATA_DIR.mkdir(exist_ok=True)
    prefix = "sim_fan_snippets" if SIMULATE else "fan_snippets"
    path = DATA_DIR / f"{prefix}_{time.strftime('%Y%m%d_%H%M%S')}_{RATE}Hz.npz"
    np.savez(path, snippets=snippets, rises=rises, blocked=blocked, rate=RATE, pre=PRE,
             threshold=THRESHOLD_V)

    ms = blocked / RATE * 1000
    print(f"Each blade blocked the beam for {ms.mean():.2f} ms on average "
          f"({ms.min():.2f} to {ms.max():.2f} ms)")
    low, high = np.percentile(data, [5, 95])
    print(f"Saved {path.relative_to(DATA_DIR.parent)}  clear {low:.2f} V, blocked {high:.2f} V")

    t_ms = np.arange(-PRE, POST) / RATE * 1000
    plt.figure(figsize=(10, 4))
    plt.plot(t_ms, snippets.T, color="tab:blue", lw=0.5, alpha=0.05)
    plt.plot(t_ms, snippets.mean(axis=0), color="k", lw=1.5, label="mean")
    plt.axhline(THRESHOLD_V, color="gray", ls=":", label="threshold")
    plt.xlabel("Time from threshold crossing (ms)")
    plt.ylabel("Photodiode (V)")
    plt.title(f"{len(snippets)} blade passes, overlaid")
    plt.legend(loc="upper left")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
