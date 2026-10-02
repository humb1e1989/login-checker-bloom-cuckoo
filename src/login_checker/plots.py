"""Create report figures from the benchmark and accuracy CSV files."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # render to files; no display needed
import matplotlib.pyplot as plt  # noqa: E402

# Categorical slots 1-5 of the validated palette, plus a marker AND a
# linestyle per structure, so identity never depends on color alone --
# including when two structures' curves fall on top of each other (e.g.
# linear_search and binary_search have nearly identical memory per
# login; without a linestyle difference one line fully hides the other).
STYLE = {
    "linear_search": ("#2a78d6", "o", "-", "Linear search"),
    "binary_search": ("#eb6834", "s", "--", "Binary search"),
    "hash_table": ("#1baf7a", "^", "-.", "Hash table"),
    "bloom_filter": ("#eda100", "D", ":", "Bloom filter"),
    "cuckoo_filter": ("#e87ba4", "v", (0, (3, 1, 1, 1)), "Cuckoo filter"),
}
INK = "#0b0b0b"
MUTED = "#52514e"


def read_rows(paths: list[Path]) -> list[dict[str, str]]:
    """Load and concatenate the rows of every CSV file that exists.

    Input: list of CSV paths. Output: list of row dictionaries (strings).
    """
    rows: list[dict[str, str]] = []
    for path in paths:
        if path.exists():
            with path.open(newline="", encoding="utf-8") as csv_file:
                rows.extend(csv.DictReader(csv_file))
    return rows


def series(rows: list[dict[str, str]], name: str, metric: str, scale: float = 1.0):
    """Extract one structure's (n, metric) points, sorted by n.

    Input: parsed CSV rows, the structure name to filter on, the metric
    column to read, and an optional divisor (e.g. 1e9 for ns -> s).
    Output: (sizes, values), two parallel lists ready to plot.
    """
    points = sorted(
        (int(r["n"]), float(r[metric]) / scale) for r in rows if r["structure"] == name
    )
    return [p[0] for p in points], [p[1] for p in points]


def style_axes(ax, xlabel: str, ylabel: str, title: str) -> None:
    """Apply the shared recessive-grid style to a subplot.

    Input: a matplotlib Axes and its axis/title text. Output: none;
    mutates ax in place (labels, muted grid, hidden top/right spines).
    """
    ax.set_xlabel(xlabel, color=MUTED)
    ax.set_ylabel(ylabel, color=MUTED)
    ax.set_title(title, color=INK, fontsize=10, loc="left")
    ax.grid(True, which="major", color="#e4e4e0", linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=8)


def line_chart(ax, rows, metric: str, scale: float, ylabel: str, title: str) -> None:
    """Draw one log-log line per structure for the given metric.

    Input: a matplotlib Axes, parsed CSV rows, the metric/scale/labels to
    plot. Output: none; draws one styled line per structure present in
    rows onto ax (structures missing from rows are simply skipped).
    """
    for name, (color, marker, linestyle, label) in STYLE.items():
        xs, ys = series(rows, name, metric, scale)
        if xs:
            ax.plot(xs, ys, color=color, marker=marker, linestyle=linestyle,
                    markersize=5, linewidth=1.6,
                    markeredgecolor="#fcfcfb", markeredgewidth=0.8, label=label)
    ax.set_xscale("log")
    ax.set_yscale("log")
    style_axes(ax, "Number of stored logins n", ylabel, title)


def save(fig, path: Path) -> None:
    """Save a figure as PNG at report resolution and close it.

    Input: a matplotlib Figure and the output path. Output: none; writes
    path and frees the figure's memory (closes it) afterward.
    """
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    print(f"wrote {path}")


def plot_query_time(rows, out: Path) -> None:
    """Plot mean query time vs n, with hit-only and miss-only panels.

    Input: parsed benchmark CSV rows, the output directory. Output: none;
    writes out/query_time.png (three side-by-side log-log panels).
    """
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4), sharey=True)
    for ax, metric, title in zip(
        axes,
        ("query_mean_ns", "hit_mean_ns", "miss_mean_ns"),
        ("Mixed 50% hit / 50% miss", "Successful lookups (hits)", "Unsuccessful lookups (misses)"),
    ):
        line_chart(ax, rows, metric, 1.0, "Mean time per query (ns)" if metric == "query_mean_ns" else "", title)
    axes[0].legend(fontsize=7, frameon=False, loc="upper left")
    save(fig, out / "query_time.png")


def plot_build_time(rows, out: Path) -> None:
    """Plot total build time vs n.

    Input: parsed benchmark CSV rows, the output directory. Output: none;
    writes out/build_time.png (one log-log panel).
    """
    fig, ax = plt.subplots(figsize=(5, 3.4))
    line_chart(ax, rows, "build_ns", 1e9, "Build time (s)", "Build time")
    ax.legend(fontsize=7, frameon=False)
    save(fig, out / "build_time.png")


def plot_memory(rows, out: Path) -> None:
    """Plot bytes per stored login vs n (structure plus retained strings).

    Input: parsed benchmark CSV rows, the output directory. Output: none;
    writes out/memory.png. Exact structures' totals add back the
    retained-string bytes that tracemalloc attributes to `values`, not to
    the structure itself (see benchmark.measure_memory).
    """
    fig, ax = plt.subplots(figsize=(5, 3.4))
    for name, (color, marker, linestyle, label) in STYLE.items():
        pts = sorted(
            (int(r["n"]), (float(r["memory_bytes"]) + float(r["string_payload_bytes"])) / int(r["n"]))
            for r in rows if r["structure"] == name and float(r["memory_bytes"]) > 0
        )
        if pts:
            ax.plot(*zip(*pts), color=color, marker=marker, linestyle=linestyle,
                    markersize=5, linewidth=1.6,
                    markeredgecolor="#fcfcfb", markeredgewidth=0.8, label=label)
    ax.set_xscale("log")
    ax.set_yscale("log")
    style_axes(ax, "Number of stored logins n", "Bytes per login", "Memory per stored login")
    ax.legend(fontsize=7, frameon=False)
    save(fig, out / "memory.png")


def plot_false_positives(acc_rows, out: Path) -> None:
    """Plot measured vs predicted false-positive rate against bits per item.

    Input: parsed accuracy.py CSV rows, the output directory. Output:
    none; writes out/false_positives.png, one measured + one dashed
    theoretical line per filter.
    """
    fig, ax = plt.subplots(figsize=(5, 3.4))
    for name, key in (("bloom_filter", "bloom_filter"), ("cuckoo_filter", "cuckoo_filter")):
        color, marker, linestyle, label = STYLE[key]
        pts = [r for r in acc_rows if r["experiment"] == "fp_sweep" and r["structure"] == name]
        xs = [float(r["bits_per_item"]) for r in pts]
        ax.plot(xs, [float(r["measured_fp"]) for r in pts], color=color, marker=marker,
                linestyle=linestyle, markersize=5, linewidth=1.6,
                markeredgecolor="#fcfcfb", label=f"{label} (measured)")
        ax.plot(xs, [float(r["theory_fp"]) for r in pts], color=color, linestyle="--",
                linewidth=1.0, label=f"{label} (theory)")
    ax.set_yscale("log")
    style_axes(ax, "Bits per stored login", "False-positive rate", "Accuracy vs space")
    ax.legend(fontsize=7, frameon=False)
    save(fig, out / "false_positives.png")


def main() -> None:
    """Read the CSV files and write every figure.

    Input: command-line flag --results (directory holding the CSVs and
    where the PNGs are written; default "results"). Output: none; skips
    a figure if its CSV inputs are not found rather than erroring.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path("results"))
    args = parser.parse_args()
    rows = read_rows([args.results / "benchmark.csv", args.results / "benchmark_large.csv"])
    if rows:
        plot_query_time(rows, args.results)
        plot_build_time(rows, args.results)
        plot_memory(rows, args.results)
    acc_rows = read_rows([args.results / "accuracy.csv"])
    if acc_rows:
        plot_false_positives(acc_rows, args.results)


if __name__ == "__main__":
    main()
