"""
Exercise 05: Fan experiment, align the beam with a live view    (about 20 min)
============================================================

Task
----
This is the start of the fan blade experiment (exercises 05-07). A laser beam
passes through a spinning fan onto a photodiode, and each passing blade makes
the signal jump up (on this rig the photodiode reads near 0 V while the
beam is clear and high while a blade blocks it). In 05 you align the setup, in 06 you record, and in 07 you
work out the blade width from the recordings.

Here you show the photodiode signal live while you line up the laser, the fan
and the photodiode. The live plot is provided. You only need to set up the
continuous AI task (one TODO), exactly as in warm-up 04, so you can start
aligning straight away.
Reference: notebooks/fan_blade_width.ipynb, section 1.

The DAQ only records here. The fan and the laser run from their own power
supplies and are NOT connected to the DAQ.

Before you start
----------------
* Wiring: photodiode output -> AI0, photodiode ground -> AI GND.
  REMOVE the AO0 -> AI0 loopback wire from the warm-up exercises.
* Switch the laser and the fan on at their own supplies.
* Laser safety: never look into the beam, and watch for reflections off the
  blades. Keep fingers away from the spinning fan.

Run from the repository's root folder:
    uv run python exercises/05_fan_live_view.py

Close the plot window (or press Ctrl+C) to stop.

Expected behaviour
------------------
* A window shows the last CHUNK samples (250 ms), updated 4 times a second.
* With the beam aligned and the fan spinning, you see a regular train of
  pulses: the bottom of the trace is the "unblocked" level, and the top of
  each pulse is the "blocked" level when a blade fully blocks the beam.
* The title shows both levels and the contrast between them. Adjust the
  alignment until the contrast is as large as you can get it. A contrast below
  about 0.1 V is too small to analyse.

Investigation questions
-----------------------
1. Block the beam with a card, then switch the room lights on and off. How
   much does the blocked level change? Why should the threshold sit between
   your own rig's two levels, rather than at a fixed voltage?
2. Read the time from one pulse to the next off the x-axis (measure across
   several pulses and divide, for accuracy). Using the number of blades on the
   fan, estimate the fan's speed in revolutions per minute. You'll compare
   this with the analysed value in exercise 07.
"""

import time

import numpy as np
import pyqtgraph as pg

import nidaqmx
import nidaqmx.system
from nidaqmx.constants import AcquisitionType, TerminalConfiguration

# ---------------------------------------------------------------------------
# Settings: change these to match your setup
# ---------------------------------------------------------------------------
DEV = "Dev1"            # device name, as shown in NI MAX
PD_CHAN = f"{DEV}/ai0"  # photodiode

RATE = 20_000           # samples/s. Check your device's maximum (e.g. USB-6001: 20 kS/s)
CHUNK = 5_000           # samples per update (250 ms at 20 kS/s)
VIEW_FOR = 120.0        # seconds before the live view stops by itself
Y_MAX = 6.0             # top of the plot's y-axis (V)


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
        print(f"Note: '{name}' is simulated, so you'll see a synthetic signal, not your photodiode.")
    max_rate = devices[name].ai_max_single_chan_rate
    if rate > max_rate:
        raise SystemExit(f"{name} can sample at most {max_rate:.0f} samples/s. Lower RATE.")


def require(value, todo):
    """Stop with a friendly message if a TODO hasn't been filled in yet."""
    if value is None:
        raise SystemExit(f"\n{todo} isn't finished yet. Fill it in and run the script again.")


# ---------------------------------------------------------------------------
def main():
    check_device(DEV, RATE)

    app = pg.mkQApp("Fan live view")
    win = pg.PlotWidget()
    win.resize(1000, 350)
    win.setYRange(-0.2, Y_MAX)
    win.setLabel("bottom", "Time within update (ms)")
    win.setLabel("left", "Photodiode (V)")
    x_ms = np.arange(CHUNK) / RATE * 1000
    curve = win.plot(x_ms, np.zeros(CHUNK))
    win.show()

    with nidaqmx.Task() as task:
        # TODO 1: Add PD_CHAN as an AI voltage channel (RSE, -10 V to +10 V),
        #         configure CONTINUOUS sampling at RATE with a buffer of
        #         10 * CHUNK samples, and start the task (as in warm-up 04).

        require(task.channel_names or None, "TODO 1")

        t_end = time.time() + VIEW_FOR
        while time.time() < t_end and win.isVisible():
            chunk = np.asarray(task.read(number_of_samples_per_channel=CHUNK))
            low, high = np.percentile(chunk, [5, 95])
            curve.setData(x_ms, chunk)
            win.setTitle(f"unblocked ≈ {low:.2f} V    blocked ≈ {high:.2f} V    "
                         f"contrast {high - low:.2f} V")
            app.processEvents()  # redraw the window and handle clicks

    win.close()
    print("Live view stopped.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped with Ctrl+C.")
