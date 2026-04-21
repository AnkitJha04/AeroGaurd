from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from Aqi_Utils import WHO_PM25_24H_THRESHOLDS, load_and_clean_data


DATA_FILE = Path(__file__).with_name("Mumbai_Data_Upload_Safe.csv")
OUTPUT_DIR = Path(__file__).with_name("report_outputs")

CLASS_LABELS = [
    "Within WHO Guideline",
    "Above WHO Guideline",
    "High",
    "Very High",
    "Extremely High",
    "Severe",
]


def pm25_to_class(pm25: float) -> int:
    limits = WHO_PM25_24H_THRESHOLDS
    if pm25 <= limits[0]:
        return 0
    if pm25 <= limits[1]:
        return 1
    if pm25 <= limits[2]:
        return 2
    if pm25 <= limits[3]:
        return 3
    if pm25 <= limits[4]:
        return 4
    return 5


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    work = work.sort_values(["city", "timestamp"]).reset_index(drop=True)

    work["hour"] = work["timestamp"].dt.hour
    work["dayofweek"] = work["timestamp"].dt.dayofweek
    work["month"] = work["timestamp"].dt.month

    work["sin_hour"] = np.sin(2 * np.pi * work["hour"] / 24)
    work["cos_hour"] = np.cos(2 * np.pi * work["hour"] / 24)
    work["sin_dow"] = np.sin(2 * np.pi * work["dayofweek"] / 7)
    work["cos_dow"] = np.cos(2 * np.pi * work["dayofweek"] / 7)

    group = work.groupby("city", group_keys=False)
    for lag in [1, 3, 6, 12, 24]:
        work[f"lag_{lag}"] = group["pm25"].shift(lag)

    work["rolling_mean_6"] = group["pm25"].rolling(6).mean().reset_index(level=0, drop=True)
    work["rolling_mean_24"] = group["pm25"].rolling(24).mean().reset_index(level=0, drop=True)
    work["rolling_std_24"] = group["pm25"].rolling(24).std().reset_index(level=0, drop=True)

    if "wind_speed" not in work.columns and "windspeed" in work.columns:
        work["wind_speed"] = work["windspeed"]

    for col in ["pm10", "humidity", "temperature", "wind_speed"]:
        if col not in work.columns:
            work[col] = np.nan

    work["target_class"] = work["pm25"].map(pm25_to_class)

    feature_cols = [
        "hour",
        "dayofweek",
        "month",
        "sin_hour",
        "cos_hour",
        "sin_dow",
        "cos_dow",
        "lag_1",
        "lag_3",
        "lag_6",
        "lag_12",
        "lag_24",
        "rolling_mean_6",
        "rolling_mean_24",
        "rolling_std_24",
        "pm10",
        "humidity",
        "temperature",
        "wind_speed",
    ]

    dataset = work.dropna(subset=feature_cols + ["target_class"]).copy()
    return dataset[["timestamp", "city", *feature_cols, "target_class"]]


def evaluate_model(location: str | None) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_and_clean_data(str(DATA_FILE))
    if isinstance(df, str):
        raise RuntimeError(df)
    if df.empty:
        raise RuntimeError("Dataset is empty after loading and cleaning.")

    if location:
        if location not in set(df["city"].unique()):
            raise RuntimeError(f"Location '{location}' not found in dataset.")
        df = df[df["city"] == location].copy()

    model_df = build_features(df)
    if model_df.empty or len(model_df) < 200:
        raise RuntimeError("Not enough rows after feature engineering. Try full dataset or another location.")

    model_df = model_df.sort_values("timestamp").reset_index(drop=True)
    split_idx = int(len(model_df) * 0.8)
    train_df = model_df.iloc[:split_idx]
    test_df = model_df.iloc[split_idx:]

    feature_cols = [c for c in model_df.columns if c not in {"timestamp", "city", "target_class"}]
    X_train = train_df[feature_cols]
    y_train = train_df["target_class"]
    X_test = test_df[feature_cols]
    y_test = test_df["target_class"]

    try:
        model = HistGradientBoostingClassifier(max_depth=8, learning_rate=0.08, max_iter=350, random_state=42)
    except Exception:
        model = RandomForestClassifier(n_estimators=400, max_depth=16, random_state=42, n_jobs=-1)

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    cm = confusion_matrix(y_test, y_pred, labels=list(range(len(CLASS_LABELS))))
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(
        y_test,
        y_pred,
        labels=list(range(len(CLASS_LABELS))),
        target_names=CLASS_LABELS,
        zero_division=0,
    )

    cm_df = pd.DataFrame(cm, index=[f"Actual: {n}" for n in CLASS_LABELS], columns=[f"Pred: {n}" for n in CLASS_LABELS])
    cm_path = OUTPUT_DIR / "confusion_matrix.csv"
    cm_png_path = OUTPUT_DIR / "confusion_matrix_heatmap.png"
    cm_df.to_csv(cm_path)

    heatmap_saved = False
    heatmap_error = None
    try:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(12, 8))
        image = ax.imshow(cm, cmap="Blues")
        fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)

        ax.set_xticks(range(len(CLASS_LABELS)))
        ax.set_yticks(range(len(CLASS_LABELS)))
        ax.set_xticklabels(CLASS_LABELS, rotation=30, ha="right")
        ax.set_yticklabels(CLASS_LABELS)
        ax.set_xlabel("Predicted Label")
        ax.set_ylabel("Actual Label")
        ax.set_title("AeroGuard AQI Classification Confusion Matrix")

        # Annotate each matrix cell for screenshot-friendly readability.
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                value = cm[i, j]
                text_color = "white" if value > (cm.max() * 0.5) else "black"
                ax.text(j, i, str(value), ha="center", va="center", color=text_color, fontsize=9)

        plt.tight_layout()
        fig.savefig(cm_png_path, dpi=220)
        plt.close(fig)
        heatmap_saved = True
    except Exception as exc:
        heatmap_error = str(exc)

    print("=" * 90)
    print("AEROGUARD ML CLASSIFICATION EVALUATION")
    print("=" * 90)
    print(f"Rows used (after feature engineering): {len(model_df)}")
    print(f"Train rows: {len(train_df)}")
    print(f"Test rows:  {len(test_df)}")
    print(f"Location mode: {location if location else 'ALL LOCATIONS'}")
    print("-" * 90)
    print(f"Accuracy: {acc:.4f}")
    print("-" * 90)
    print("Confusion Matrix (rows=actual, cols=predicted)")
    print(cm_df.to_string())
    print("-" * 90)
    print("Classification Report")
    print(report)
    print("-" * 90)
    print(f"Saved confusion matrix CSV: {cm_path}")
    if heatmap_saved:
        print(f"Saved confusion matrix PNG: {cm_png_path}")
    else:
        print("Could not save confusion matrix PNG. Install matplotlib and run again.")
        if heatmap_error:
            print(f"Heatmap export detail: {heatmap_error}")
    print("=" * 90)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Print terminal ML evaluation with confusion matrix.")
    parser.add_argument(
        "--location",
        default=None,
        help="Optional location/city (e.g., Colaba). If omitted, uses all locations.",
    )
    args = parser.parse_args()
    evaluate_model(args.location)
