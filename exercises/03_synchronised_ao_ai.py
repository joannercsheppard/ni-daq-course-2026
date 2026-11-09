"""
Warm-up 03: Synchronised output and input (AO + AI)             (about 15 min)
===================================================

Task
----
A refresher of playing a waveform on AO0 while recording AI0, so that AI
sample i is taken at the same moment as AO sample i. The two tasks are already
set up for you. Your job is the part that locks them together: the trigger and
the start order.

    ai_task.start()  -> armed, waiting...
    ao_task.start()  -> AO starts --(/Dev1/ao/StartTrigger)--> AI starts

Key calls: ai_task.triggers.start_trigger.cfg_dig_edge_start_trig,
task.write(..., auto_start=False), task.start, task.read, task.wait_until_done.
Reference: notebooks/nidaqmx_tutorial.ipynb, section 3.

Before you start
----------------
* Set DEV below to your device's name.
* Loopback wired: AO0 -> AI0 and AO GND -> AI GND.
* This one needs REAL hardware. A simulated device fires triggers immediately
  and records a synthetic signal, so the lag below means nothing on it.

Run from the repository's root folder:
    uv run python exercises/03_synchronised_ao_ai.py

Expected behaviour
------------------
* The script prints how many samples the recording lags the output by, then
  plots both traces: a 20 Hz sine wave that steps up by 1 V halfway through.
* With the trigger and the right start order, the traces sit on top of each
  other and the lag is 0 samples, or very close to it.
* AO0 is set back to 0 V at the end, even after an error.

Investigation questions
-----------------------
1. Comment out your trigger line (TODO 1) and start AI AFTER AO. What lag is
   reported now? Run it a few times: is it the same every time? What would a
   varying lag do to a microscope image?
2. Put the trigger back but start AO BEFORE AI. What happens, and which error
   do you get? Explain it using the diagram above.
"""

import matplotlib.pyplot as plt
import numpy as np

import nidaqmx
import nidaqmx.system
from nidaqmx.constants import AcquisitionType, TerminalConfiguration

# ---------------------------------------------------------------------------
# Settings: change these to match your setup
# ---------------------------------------------------------------------------
DEV = "Dev1"                  # device name, as shown in NI MAX
AO_CHAN = f"{DEV}/ao0"
AI_CHAN = f"{DEV}/ai0"

# A trigger is a *terminal* name, not a channel name, so it starts with "/".
AO_START_TRIGGER = f"/{DEV}/ao/StartTrigger"

RATE = 10_000                 # samples per second, shared by AO and AI
DURATION = 0.2                # s


# ---------------------------------------------------------------------------
# Helpers (provided: you don't need to change these)
# ---------------------------------------------------------------------------
def check_device(name):
    """List the DAQ devices; stop if `name` is missing. Returns True if it's simulated."""
    devices = {d.name: d for d in nidaqmx.system.System.local().devices}
    for d in devices.values():
        sim = ", SIMULATED" if d.dev_is_simulated else ""
        print(f"Device found: {d.name} ({d.product_type}{sim})")
    if name not in devices:
        raise SystemExit(f"'{name}' not found. Set DEV at the top of this file to one of {list(devices)}.")
    return devices[name].dev_is_simulated


def require(value, todo):
    """Stop with a friendly message if a TODO hasn't been filled in yet."""
    if value is None:
        raise SystemExit(f"\n{todo} isn't finished yet. Fill it in and run the script again.")


def zero_ao(channel=AO_CHAN):
    """Set an analog output back to 0 V. Warns instead of failing, so it never hides another error."""
    try:
        with nidaqmx.Task() as task:
            task.ao_channels.add_ao_voltage_chan(channel)
            task.write(0.0)
    except nidaqmx.DaqError as err:
        print(f"Warning: could not reset {channel} to 0 V: {err}")


def make_test_signal(n):
    """A 20 Hz sine wave plus a 1 V step halfway through, ending on 0 V."""
    t = np.arange(n) / RATE
    wave = 1.5 * np.sin(2 * np.pi * 20 * t)
    wave[n // 2:] += 1.0
    wave[-1] = 0.0
    return wave


def estimate_lag(sent, recorded):
    """How many samples `recorded` lags behind `sent`, found by cross-correlation."""
    a = sent - sent.mean()
    b = recorded - recorded.mean()
    corr = np.correlate(b, a, mode="full")
    return int(np.argmax(corr)) - (len(a) - 1)


# ---------------------------------------------------------------------------
# The synchronised recording
# ---------------------------------------------------------------------------
def play_and_record(out_wave):
    n = len(out_wave)

    with nidaqmx.Task() as ao_task, nidaqmx.Task() as ai_task:
        # Provided: both tasks, with the same FINITE timing.
        ao_task.ao_channels.add_ao_voltage_chan(AO_CHAN, min_val=-10, max_val=10)
        ao_task.timing.cfg_samp_clk_timing(RATE, sample_mode=AcquisitionType.FINITE, samps_per_chan=n)
        ai_task.ai_channels.add_ai_voltage_chan(
            AI_CHAN, terminal_config=TerminalConfiguration.RSE, min_val=-10, max_val=10
        )
        ai_task.timing.cfg_samp_clk_timing(RATE, sample_mode=AcquisitionType.FINITE, samps_per_chan=n)

        # TODO 1: Make ai_task wait for AO_START_TRIGGER before it starts.

        # TODO 2: Write out_wave to ao_task without starting it. Then start
        #         the two tasks in the right order (see the diagram at the top).

        # TODO 3: Replace None with a read of all n samples from ai_task
        #         (timeout DURATION + 2 s). Then wait until ao_task is done.
        in_wave = None

    require(in_wave, "TODO 3")
    return np.asarray(in_wave)


def main():
    simulated = check_device(DEV)
    n = int(RATE * DURATION)
    t = np.arange(n) / RATE
    out_wave = make_test_signal(n)

    try:
        in_wave = play_and_record(out_wave)
    finally:
        zero_ao()

    if simulated:
        print("Simulated device: the recorded trace is synthetic, so there's no lag to measure.")
    else:
        lag = estimate_lag(out_wave, in_wave)
        print(f"Recorded lags sent by {lag} samples ({lag / RATE * 1000:.2f} ms)")

    plt.plot(t * 1000, out_wave, label="AO0 (sent)")
    plt.plot(t * 1000, in_wave, "--", label="AI0 (recorded)")
    plt.xlabel("Time (ms)")
    plt.ylabel("Voltage (V)")
    plt.legend()
    plt.title("Synchronised AO -> AI")
    plt.show()


if __name__ == "__main__":
    main()
