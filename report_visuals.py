from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import plotly.express as px

from Aqi_Utils import generate_ml_forecast, load_and_clean_data


DATA_FILE = Path(__file__).with_name("Mumbai_Data_Upload_Safe.csv")
OUTPUT_DIR = Path(__file__).with_name("report_outputs") / "visuals"


def create_visuals(location: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_and_clean_data(str(DATA_FILE))
    if isinstance(df, str):
        raise RuntimeError(df)

    if df.empty:
        raise RuntimeError("Dataset is empty after loading and cleaning.")

    location_list = sorted(df["city"].dropna().unique().tolist())
    selected_location = location if location in location_list else location_list[0]

    filtered_df = df[df["city"] == selected_location].sort_values("timestamp")
    forecast_df = generate_ml_forecast(filtered_df, periods=12)
    latest_all = df.groupby("city").last().reset_index()

    latest_bar = latest_all.sort_values("pm25", ascending=False).head(15)
    fig_latest = px.bar(
        latest_bar,
        x="city",
        y="pm25",
        color="pm25",
        title="Top 15 Locations by Latest PM2.5",
        template="plotly_dark",
    )
    fig_latest.update_layout(xaxis_title="Location", yaxis_title="PM2.5 (ug/m3)")
    latest_path = OUTPUT_DIR / "latest_pm25_top15.html"
    fig_latest.write_html(str(latest_path), include_plotlyjs="cdn")

    trend_fig = px.area(
        filtered_df.tail(72),
        x="timestamp",
        y="pm25",
        title=f"72-Hour PM2.5 Trend - {selected_location}",
        template="plotly_dark",
    )
    trend_fig.update_layout(xaxis_title="Timestamp", yaxis_title="PM2.5 (ug/m3)")
    trend_path = OUTPUT_DIR / f"trend_72h_{selected_location.replace(' ', '_')}.html"
    trend_fig.write_html(str(trend_path), include_plotlyjs="cdn")

    if not forecast_df.empty:
        combined = pd.concat([filtered_df.tail(36), forecast_df], ignore_index=True)
        forecast_fig = px.line(
            combined,
            x="timestamp",
            y="pm25",
            color="type",
            title=f"Historical + 12-Hour Forecast - {selected_location}",
            template="plotly_dark",
            markers=True,
            color_discrete_map={"Historical": "gray", "Forecast": "#00CC96"},
        )
        forecast_fig.update_layout(xaxis_title="Timestamp", yaxis_title="PM2.5 (ug/m3)")
        forecast_path = OUTPUT_DIR / f"forecast_{selected_location.replace(' ', '_')}.html"
        forecast_fig.write_html(str(forecast_path), include_plotlyjs="cdn")
    else:
        forecast_path = None

    map_fig = px.scatter_mapbox(
        latest_all,
        lat="lat",
        lon="lon",
        color="pm25",
        size="pm25",
        hover_name="city",
        zoom=8,
        center={"lat": float(latest_all["lat"].mean()), "lon": float(latest_all["lon"].mean())},
        mapbox_style="open-street-map",
        title="Regional PM2.5 Snapshot Map",
    )
    map_path = OUTPUT_DIR / "regional_pm25_map.html"
    map_fig.write_html(str(map_path), include_plotlyjs="cdn")

    print("Visual assets generated:")
    print(f"- {latest_path}")
    print(f"- {trend_path}")
    if forecast_path:
        print(f"- {forecast_path}")
    print(f"- {map_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate AeroGuard visual assets for screenshots.")
    parser.add_argument("--location", default="Colaba", help="Location to build trend + forecast visuals")
    args = parser.parse_args()
    create_visuals(args.location)
