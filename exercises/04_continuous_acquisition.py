"""
Warm-up 04: Continuous acquisition                              (about 10 min)
==================================

Task
----
A refresher of streaming data for as long as you like, by reading chunks from
the DAQ's buffer in a loop. The fan experiment's live view (exercise 05)
uses exactly this, with a plot added.

In continuous mode the device keeps filling a circular BUFFER in the
computer's memory. Your loop must read chunks out of it fast enough that unread
samples aren't overwritten. Aim for roughly 5-10 reads per second.

Key calls: task.timing.cfg_samp_clk_timing(..., sample_mode=AcquisitionType.CONTINUOUS),
task.start, task.read(number_of_samples_per_channel=...).
Reference: notebooks/nidaqmx_tutorial.ipynb, section 4a.

Before you start
----------------
* Set DEV below to your device's name. Any signal on AI0 will do.

Run from the repository's root folder:
    uv run python exercises/04_continuous_acquisition.py

Expected behaviour
------------------
* A running count of chunks is printed (about 15 after RUN_FOR = 3 s), then a
  plot shows all the data joined together, with no gaps.
* Ctrl+C stops the recording cleanly.

Investigation questions
-----------------------
1. Add time.sleep(1.5) inside the while loop, set RUN_FOR = 10, and run it.
   What error do you get, and after roughly how long? Work out when it should
   happen from BUFFER, RATE and CHUNK. Then fix it without removing the sleep.
2. Try CHUNK = 100 and then CHUNK = 20_000 (keep BUFFER = 10 * CHUNK). How
   often does the count update in each case? Why is 5-10 reads per second a
   good target for a live display?
"""

import time

import matplotlib.pyplot as plt
import numpy as np

import nidaqmx
import nidaqmx.system
from nidaqmx.constants import AcquisitionType, TerminalConfiguration

# ---------------------------------------------------------------------------
# Settings: change these to match your setup
# ---------------------------------------------------------------------------
DEV = "Dev1"                  # device name, as shown in NI MAX
AI_CHAN = f"{DEV}/ai0"

RATE = 10_000                 # samples per second
CHUNK = 2_000                 # samples per read (5 reads per second)
BUFFER = 10 * CHUNK           # size of the circular buffer, in samples
RUN_FOR = 3.0                 # seconds


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
def main():
    check_device(DEV)
    chunks = []

    with nidaqmx.Task() as task:
        # TODO 1: Add AI_CHAN (RSE, -10 V to +10 V), configure CONTINUOUS
        #         sampling at RATE with a buffer of BUFFER samples, and start
        #         the task. (For continuous tasks, samps_per_chan sets the
        #         buffer size, not the total number of samples.)

        t_start = time.time()
        while time.time() - t_start < RUN_FOR:
            # TODO 2: Replace None with a read of CHUNK samples.
            chunk = None
            require(chunk, "TODO 2")

            chunks.append(np.asarray(chunk))
            print(f"\rRead {len(chunks)} chunks, mean = {chunks[-1].mean():+.3f} V", end="")
    print()

    data = np.concatenate(chunks)
    t = np.arange(len(data)) / RATE
    plt.figure(figsize=(10, 3))
    plt.plot(t, data)
    plt.xlabel("Time (s)")
    plt.ylabel("AI0 (V)")
    plt.title(f"Continuous acquisition: {len(data)} samples")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped with Ctrl+C.")
