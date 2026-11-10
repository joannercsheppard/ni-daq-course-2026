"""
Exercise 07: Fan experiment, measure the blade width              (about 30 min)
====================================================

Task
----
Turn the recording from exercise 06 into a blade width, with two Gaussian fits.

1. The edge (TODOs 1-3). The laser beam's brightness falls off as a Gaussian
   from its centre. As a blade edge sweeps across it the signal rises
   smoothly, and the SLOPE of that rise is the Gaussian itself:

       mean of the                 ┌──────────
       snippets          ──────────┘

       slope of                    ╭╮
       the mean          ──────────╯╰─────────
                                   ↑ t_edge: the blade edge crosses the beam's centre

   Fit a Gaussian to the slope of the averaged snippets. Its width σ gives the
   beam's diameter (the "knife-edge" method used to measure laser spots on real
   microscopes), and its centre t_edge shows where the threshold crossing
   (t = 0) sits on the edge.

2. The speed (TODO 4): time becomes distance, as in a scanning microscope.
       blade period         T = mean time between blades arriving
       rotation frequency   f = 1 / (N_BLADES * T)
       blade speed at beam  v = 2π * BEAM_RADIUS_MM * f

3. The width (TODOs 5-6). Exercise 06 saved how long each blade kept the
   signal above the threshold. Unless the threshold is exactly halfway up the
   edge, that's not quite the time from one edge's centre to the other's:
   the threshold is crossed t_edge early on the way up, and t_edge late on
   the way down. So each blade pass gives a width
       w = v * (time blocked - 2 * t_edge)
   Plot a histogram of the 1000 widths and fit a Gaussian to it: its centre
   is the blade width, and its σ is how much single blade passes vary. The
   times blocked are whole numbers of samples, so the widths come in steps of
   v / rate mm, and the histogram has one bar per step.

Reference: notebooks/fan_blade_width.ipynb, section 3 (same steps, in order).

Before you start
----------------
* Record with exercise 06. (With SIMULATE = True there, the true width is
  about 15 mm and the beam 1 mm, using the settings below as they are.)
* Count the blades and measure the beam's distance from the fan's axis, and
  enter them in the settings below.

Run from the repository's root folder:
    uv run python exercises/07_fan_analyse.py                     # newest recording in data/
    uv run python exercises/07_fan_analyse.py data/<file>.npz     # a particular recording

Expected behaviour
------------------
* Prints the fan's speed, the edge's centre and the beam diameter, and the
  blade width with its spread. With simulated data: width close to 15 mm,
  beam close to 1 mm.
* Plots the snippets and their mean, the slope with its fitted Gaussian,
  and the histogram of widths with its fitted Gaussian.

Investigation questions
-----------------------
1. Measure a blade with a ruler and compare. Fan blades are angled (pitched):
   which width does the beam actually measure?
2. Record twice in exercise 06 with different values of THRESHOLD_V. Does
   the average time blocked change? Does the blade width? What does the
   - 2 * t_edge correction do?
3. What sets the σ of the histogram? Would it shrink if you recorded more
   blade passes? What would shrink?
4. Single widths come in steps of one sample, yet the fitted width is far
   more precise than that. Where does the extra precision come from? What
   would happen at a much lower sample rate?
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

# ---------------------------------------------------------------------------
# Settings: measure these on your rig!
# ---------------------------------------------------------------------------
N_BLADES = 7
BEAM_RADIUS_MM = 30.0     # distance from the fan's axis to the laser beam
EDGE_FIT_MS = 0.5         # fit the edge's Gaussian within this time of t = 0

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# ---------------------------------------------------------------------------
# Helpers (provided: you don't need to change these)
# ---------------------------------------------------------------------------
def require(value, todo):
    """Stop with a friendly message if a TODO hasn't been filled in yet."""
    if value is None:
        raise SystemExit(f"\n{todo} isn't finished yet. Fill it in and run the script again.")


def load_recording():
    """Load the .npz named on the command line, or the newest in data/.

    Returns (snippets, rises, blocked, rate, pre).
    """
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        files = sorted(DATA_DIR.glob("*.npz"), key=lambda p: p.stat().st_mtime)
        if not files:
            raise SystemExit("No recordings found. Record one with exercises/06_fan_record.py first.")
        path = files[-1]
    f = np.load(path)
    if "blocked" not in f:
        raise SystemExit(f"{path.name} is from an older version of exercise 06. Record it again.")
    snippets, rate, pre = f["snippets"], int(f["rate"]), int(f["pre"])
    print(f"File: {path.name} ({len(snippets)} blade passes at {rate} samples/s)")
    return snippets, f["rises"], f["blocked"], rate, pre


# ---------------------------------------------------------------------------
# Your analysis
# ---------------------------------------------------------------------------
def gaussian(x, amplitude, centre, sigma):
    """A Gaussian of height `amplitude`, centred on `centre`, with width `sigma`."""
    # TODO 2: Replace None with amplitude * exp(-(x - centre)² / (2 * sigma²)).
    #         Use np.exp, so that it works on a whole array of x values.
    return None


def fit_gaussian(x, y, guess):
    """Fit `gaussian` to the points (x, y), starting from `guess`.

    Returns (amplitude, centre, sigma).
    """
    require(gaussian(x, *guess), "TODO 2")
    # TODO 3: Replace None with the fitted parameters. curve_fit(model, x, y,
    #         p0=guess) fits model(x, *params) to y, starting from `guess`,
    #         and returns (params, covariance). Keep only params.
    params = None
    require(params, "TODO 3")
    amplitude, centre, sigma = params
    return amplitude, centre, abs(sigma)


# ---------------------------------------------------------------------------
def main():
    snippets, rises, blocked, rate, pre = load_recording()
    # Times in s. Sample `pre` is the first at or above the threshold, so the
    # signal actually crossed it somewhere in the sample before: on average
    # half a sample earlier. That moment is t = 0.
    t = (np.arange(snippets.shape[1]) - pre + 0.5) / rate
    t_mid = t[:-1] + 0.5 / rate                       # times between samples, for np.diff

    # --- 1. The edge -------------------------------------------------------
    # TODO 1: Replace the Nones with the mean of the snippets (one value per
    #         time point, so average over axis=0), and its slope in V/s:
    #         the difference between neighbouring samples (np.diff) times rate.
    mean = None
    slope = None
    require(mean, "TODO 1")
    require(slope, "TODO 1")

    # Provided: fit the slope near t = 0, starting from a guess of a peak
    # as high as the biggest slope, at t = 0, about 2 samples wide.
    near = np.abs(t_mid) <= max(EDGE_FIT_MS / 1000, 4 / rate)
    edge_fit = fit_gaussian(t_mid[near], slope[near], guess=[slope.max(), 0.0, 2 / rate])
    _, t_edge, sigma_edge = edge_fit

    # --- 2. The speed ------------------------------------------------------
    # TODO 4: Replace the Nones with the blade period T in seconds (the mean
    #         number of samples between successive rises, divided by rate),
    #         the rotation frequency f = 1 / (N_BLADES * T), and the blade
    #         speed at the beam v = 2π * BEAM_RADIUS_MM * f (mm/s).
    blade_period = None
    rot_freq = None
    speed_mm_s = None
    require(blade_period, "TODO 4")
    require(rot_freq, "TODO 4")
    require(speed_mm_s, "TODO 4")

    # --- 3. The width ------------------------------------------------------
    # TODO 5: Replace the Nones with the beam diameter in mm, 4 * v * sigma_edge,
    #         and the width of every blade pass in mm,
    #         v * (blocked / rate - 2 * t_edge).
    beam_mm = None
    widths_mm = None
    require(beam_mm, "TODO 5")
    require(widths_mm, "TODO 5")

    # Provided: each time blocked is a whole number of samples, so the widths
    # come in steps of one sample's worth of blade travel. One bin per step.
    step = speed_mm_s / rate
    bin_edges = np.arange(widths_mm.min() - step / 2, widths_mm.max() + step, step)
    counts, bin_edges = np.histogram(widths_mm, bins=bin_edges)
    bin_centres = (bin_edges[:-1] + bin_edges[1:]) / 2
    if len(counts) < 4:
        raise SystemExit(f"The widths fall into only {len(counts)} histogram bars, too few to fit "
                         f"a Gaussian. Record at a higher RATE in exercise 06.")

    # TODO 6: Replace None with a Gaussian fitted to the histogram (bin_centres,
    #         counts), using your fit_gaussian. A good guess: the tallest bar's
    #         height, the mean of widths_mm, and the standard deviation of widths_mm.
    hist_fit = None
    require(hist_fit, "TODO 6")
    _, w_mm, w_sigma = hist_fit

    print(f"Fan speed:     {rot_freq * 60:.0f} rpm (blade period {blade_period * 1e3:.2f} ms)")
    print(f"Edge:          centre {t_edge * 1e3:+.3f} ms from the threshold crossing, "
          f"σ {sigma_edge * 1e3:.3f} ms")
    print(f"Beam diameter: {beam_mm:.2f} mm (1/e²)")
    print(f"Blade width:   {w_mm:.2f} mm (σ {w_sigma:.2f} mm over {len(widths_mm)} blade passes)")

    t_ms = t * 1e3
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(9, 9))
    ax1.plot(t_ms, snippets[:200].T, color="tab:blue", lw=0.5, alpha=0.05)
    ax1.plot(t_ms, mean, color="k", lw=1.5, label="mean")
    ax1.axvline(t_edge * 1e3, color="tab:red", ls="--", label="fitted edge centre")
    ax1.set_xlabel("Time from threshold crossing (ms)")
    ax1.set_ylabel("Photodiode (V)")
    ax1.set_title("Blade arriving")
    ax1.legend(loc="upper left")

    ax2.plot(t_mid * 1e3, slope / 1e3, color="k", lw=1, label="slope of the mean")
    ax2.plot(t_mid * 1e3, gaussian(t_mid, *edge_fit) / 1e3, color="tab:red", ls="--",
             label=f"Gaussian: beam {beam_mm:.2f} mm")
    ax2.set_xlabel("Time from threshold crossing (ms)")
    ax2.set_ylabel("Slope (V/ms)")
    ax2.legend(loc="upper left")

    x = np.linspace(bin_edges[0], bin_edges[-1], 300)
    ax3.bar(bin_centres, counts, width=np.diff(bin_edges), color="tab:blue", alpha=0.5,
            label="blade passes")
    ax3.plot(x, gaussian(x, *hist_fit), color="tab:red", ls="--",
             label=f"Gaussian: {w_mm:.2f} ± {w_sigma:.2f} mm")
    ax3.set_xlabel("Blade width (mm)")
    ax3.set_ylabel("Blade passes")
    ax3.legend(loc="upper left")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
