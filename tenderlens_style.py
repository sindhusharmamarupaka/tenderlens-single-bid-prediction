"""TenderLens visual style — import in every notebook:  from tenderlens_style import *"""
import matplotlib as mpl
import matplotlib.pyplot as plt

# ---- Colour roles: Navy + Teal + Amber (validated for colour-blind safety) ----
SINGLE = "#e0a000"   # single-bid / pushes towards single-bid (chart amber; brand #ffb400 is too light for marks)
MULTI = "#0aa6a6"    # multi-bid / pushes away from single-bid (teal)
THIRD = "#05556b"    # benchmark / reference series / anomaly flag (deep blue-teal)
AMBER_BRAND = "#ffb400"  # app accents, badges, highlights - not chart marks
HILITE = "#ffdd7b"   # soft highlight bands only
NAVY = "#02151f"     # headers, dark UI
INK = "#02151f"      # primary text
INK2 = "#4a5a62"     # secondary text
GRID = "#e4eaec"     # grid lines
AXIS = "#b3bfc4"     # axis lines
NEUTRAL = "#b8c7cc"  # neutral / benchmark bars
SURFACE = "#f7fafc"  # background
APP_BG = "#fdf6e3"    # Streamlit app page background (warm gold tint) - LOCKED
APP_CARD = "#ffffff"  # app cards
APP_SIDEBAR = "#02151f"  # app sidebar (navy)
BLUES = ["#d3f0ef", "#94dcdb", "#4cc0c0", "#0aa6a6", "#05556b", "#02151f"]  # magnitude ramp (teal -> navy)

FONT = ["Inter", "Helvetica Neue", "Arial", "DejaVu Sans"]


def use_style():
    mpl.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "font.family": "sans-serif", "font.sans-serif": FONT, "font.size": 10.5,
        "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.titlepad": 22, "axes.labelsize": 10, "axes.labelcolor": INK2,
        "axes.edgecolor": AXIS, "axes.linewidth": 0.8,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.7, "axes.axisbelow": True,
        "xtick.color": INK2, "ytick.color": INK2, "xtick.labelsize": 9.5, "ytick.labelsize": 9.5,
        "legend.frameon": False, "legend.fontsize": 9.5,
        "lines.linewidth": 2, "figure.dpi": 110, "savefig.dpi": 160, "savefig.bbox": "tight",
    })


def title(ax, finding, subtitle=None):
    """Title = the finding; subtitle = what is measured."""
    ax.set_title(finding, color=INK)
    if subtitle:
        ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=9.5, color=INK2, va="bottom")


def source(fig, text="Source: Assam e-tenders via CivicDataLab"):
    fig.text(0.01, -0.02, text, fontsize=8.5, color=INK2, ha="left", va="top")


def save_fig(fig, path):
    fig.savefig(path)


use_style()
