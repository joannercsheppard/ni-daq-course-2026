"""
Exercise 07: Fan experiment, measure the blade width              (about 30 min)
====================================================

Task
----
Turn the blade passes from exercise 06 into a blade width by fitting Gaussians.

The laser beam's brightness falls off as a Gaussian from its centre. As a
blade edge sweeps across it, the light reaching the photodiode changes
smoothly, and the SLOPE of that change is the Gaussian itself. Its peak is the
moment the edge crosses the centre of the beam:

    mean of the       ─────┐                  ┌─────
    snippets               └──────────────────┘

    slope of            ───╮╭────────────────╭╮───
    the mean               ╰╯                ╰╯
                       t_arrive   ◄── τ ──►  t_leave

  1. Mean and slope (TODO 1): average the snippets, then take the slope.
  2. Fit the edges (TODOs 2-3): fit a Gaussian to the slope at each edge.
     The two centres give the time τ that the blade takes to pass the beam,
     to a fraction of a sample.
  3. Width (TODOs 4-5): time becomes distance, as in a scanning microscope.
         blade period         T = mean time between threshold crossings
         rotation frequency   f = 1 / (N_BLADES * T)
         blade speed at beam  v = 2π * BEAM_RADIUS_MM * f
         blade width          w = v * τ
         beam diameter        d = 4 * v * σ   (σ of the arriving edge's Gaussian)

  Both centres are measured at the middle of the beam, so the beam's size
  cancels out of w. The fitted σ measures the beam itself: this is the
  "knife-edge" method used to measure laser spots on real microscopes.

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
* Prints the fan's speed, the edge times, the blade width and the beam
  diameter. With simulated data: width close to 15 mm, beam close to 1 mm.
* Plots the mean snippet with the blade shaded between the fitted edges, and
  the slope with the two fitted Gaussians on top of it.

Investigation questions
-----------------------
1. Measure a blade with a ruler and compare. Fan blades are angled (pitched):
   which width does the beam actually measure?
2. Record twice in exercise 06 with different values of THRESHOLD_V. Does the
   blade width change? Why not, when the threshold moves where each snippet
   starts?
3. Is the Gaussian at the leaving edge wider than at the arriving edge? Why?
   (Hint: your answer to question 1 in exercise 06.)
4. Each edge is only a few samples long, yet the fit places it to a fraction
   of a sample. Where does that extra precision come from?
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
EDGE_FIT_MS = 0.5         # fit each Gaussian to the slope within this time of the edge

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

    Returns (snippets, crossings, rate, pre).
    """
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        files = sorted(DATA_DIR.glob("*.npz"), key=lambda p: p.stat().st_mtime)
        if not files:
            raise SystemExit("No recordings found. Record one with exercises/06_fan_record.py first.")
        path = files[-1]
    f = np.load(path)
    snippets, rate, pre = f["snippets"], int(f["rate"]), int(f["pre"])
    print(f"File: {path.name} ({len(snippets)} blade passes, "
          f"{snippets.shape[1]} samples each at {rate} samples/s)")
    return snippets, f["crossings"], rate, pre


# ---------------------------------------------------------------------------
# Your analysis
# ---------------------------------------------------------------------------
def gaussian(t, amplitude, centre, sigma):
    """A Gaussian of height `amplitude`, centred on `centre`, with width `sigma`."""
    # TODO 2: Replace None with amplitude * exp(-(t - centre)² / (2 * sigma²)).
    #         Use np.exp, so that it works on a whole array of times t.
    return None


def fit_edge(t, slope, around):
    """Fit a Gaussian to `slope` within EDGE_FIT_MS of time `around`.

    Returns (amplitude, centre, sigma). Times are in seconds.
    """
    dt = t[1] - t[0]
    near = np.abs(t - around) <= max(EDGE_FIT_MS / 1000, 4 * dt)
    guess = [slope[near].max(), around, 2 * dt]
    require(gaussian(t[near], *guess), "TODO 2")

    # TODO 3: Replace None with the fitted parameters. curve_fit(model, x, y,
    #         p0=guess) fits model(x, *params) to y, starting from `guess`,
    #         and returns (params, covariance). Fit `gaussian` to t[near]
    #         and slope[near], and keep only params.
    params = None
    require(params, "TODO 3")
    return params


# ---------------------------------------------------------------------------
def main():
    snippets, crossings, rate, pre = load_recording()
    t = (np.arange(snippets.shape[1]) - pre) / rate   # s, 0 = threshold crossing
    t_mid = t[:-1] + 0.5 / rate                       # times between samples, for np.diff

    # TODO 1: Replace the Nones with the mean of the snippets (one value per
    #         time point, so average over axis=0), and its slope in V/s:
    #         the difference between neighbouring samples (np.diff) times rate.
    mean = None
    slope = None
    require(mean, "TODO 1")
    require(slope, "TODO 1")

    # TODO 4: Replace the Nones with the blade period T in seconds (the mean
    #         number of samples between successive crossings, divided by rate),
    #         the rotation frequency f = 1 / (N_BLADES * T), and the blade
    #         speed at the beam v = 2π * BEAM_RADIUS_MM * f (mm/s).
    blade_period = None
    rot_freq = None
    speed_mm_s = None
    require(blade_period, "TODO 4")
    require(rot_freq, "TODO 4")
    require(speed_mm_s, "TODO 4")

    # Provided: the arriving edge is at t = 0 and the slope there is negative,
    # so fit -slope. The leaving edge is the biggest rise within one blade
    # period after that.
    a_arrive, t_arrive, sigma_arrive = fit_edge(t_mid, -slope, around=0.0)
    after = (t_mid > EDGE_FIT_MS / 1000) & (t_mid < blade_period)
    if not after.any() or slope[after].max() < 0.5 * (-slope).max():
        raise SystemExit("No leaving edge in the snippets. Increase POST in exercise 06.")
    a_leave, t_leave, sigma_leave = fit_edge(t_mid, slope, around=t_mid[after][np.argmax(slope[after])])

    # TODO 5: Replace the Nones with the blade width in mm, v * (t_leave - t_arrive),
    #         and the beam diameter in mm, 4 * v * sigma_arrive.
    w_mm = None
    beam_mm = None
    require(w_mm, "TODO 5")
    require(beam_mm, "TODO 5")

    print(f"Fan speed:     {rot_freq * 60:.0f} rpm (blade period {blade_period * 1e3:.2f} ms)")
    print(f"Edges:         arrives {t_arrive * 1e3:.3f} ms, leaves {t_leave * 1e3:.3f} ms "
          f"(σ {abs(sigma_arrive) * 1e3:.3f} and {abs(sigma_leave) * 1e3:.3f} ms)")
    print(f"Blade width:   {w_mm:.2f} mm")
    print(f"Beam diameter: {abs(beam_mm):.2f} mm (1/e², from the arriving edge)")

    t_ms, mid_ms = t * 1e3, t_mid * 1e3
    show = (t > -1e-3) & (t < t_leave + 1e-3)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    ax1.plot(t_ms[show], snippets[:200, show].T, color="tab:blue", lw=0.5, alpha=0.05)
    ax1.plot(t_ms[show], mean[show], color="k", lw=1.5, label="mean")
    ax1.axvspan(t_arrive * 1e3, t_leave * 1e3, color="orange", alpha=0.2, label=f"blade: {w_mm:.2f} mm")
    ax1.set_ylabel("Photodiode (V)")
    ax1.legend(loc="lower right")
    ax1.set_title("Blade passes and their mean")

    show = show[:-1]
    ax2.plot(mid_ms[show], slope[show] / 1e3, color="k", lw=1, label="slope of the mean")
    for a, centre, sigma in [(-a_arrive, t_arrive, sigma_arrive), (a_leave, t_leave, sigma_leave)]:
        ax2.plot(mid_ms[show], gaussian(t_mid[show], a, centre, sigma) / 1e3,
                 color="tab:red", lw=1.5, ls="--")
    ax2.plot([], [], color="tab:red", ls="--", label="fitted Gaussians")
    ax2.set_xlabel("Time from threshold crossing (ms)")
    ax2.set_ylabel("Slope (V/ms)")
    ax2.legend(loc="lower right")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
