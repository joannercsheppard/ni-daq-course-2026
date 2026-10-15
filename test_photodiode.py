"""Quick photodiode test: record AI0 on the NI DAQ, save it, and plot it.

The fan and laser are powered separately (not from the DAQ); this only records.
Run with:  python test_photodiode.py
Saves photodiode_<time>.csv (columns: time_s, volts) and shows a plot.
"""
import time

import matplotlib.pyplot as plt
import numpy as np

import nidaqmx
import nidaqmx.system
from nidaqmx.constants import AcquisitionType, TerminalConfiguration

DEV = "Dev1"          # change if NI MAX shows a different name
PD_CHAN = f"{DEV}/ai0"
RATE = 20_000         # samples/s. Check your device's maximum (e.g. USB-6001 is 20 kS/s)
DURATION = 1.0        # s to record


def record(rate, duration):
    n = int(rate * duration)
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan(
            PD_CHAN, terminal_config=TerminalConfiguration.RSE, min_val=-10, max_val=10
        )
        task.timing.cfg_samp_clk_timing(rate, sample_mode=AcquisitionType.FINITE, samps_per_chan=n)
        data = np.array(task.read(number_of_samples_per_channel=n, timeout=duration + 5))
    return np.arange(n) / rate, data


def blade_period(pd, rate):
    """Median time between blade pulses, using a threshold halfway between dark and light."""
    threshold = (np.percentile(pd, 5) + np.percentile(pd, 95)) / 2
    blocked = (pd < threshold).astype(int)
    starts = np.flatnonzero(np.diff(blocked) == 1) + 1
    if starts.size < 2:
        return threshold, None
    return threshold, np.median(np.diff(starts)) / rate


# Show which DAQ devices the PC can see, so a wrong DEV name is obvious
names = [d.name for d in nidaqmx.system.System.local().devices]
print("Devices found:", names)
if DEV not in names:
    raise SystemExit(f"'{DEV}' not found. Set DEV at the top of this file to one of {names}.")

t, pd = record(RATE, DURATION)
print(f"Recorded {pd.size} samples: min {pd.min():.3f} V, max {pd.max():.3f} V")

threshold, period = blade_period(pd, RATE)
if period is None:
    print("No blade pulses found. Is the fan spinning and the beam on the photodiode?")
else:
    print(f"Blade period ≈ {period * 1000:.2f} ms ({1 / period:.1f} blades/s)")

fname = time.strftime("photodiode_%Y%m%d_%H%M%S.csv")
np.savetxt(fname, np.column_stack([t, pd]), delimiter=",", header="time_s,volts", comments="")
print("Saved", fname)

plt.plot(t * 1000, pd)
plt.axhline(threshold, color="gray", ls="--", label="threshold")
plt.xlabel("Time (ms)")
plt.ylabel("AI0 (V)")
plt.legend()
plt.show()
