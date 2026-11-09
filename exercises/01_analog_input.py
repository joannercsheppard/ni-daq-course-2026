"""
Warm-up 01: Analog input (AI)                                   (about 10 min)
=============================

Task
----
A refresher of reading voltages from the DAQ, in two parts:

  Part A  On-demand read: read one value from AI0 when Python asks for it.
  Part B  Finite, hardware-timed acquisition: the DAQ's own clock takes
          N_SAMPLES samples at RATE samples/s, and you plot them.

Key calls: task.ai_channels.add_ai_voltage_chan, task.timing.cfg_samp_clk_timing,
task.read. Reference: notebooks/nidaqmx_tutorial.ipynb, section 1.

Before you start
----------------
* Set DEV below to your device's name. The script prints the names it can find.
* Wire the loopback used by all the warm-ups: AO0 -> AI0 and AO GND -> AI GND.
  Until something drives AO0 (warm-up 02), AI0 just reads about 0 V.
* A simulated device from NI MAX also works here. It returns a synthetic signal.

Run from the repository's root folder:
    uv run python exercises/01_analog_input.py        # Parts A and B
    uv run python exercises/01_analog_input.py B      # Part B only

Expected behaviour
------------------
* Part A prints one voltage between -10 V and +10 V.
* Part B prints the minimum and maximum of 1000 samples and plots them over
  100 ms. Close the plot window to finish.
* If a TODO isn't done yet, the script stops and tells you which one.

Investigation questions
-----------------------
1. In Part A, read 5 values in a loop and time each read with
   time.perf_counter(). How evenly spaced are they? Why do the experiment's
   recordings use the hardware sample clock instead?
2. Look up your device's maximum AI sample rate (NI MAX or the datasheet) and
   set RATE above it. What happens, and at which line?
"""

import sys
import time

import matplotlib.pyplot as plt
import numpy as np

import nidaqmx
import nidaqmx.system
from nidaqmx.constants import AcquisitionType, TerminalConfiguration

# ---------------------------------------------------------------------------
# Settings: change these to match your setup
# ---------------------------------------------------------------------------
DEV = "Dev1"                # device name, as shown in NI MAX
AI_CHAN = f"{DEV}/ai0"

RATE = 10_000               # samples per second
N_SAMPLES = 1_000           # samples per recording (0.1 s at 10 kS/s)

PARTS_TO_RUN = ["A", "B"]   # or pass the parts on the command line


# ---------------------------------------------------------------------------
# Helpers (provided: you don't need to change these)
# ---------------------------------------------------------------------------
def check_device(name):
    """List the DAQ devices this computer can see, and stop if `name` isn't one of them."""
    devices = {d.name: d for d in nidaqmx.system.System.local().devices}
    for d in devices.values():
        sim = ", SIMULATED" if d.dev_is_simulated else ""
        print(f"Device found: {d.name} ({d.product_type}{sim})")
    if name not in devices:
        raise SystemExit(f"'{name}' not found. Set DEV at the top of this file to one of {list(devices)}.")


def require(value, todo):
    """Stop with a friendly message if a TODO hasn't been filled in yet."""
    if value is None:
        raise SystemExit(f"\n{todo} isn't finished yet. Fill it in and run the script again.")


# ---------------------------------------------------------------------------
# Part A: on-demand read
# ---------------------------------------------------------------------------
def part_a_on_demand():
    with nidaqmx.Task() as task:
        # TODO A1: Add AI_CHAN as an AI voltage channel (RSE, -10 V to +10 V).

        # TODO A2: Replace None with a single on-demand read.
        value = None

    require(value, "TODO A2")
    print(f"AI0 = {value:.4f} V")


# ---------------------------------------------------------------------------
# Part B: finite, hardware-timed acquisition
# ---------------------------------------------------------------------------
def part_b_finite():
    with nidaqmx.Task() as task:
        # TODO B1: Add AI_CHAN as in A1, then configure FINITE sampling of
        #          N_SAMPLES samples at RATE.

        # TODO B2: Replace None with a read of all N_SAMPLES samples.
        data = None

    require(data, "TODO B2")
    data = np.asarray(data)
    t = np.arange(len(data)) / RATE

    print(f"Recorded {data.size} samples: min {data.min():.3f} V, max {data.max():.3f} V")
    plt.plot(t * 1000, data)
    plt.xlabel("Time (ms)")
    plt.ylabel("AI0 (V)")
    plt.title("Part B: finite acquisition")
    plt.show()


# ---------------------------------------------------------------------------
PARTS = {"A": part_a_on_demand, "B": part_b_finite}


def main():
    parts = [p.upper() for p in sys.argv[1:]] or PARTS_TO_RUN
    check_device(DEV)
    for p in parts:
        if p not in PARTS:
            raise SystemExit(f"Unknown part '{p}'. Choose from {list(PARTS)}.")
        print(f"\n=== Part {p} ===")
        PARTS[p]()


if __name__ == "__main__":
    main()
