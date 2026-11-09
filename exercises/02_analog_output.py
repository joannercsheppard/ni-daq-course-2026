"""
Warm-up 02: Analog output (AO)                                  (about 10 min)
==============================

Task
----
A refresher of making the DAQ produce voltages, in two parts:

  Part A  On-demand output: set AO0 to SET_V, and read it back on AI0.
  Part B  Finite, hardware-timed waveform: play 5 cycles of a 50 Hz sine
          wave on AO0 using the device's sample clock.

For a timed output, the order matters: configure timing -> write the whole
buffer without starting -> start -> wait until done -> stop.

Key calls: task.ao_channels.add_ao_voltage_chan, task.timing.cfg_samp_clk_timing,
task.write(..., auto_start=False), task.start, task.wait_until_done, task.stop.
Reference: notebooks/nidaqmx_tutorial.ipynb, section 2.

Before you start
----------------
* Set DEV below to your device's name.
* Loopback wired: AO0 -> AI0 and AO GND -> AI GND. Nothing else on AO0.
  On a simulated device the read-back won't match what you wrote. That's expected.

Run from the repository's root folder:
    uv run python exercises/02_analog_output.py       # Parts A and B
    uv run python exercises/02_analog_output.py B     # Part B only

Expected behaviour
------------------
* Part A prints the voltage written and the voltage read back. With the
  loopback, they agree to within a few mV.
* Part B plays the sine wave, then plots the samples that were sent: a 2 V
  sine wave, 100 ms long, drawn as a staircase.
* When the script ends, even after an error or Ctrl+C, zero_ao() puts AO0
  back to 0 V.

Investigation questions
-----------------------
1. Set DURATION = 0.105 (so the wave no longer ends on a whole cycle) and
   comment out the zero_ao() calls in Part B and main(). Run Part B, then
   warm-up 01 Part A. What voltage is left on AO0, and why would that matter
   if AO0 controlled a laser's power?
2. In Part A, try SET_V = 12. What happens, and what are min_val and max_val
   protecting you from?
"""

import sys

import matplotlib.pyplot as plt
import numpy as np

import nidaqmx
import nidaqmx.system
from nidaqmx.constants import AcquisitionType, TerminalConfiguration

# ---------------------------------------------------------------------------
# Settings: change these to match your setup
# ---------------------------------------------------------------------------
DEV = "Dev1"               # device name, as shown in NI MAX
AO_CHAN = f"{DEV}/ao0"
AI_CHAN = f"{DEV}/ai0"     # for the loopback read-back

SET_V = 2.5                # Part A: on-demand output voltage (V)

AO_RATE = 10_000           # Part B: output samples per second
FREQ = 50                  # Hz
AMPLITUDE = 2.0            # V
DURATION = 0.1             # s (5 cycles at 50 Hz)

PARTS_TO_RUN = ["A", "B"]  # or pass the parts on the command line


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


def zero_ao(channel=AO_CHAN):
    """Set an analog output back to 0 V. Warns instead of failing, so it never hides another error."""
    try:
        with nidaqmx.Task() as task:
            task.ao_channels.add_ao_voltage_chan(channel)
            task.write(0.0)
    except nidaqmx.DaqError as err:
        print(f"Warning: could not reset {channel} to 0 V: {err}")


def read_back():
    """One on-demand read of AI_CHAN (you wrote this in warm-up 01)."""
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan(
            AI_CHAN, terminal_config=TerminalConfiguration.RSE, min_val=-10, max_val=10
        )
        return task.read()


# ---------------------------------------------------------------------------
# Part A: on-demand output
# ---------------------------------------------------------------------------
def part_a_on_demand():
    with nidaqmx.Task() as ao_task:
        # TODO A1: Add AO_CHAN as an AO voltage channel (-10 V to +10 V), then
        #          write SET_V to it. With no timing configured, the output
        #          changes at once and STAYS there after the task closes.

        require(ao_task.channel_names or None, "TODO A1")

    print(f"Wrote {SET_V:.3f} V to AO0; AI0 reads {read_back():.3f} V")


# ---------------------------------------------------------------------------
# Part B: finite, hardware-timed waveform
# ---------------------------------------------------------------------------
def part_b_waveform():
    n_ao = int(AO_RATE * DURATION)
    t_ao = np.arange(n_ao) / AO_RATE
    waveform = AMPLITUDE * np.sin(2 * np.pi * FREQ * t_ao)

    with nidaqmx.Task() as ao_task:
        # TODO B1: Add AO_CHAN (-10 V to +10 V) and configure FINITE timing
        #          of n_ao samples at AO_RATE.

        # TODO B2: Write `waveform` into the buffer WITHOUT starting the task.

        # TODO B3: Start the task, wait until it's done (timeout DURATION + 2 s),
        #          then stop it.

        require(ao_task.channel_names or None, "TODO B1")

    zero_ao()  # the last sample stays on the output, so go back to 0 V

    plt.plot(t_ao * 1000, waveform, drawstyle="steps-post")
    plt.xlabel("Time (ms)")
    plt.ylabel("AO0 (V)")
    plt.title("Part B: waveform that was played")
    plt.show()


# ---------------------------------------------------------------------------
PARTS = {"A": part_a_on_demand, "B": part_b_waveform}


def main():
    parts = [p.upper() for p in sys.argv[1:]] or PARTS_TO_RUN
    check_device(DEV)
    try:
        for p in parts:
            if p not in PARTS:
                raise SystemExit(f"Unknown part '{p}'. Choose from {list(PARTS)}.")
            print(f"\n=== Part {p} ===")
            PARTS[p]()
    finally:
        zero_ao()  # always leave the output at 0 V, even after an error or Ctrl+C


if __name__ == "__main__":
    main()
