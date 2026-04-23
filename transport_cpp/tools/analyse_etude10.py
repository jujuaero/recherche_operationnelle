import math
from pathlib import Path

import numpy as np
import pandas as pd


def classify_complexity_from_maxima(n_values, t_values):
    n = np.array(n_values, dtype=float)
    t = np.array(t_values, dtype=float)
    t = np.clip(t, 1e-12, None)

    candidates = {
        "O(log n)": np.log(np.clip(n, 2, None)),
        "O(n)": n,
        "O(n log n)": n * np.log(np.clip(n, 2, None)),
        "O(n^2)": n ** 2,
        "O(n^k)": None,
        "O(k^n)": None,
    }

    scores = {}

    # Linear fit on transformed features
    for name, x in candidates.items():
        if x is None:
            continue
        a, b = np.linalg.lstsq(np.vstack([np.ones_like(x), x]).T, t, rcond=None)[0]
        pred = a + b * x
        mse = float(np.mean((t - pred) ** 2))
        scores[name] = mse

    # Polynomial in log-log: t = c * n^k
    x = np.log(n)
    y = np.log(t)
    a, b = np.linalg.lstsq(np.vstack([np.ones_like(x), x]).T, y, rcond=None)[0]
    pred = np.exp(a + b * x)
    scores["O(n^k)"] = float(np.mean((t - pred) ** 2))

    # Exponential: t = c * k^n => log(t) = log(c) + n*log(k)
    x = n
    y = np.log(t)
    a, b = np.linalg.lstsq(np.vstack([np.ones_like(x), x]).T, y, rcond=None)[0]
    pred = np.exp(a + b * x)
    scores["O(k^n)"] = float(np.mean((t - pred) ** 2))

    best = min(scores.items(), key=lambda kv: kv[1])[0]
    return best, scores


def main():
    csv_path = Path("results/etude10/resultats_etude10_cpp.csv")
    if not csv_path.exists():
        raise FileNotFoundError("results/etude10/resultats_etude10_cpp.csv introuvable")

    df = pd.read_csv(csv_path)

    required = [
        "theta_NO_s",
        "theta_BH_s",
        "t_NO_s",
        "t_BH_s",
    ]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Colonne manquante: {col}")

    df["theta_plus_t_NO_s"] = df["theta_NO_s"] + df["t_NO_s"]
    df["theta_plus_t_BH_s"] = df["theta_BH_s"] + df["t_BH_s"]

    metrics = [
        "theta_NO_s",
        "theta_BH_s",
        "t_NO_s",
        "t_BH_s",
        "theta_plus_t_NO_s",
        "theta_plus_t_BH_s",
    ]

    # Maxima par n (enveloppe supérieure du nuage)
    max_df = df.groupby("n", as_index=False)[metrics].max().sort_values("n")
    out_dir = Path("results/etude10")
    out_dir.mkdir(exist_ok=True)
    max_df.to_csv(out_dir / "maxima_etude10_cpp.csv", index=False)

    lines = []
    lines.append("Complexite pire des cas (enveloppe superieure)\n")
    lines.append(f"Nombre de lignes mesurees: {len(df)}\n")

    for metric in metrics:
        n_vals = max_df["n"].to_numpy()
        t_vals = max_df[metric].to_numpy()
        best, scores = classify_complexity_from_maxima(n_vals, t_vals)
        lines.append(f"- {metric}: {best}")

    (out_dir / "classification_complexite.txt").write_text("\n".join(lines), encoding="utf-8")

    print("[OK] Export maxima:", out_dir / "maxima_etude10_cpp.csv")
    print("[OK] Export classification:", out_dir / "classification_complexite.txt")


if __name__ == "__main__":
    main()
