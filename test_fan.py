"""Quick fan test: spin the fan from AO0 on the NI DAQ.

Run with:  python fan_test.py
Type a voltage (e.g. 3) and press Enter to set the fan speed.
Type q (or press Ctrl+C) to stop. The fan is always set back to 0 V on exit.
"""
import nidaqmx
import nidaqmx.system

DEV = "Dev1"          # change if NI MAX shows a different name
FAN_CHAN = f"{DEV}/ao0"
MAX_V = 6.0           # safety cap on what you can type


def set_fan(volts):
    with nidaqmx.Task() as task:
        task.ao_channels.add_ao_voltage_chan(FAN_CHAN, min_val=0, max_val=10)
        task.write(volts)
    print(f"AO0 = {volts:.2f} V")


# Show which DAQ devices the PC can see, so a wrong DEV name is obvious
names = [d.name for d in nidaqmx.system.System.local().devices]
print("Devices found:", names)
if DEV not in names:
    raise SystemExit(f"'{DEV}' not found. Set DEV at the top of this file to one of {names}.")

try:
    set_fan(0.0)
    while True:
        s = input(f"Fan voltage 0-{MAX_V} V (q to quit): ").strip()
        if s.lower() == "q":
            break
        try:
            v = float(s)
        except ValueError:
            print("Type a number, e.g. 3")
            continue
        set_fan(min(max(v, 0.0), MAX_V))
finally:
    set_fan(0.0)
    print("Fan off.")