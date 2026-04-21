from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from Aqi_Utils import (
    calculate_aqi_status,
    generate_ml_forecast,
    generate_text_explanation,
    get_persona_config,
    load_and_clean_data,
)
from solutions_engine import generate_actionable_responses


DATA_FILE = Path(__file__).with_name("Mumbai_Data_Upload_Safe.csv")
OUTPUT_DIR = Path(__file__).with_name("report_outputs")


def _format_actions(actions: list) -> str:
    if not actions:
        return "No immediate interventions required."
    lines = []
    for idx, action in enumerate(actions, start=1):
        lines.append(f"{idx}. [{action.severity.upper()}] {action.title}: {action.message}")
    return "\n".join(lines)


def build_report(location: str, persona: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_and_clean_data(str(DATA_FILE))
    if isinstance(df, str):
        raise RuntimeError(df)

    if df.empty:
        raise RuntimeError("Dataset is empty after loading and cleaning.")

    available_locations = sorted(df["city"].dropna().unique().tolist())
    selected_location = location if location in available_locations else available_locations[0]

    filtered_df = df[df["city"] == selected_location].sort_values("timestamp")
    latest = filtered_df.iloc[-1]

    pm25 = float(latest.get("pm25", 0.0))
    status, _ = calculate_aqi_status(pm25, persona)
    persona_config = get_persona_config(persona)

    forecast_df = generate_ml_forecast(filtered_df, periods=12)
    one_step_forecast = forecast_df.head(1) if not forecast_df.empty else pd.DataFrame()

    explanation = generate_text_explanation(
        pm25,
        filtered_df,
        one_step_forecast,
        latest.get("humidity", None),
        latest.get("temperature", None),
    )

    smart_actions = generate_actionable_responses(selected_location, filtered_df, forecast_df)

    summary = {
        "rows": int(len(df)),
        "cities": int(df["city"].nunique()),
        "start": str(df["timestamp"].min()),
        "end": str(df["timestamp"].max()),
    }

    print("=" * 80)
    print("AEROGUARD PROJECT REPORT OUTPUT")
    print("=" * 80)
    print(f"Dataset file: {DATA_FILE.name}")
    print(f"Rows: {summary['rows']}")
    print(f"Locations: {summary['cities']}")
    print(f"Time range: {summary['start']} -> {summary['end']}")
    print("-" * 80)
    print(f"Selected location: {selected_location}")
    print(f"Selected persona: {persona}")
    print(f"Current PM2.5: {pm25:.1f} ug/m3")
    print(f"Risk category: {status}")
    print(f"Health advice: {persona_config['advice_by_status'].get(status, '')}")
    print("-" * 80)
    print("AI EXPLANATION")
    print(explanation)
    print("-" * 80)
    print("SMART-CITY ACTIONS")
    print(_format_actions(smart_actions))

    if not forecast_df.empty:
        print("-" * 80)
        print("12-HOUR FORECAST (TOP 12)")
        display_cols = ["timestamp", "pm25", "pm10", "city", "type"]
        print(forecast_df[display_cols].to_string(index=False))

    forecast_path = OUTPUT_DIR / f"forecast_{selected_location.replace(' ', '_')}.csv"
    actions_path = OUTPUT_DIR / f"actions_{selected_location.replace(' ', '_')}.csv"
    md_path = OUTPUT_DIR / f"report_{selected_location.replace(' ', '_')}.md"

    if not forecast_df.empty:
        forecast_df.to_csv(forecast_path, index=False)

    if smart_actions:
        pd.DataFrame(
            [
                {"title": a.title, "severity": a.severity, "message": a.message}
                for a in smart_actions
            ]
        ).to_csv(actions_path, index=False)

    md_lines = [
        "# AeroGuard Project Report",
        "",
        "## Dataset Summary",
        f"- Rows: {summary['rows']}",
        f"- Locations: {summary['cities']}",
        f"- Time range: {summary['start']} -> {summary['end']}",
        "",
        "## Selected Context",
        f"- Location: {selected_location}",
        f"- Persona: {persona}",
        f"- Current PM2.5: {pm25:.1f} ug/m3",
        f"- Risk category: {status}",
        "",
        "## AI Explanation",
        explanation,
        "",
        "## Smart-City Actions",
        _format_actions(smart_actions),
    ]
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    print("-" * 80)
    print("FILES WRITTEN")
    print(f"Markdown report: {md_path}")
    if forecast_path.exists():
        print(f"Forecast CSV:    {forecast_path}")
    if actions_path.exists():
        print(f"Actions CSV:     {actions_path}")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate AeroGuard report outputs for screenshots.")
    parser.add_argument("--location", default="Colaba", help="City/location to analyze")
    parser.add_argument("--persona", default="Respiratory Patient", help="Persona for risk/advice")
    args = parser.parse_args()
    build_report(args.location, args.persona)
