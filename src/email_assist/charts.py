from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from .constants import CATEGORIES


def write_category_probability_chart(
    emails: list[dict[str, Any]], path: Path
) -> None:
    probabilities = [
        [
            float(value)
            for email in emails
            if (value := email.get(f"final_{category}_probability")) is not None
        ]
        for category in CATEGORIES
    ]

    figure, axis = plt.subplots(figsize=(14, 7))
    if any(probabilities):
        boxes = axis.boxplot(
            probabilities,
            patch_artist=True,
            showfliers=True,
        )
        colors = plt.get_cmap("viridis")(
            [index / max(len(CATEGORIES) - 1, 1) for index in range(len(CATEGORIES))]
        )
        for box, color in zip(boxes["boxes"], colors):
            box.set_facecolor(color)
        axis.set_xticks(range(1, len(CATEGORIES) + 1), CATEGORIES)
        axis.set_ylim(0, 1)
        axis.set_ylabel("Probability")
        axis.set_xlabel("Email category")
        axis.grid(axis="y", linestyle="--", alpha=0.7)
        axis.tick_params(axis="x", labelrotation=45)
    else:
        axis.text(
            0.5,
            0.5,
            "No email probability data available.",
            horizontalalignment="center",
            verticalalignment="center",
            transform=axis.transAxes,
        )
        axis.set_axis_off()

    axis.set_title("Distribution of Category Probabilities per Email")
    figure.tight_layout()
    figure.savefig(path, format="png", dpi=150, bbox_inches="tight")
    plt.close(figure)
