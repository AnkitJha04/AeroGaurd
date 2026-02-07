"""Smart-city response recommendations based on AQI forecasts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pandas as pd

ALT_ROUTES = ["Coastal Road", "Eastern Freeway", "Northern Bypass", "Riverfront Link"]
RUSH_HOURS = {8, 9, 10, 17, 18, 19, 20}


@dataclass
class SmartAction:
    title: str
    message: str
    severity: str  # streamlit severity levels: success, info, warning, error


def _prepare_forecast(forecast_df: Optional[pd.DataFrame]) -> pd.DataFrame:
    if forecast_df is None or forecast_df.empty:
        return pd.DataFrame()
    clean_df = forecast_df.copy()
    clean_df['timestamp'] = pd.to_datetime(clean_df['timestamp'], errors='coerce', format='mixed')
    numeric_cols = ['pm25', 'pm10', 'wind_speed']
    for col in numeric_cols:
        if col in clean_df.columns:
            clean_df[col] = pd.to_numeric(clean_df[col], errors='coerce')
    clean_df = clean_df.dropna(subset=['timestamp'])
    return clean_df.sort_values('timestamp')


def _traffic_load_balancer(location: str, forecast_df: pd.DataFrame) -> Optional[SmartAction]:
    if forecast_df.empty or 'pm25' not in forecast_df.columns:
        return None
    rush_forecast = forecast_df[forecast_df['timestamp'].dt.hour.isin(RUSH_HOURS)]
    high_pollution = rush_forecast[rush_forecast['pm25'] > 150]
    if high_pollution.empty:
        return None
    alert_row = high_pollution.loc[high_pollution['pm25'].idxmax()]
    alt_route = ALT_ROUTES[int(alert_row['timestamp'].hour) % len(ALT_ROUTES)]
    pm_value = float(alert_row['pm25'])
    stamp = alert_row['timestamp'].strftime('%I:%M %p')
    message = (
        f"PM2.5 projected at {pm_value:.0f} µg/m³ around {stamp} in {location}. "
        f"Divert heavy vehicles via {alt_route} to protect commuters."
    )
    return SmartAction(
        title="Traffic Load Balancer",
        message=message,
        severity='error'
    )


def _smart_construction_compliance(history_df: pd.DataFrame) -> Optional[SmartAction]:
    if history_df is None or history_df.empty:
        return None
    if 'wind_speed' not in history_df.columns or 'pm10' not in history_df.columns:
        return None
    latest = history_df.dropna(subset=['wind_speed', 'pm10']).iloc[-1:]
    if latest.empty:
        return None
    wind_speed = float(latest['wind_speed'].iloc[0])
    pm10 = float(latest['pm10'].iloc[0])
    if wind_speed > 15 and pm10 > 200:
        return SmartAction(
            title="Smart Construction Compliance",
            message=(
                f"Wind speed {wind_speed:.1f} km/h with PM10 {pm10:.0f} µg/m³. "
                "Dust plumes heading toward residential zones — pause construction immediately."
            ),
            severity='error'
        )
    return None


def _predictive_mist_cannons(history_df: pd.DataFrame, forecast_df: pd.DataFrame) -> Optional[SmartAction]:
    if forecast_df.empty:
        return None
    current_pm10 = None
    if 'pm10' in history_df.columns and not history_df['pm10'].dropna().empty:
        current_pm10 = float(history_df['pm10'].dropna().iloc[-1])
    elif 'pm25' in history_df.columns and not history_df['pm25'].dropna().empty:
        current_pm25 = float(history_df['pm25'].dropna().iloc[-1])
        current_pm10 = current_pm25 * 1.5
    if current_pm10 is None or current_pm10 == 0:
        return None
    upcoming = forecast_df.head(2)
    if upcoming.empty:
        return None
    if 'pm10' in upcoming.columns and not upcoming['pm10'].dropna().empty:
        target_row = upcoming.loc[upcoming['pm10'].idxmax()]
        future_pm10 = float(target_row['pm10'])
    else:
        target_row = upcoming.loc[upcoming['pm25'].idxmax()]
        future_pm10 = float(target_row['pm25'] * 1.5)
    if future_pm10 > current_pm10 * 1.2:
        stamp = target_row['timestamp'].strftime('%I:%M %p')
        return SmartAction(
            title="Predictive Mist Cannons",
            message=(
                f"PM10 expected to rise from {current_pm10:.0f} to {future_pm10:.0f} µg/m³ by {stamp}. "
                "Activate mist cannons for pre-emptive suppression."
            ),
            severity='warning'
        )
    return None


def _green_corridor_routing(forecast_df: pd.DataFrame) -> Optional[SmartAction]:
    if forecast_df.empty or 'pm25' not in forecast_df.columns:
        return None
    horizon = forecast_df.head(6)
    if horizon.empty:
        return None
    max_row = horizon.loc[horizon['pm25'].idxmax()]
    max_pm25 = float(max_row['pm25'])
    max_time = max_row['timestamp'].strftime('%I:%M %p')
    min_row = horizon.loc[horizon['pm25'].idxmin()]
    min_pm25 = float(min_row['pm25'])
    min_time = min_row['timestamp'].strftime('%I:%M %p')
    if max_pm25 > 200:
        return SmartAction(
            title="Green Corridor Routing",
            message=(
                f"⚠️ AQI projected near {max_pm25:.0f} at {max_time}. "
                "Cyclists/Pedestrians: Avoid main roads; use Green Corridor A."
            ),
            severity='warning'
        )
    if min_pm25 < 100:
        return SmartAction(
            title="Green Corridor Routing",
            message=(
                f"✅ AQI expected around {min_pm25:.0f} at {min_time}. "
                "Outdoor activities safe along green corridors."
            ),
            severity='success'
        )
    return None


def _hvac_automation(forecast_df: pd.DataFrame, history_df: pd.DataFrame) -> Optional[SmartAction]:
    if forecast_df.empty and history_df.empty:
        return None
    target_row = None
    if not forecast_df.empty and 'pm25' in forecast_df.columns:
        target_row = forecast_df.iloc[0]
        next_pm25 = float(target_row['pm25'])
    elif not history_df.empty and 'pm25' in history_df.columns:
        next_pm25 = float(history_df['pm25'].dropna().iloc[-1])
    else:
        return None
    stamp = target_row['timestamp'].strftime('%I:%M %p') if target_row is not None else "current interval"
    if next_pm25 > 100:
        return SmartAction(
            title="HVAC Automation",
            message=f"Predicted PM2.5 {next_pm25:.0f} µg/m³ by {stamp}. HVAC Mode: Recirculation Only (close intake).",
            severity='warning'
        )
    return SmartAction(
        title="HVAC Automation",
        message=f"PM2.5 holding near {next_pm25:.0f} µg/m³. HVAC Mode: Fresh Air Intake Open.",
        severity='success'
    )


def generate_actionable_responses(
    location: str,
    history_df: pd.DataFrame,
    forecast_df: Optional[pd.DataFrame]
) -> List[SmartAction]:
    """Builds a prioritized list of smart-city interventions."""
    history_df = history_df.copy() if history_df is not None else pd.DataFrame()
    forecast_df = _prepare_forecast(forecast_df)

    actions: List[SmartAction] = []

    builders = [
        lambda: _traffic_load_balancer(location, forecast_df),
        lambda: _smart_construction_compliance(history_df),
        lambda: _predictive_mist_cannons(history_df, forecast_df),
        lambda: _green_corridor_routing(forecast_df),
        lambda: _hvac_automation(forecast_df, history_df)
    ]

    for builder in builders:
        action = builder()
        if action:
            actions.append(action)

    return actions
