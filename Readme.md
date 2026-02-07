# AeroGuard: Hyper-Local Air Quality & Health Risk Forecaster

![Python](https://img.shields.io/badge/Python-3.9%2B-blue) ![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red) ![Status](https://img.shields.io/badge/Status-Hackathon%20Ready-success) ![License](https://img.shields.io/badge/License-MIT-green)

## Project Overview

AeroGuard is an end-to-end artificial intelligence system designed to address a critical gap in environmental monitoring: the lack of actionable, personalized, and hyper-local air quality data. While traditional systems report city-wide averages, AeroGuard leverages machine learning and spatial interpolation to forecast pollution levels at a granular scale. Beyond mere prediction, the system serves as a health intelligence platform, translating complex atmospheric data into specific, persona-based recommendations for vulnerable demographics.


## Table of Contents

1.  [Problem Statement](#problem-statement)
2.  [Solution Architecture](#solution-architecture)
3.  [Key Technical Innovations](#key-technical-innovations)
4.  [Technology Stack](#technology-stack)
5.  [Installation and Setup](#installation-and-setup)
6.  [Usage Guide](#usage-guide)
7.  [Project Structure](#project-structure)
8.  [Future Roadmap](#future-roadmap)


## Problem Statement

Current air quality monitoring infrastructure faces three fundamental limitations:

* **Spatial Granularity:** Most systems report a single Air Quality Index (AQI) for an entire city, failing to capture significant variations between industrial zones, traffic junctions, and residential parks.
* **Predictive Capability:** Users typically receive data about current conditions rather than near-term forecasts, making proactive planning difficult.
* **Contextual Relevance:** Health alerts are often generic, ignoring the fact that pollution levels safe for a healthy adult may be hazardous for children, the elderly, or asthmatics.

AeroGuard was developed to solve these issues by providing a predictive, hyper-local, and personalized monitoring experience.


## Solution Architecture

The system operates on a five-layer architecture designed to transform raw sensor data into human-readable insights.

### 1. Temporal Prediction Engine
Rather than relying on static rules, this engine utilizes historical time-series data (last 24 hours) to forecast PM2.5 concentrations for the next 12 hours. It employs Gradient Boosting (XGBoost) to model complex non-linear relationships between traffic patterns, weather conditions, and pollution levels.

### 2. Hyper-Local Spatial Intelligence
To address the scarcity of physical sensors, the system implements **Kriging (Gaussian Process Regression)**. This advanced geostatistical technique estimates pollution levels in unmonitored locations by interpolating data from known points, allowing for the generation of a continuous city-wide pollution heatmap.

### 3. Health Risk Classification Layer
This logic layer acts as an interpreter, converting numerical forecasts into risk categories. It supports three distinct user personas—General Public, Children/Elderly, and Outdoor Workers—dynamically adjusting risk thresholds and recommendations based on the selected demographic.

### 4. Explainability Module
Trust is built through transparency. The system includes an explainability layer that analyzes feature importance to generate natural language explanations. It informs the user *why* a forecast is high (e.g., "Elevated risk driven by low wind speed preventing pollutant dispersion"), ensuring the data is not just accurate but also understandable.

### 5. Interactive User Interface
The frontend is built with Streamlit to ensure responsiveness across mobile and desktop devices. It provides a clean, professional dashboard for users to visualize forecasts, explore heatmaps, and receive health advice.


## Key Technical Innovations

* **Persona-Adaptive Risk Scoring:** Unlike standard applications that use a universal threshold, AeroGuard's risk logic adapts to the biological vulnerability of the user.
* **Spatial Extrapolation:** The implementation of Kriging allows the system to provide intelligence for areas without direct sensor coverage, a significant improvement over nearest-neighbor approaches.
* **Automated Reasoning:** The system bridges the gap between data science and public communication by automatically generating the "reasoning" behind every forecast.


## Technology Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend Logic** | Python 3.9+ | Core application logic and data processing. |
| **Data Manipulation** | Pandas, NumPy | Handling time-series data and numerical operations. |
| **Machine Learning** | Scikit-Learn, XGBoost | Gradient boosting for regression and forecasting. |
| **Spatial Analysis** | GaussianProcessRegressor | Inverse Distance Weighing for spatial interpolation. |
| **Visualization** | Plotly, Folium | Interactive charting and geospatial mapping. |
| **Frontend Framework** | Streamlit | Rapid deployment of the interactive dashboard. |


## Installation and Setup
Follow these steps to deploy the application locally.
### Prerequisites
Ensure that Python 3.8 or higher is installed on your system.

### Step 1: Clone the Repository
```bash
git clone [https://github.com/AIColegion-VESIT/team-62-genesis-.git]
cd aeroguard

Step 2: Install Dependencies
Install the required Python packages using the provided requirements file or the command below.
```Bash
pip install streamlit pandas numpy scikit-learn xgboost plotly folium streamlit-folium

Step 3: Launch the Application
Execute the following command in your terminal to start the local server.
```Bash
python -m streamlit run Main.py


Usage Guide
1. Context Selection: Upon launching the app, use the sidebar to select your current Location and User Persona. This configures the backend models to your specific context.
2. Review Forecast: The main dashboard displays a 12-hour predictive chart. Use this to identify safe windows for outdoor activities.
3. Analyze Risk: Consult the "Health Advisory" section for specific, actionable guidance tailored to the selected persona.
4. Explore Spatial Data: Scroll to the "Hyper-Local Heatmap" to visualize how pollution is distributed across the surrounding area, helping to identify cleaner routes or zones.

Project Structure
AQIMONITOR/
├── Main.py                 # Main entry point containing UI and logic
├── Requirements.txt       # List of project dependencies
├── README.md              # Project documentation
└── Resource Files/                  # Directory for storing dataset files
    ── Augmented_Data.csv
    ── Bejing_Data(2013).csv
    ── Indian_Data(2015-2020).csv
    ── Merged_Data.csv
└── Data Augumentation/     # Directory for storing synthetic data generator files
    ├── Data_Synthesizer.py    # Utility script for synthetic data generation
    ├── Merger.py              # Utility script for merger of multiple datasets

Future Roadmap
The current version of AeroGuard represents a robust prototype. Future development phases will focus on:
1. IoT Integration: Interfacing directly with networked ESP32/Arduino particulate matter sensors for real-time data ingestion.
2. Computer Vision Analysis: Implementing Convolutional Neural Networks (CNNs) to estimate visibility and AQI from sky-facing camera feeds.
3. Push Notification System: Enabling proactive alerts sent via SMS or email when air quality is predicted to deteriorate significantly.
4. Hardware Connectivity with over the air transmission for accurate real time analysis anlong with prediction