import pandas as pd
import numpy as np
import os

def merge_datasets():
    print("🔄 Initializing Universal Data Merger...")
    
    # 1. COORDINATE DICTIONARY (Maps city names to Lat/Lon)
    city_coords = {
        # Beijing Stations
        "Aotizhongxin": [39.9824, 116.4063],
        "Changping": [40.2183, 116.2255],
        "Dingling": [40.2917, 116.2203],
        "Dongsi": [39.9292, 116.4172],
        "Guanyuan": [39.9293, 116.3506],
        "Gucheng": [39.9138, 116.1844],
        "Huairou": [40.3283, 116.6269],
        "Nongzhanguan": [39.9333, 116.4667],
        "Shunyi": [40.1264, 116.6552],
        "Tiantan": [39.8863, 116.4072],
        "Wanliu": [39.9873, 116.2886],
        "Wanshouxigong": [39.8782, 116.3520],
        
        # India Cities
        "Ahmedabad": [23.0225, 72.5714],
        "Delhi": [28.7041, 77.1025],
        "Bengaluru": [12.9716, 77.5946],
        "Mumbai": [19.0760, 72.8777],
        "Chennai": [13.0827, 80.2707],
        "Hyderabad": [17.3850, 78.4867],
        "Kolkata": [22.5726, 88.3639]
    }

    combined_frames = []

    # --- PROCESS FILE 1: SIMULATED GLOBAL DATA ---
    if os.path.exists("C:\\Users\\ankit\\OneDrive\\Documents\\Personal\\Repls\\Complete code\\Random Python\\AqiMonitor\\Resource Files\\Augmented_Data.csv"):
        print("   Reading 'Augmented_Data.csv'...")
        df_global = pd.read_csv("C:\\Users\\ankit\\OneDrive\\Documents\\Personal\\Repls\\Complete code\\Random Python\\AqiMonitor\\Resource Files\\Augmented_Data.csv")
        if 'lat' in df_global.columns:
            combined_frames.append(df_global)
            print(f"   ✅ Added {len(df_global)} global rows.")
    else:
        print("   ⚠️ 'Global_Air_Quality.csv' not found (Skipping).")

    # --- PROCESS FILE 2: BEIJING DATA ---
    if os.path.exists("C:\\Users\\ankit\\OneDrive\\Documents\\Personal\\Repls\\Complete code\\Random Python\\AqiMonitor\\Resource Files\\Bejing_Data(2013).csv"):
        print("   Reading 'Bejing_Data(2013).csv' (Beijing)...")
        df_bj = pd.read_csv("C:\\Users\\ankit\\OneDrive\\Documents\\Personal\\Repls\\Complete code\\Random Python\\AqiMonitor\\Resource Files\\Bejing_Data(2013).csv") 
        
        # Add Lat/Lon
        print("   📍 Mapping Coordinates for Beijing...")
        df_bj['lat'] = df_bj['location'].map(lambda x: city_coords.get(x, [None, None])[0])
        df_bj['lon'] = df_bj['location'].map(lambda x: city_coords.get(x, [None, None])[1])
        
        # Drop rows where we couldn't find coords
        df_bj = df_bj.dropna(subset=['lat', 'lon'])
        
        # Standardize columns (add missing physics columns if needed)
        for col in ['traffic', 'wind', 'humidity']:
            if col not in df_bj.columns:
                df_bj[col] = 0.5 

        combined_frames.append(df_bj)
        print(f"   ✅ Added {len(df_bj)} Beijing rows.")
    else:
        print("   ⚠️ 'Bejing_Data(2013).csv' not found (Skipping).")

    # --- PROCESS FILE 3: INDIA DATA ---
    if os.path.exists("C:\\Users\\ankit\\OneDrive\\Documents\\Personal\\Repls\\Complete code\\Random Python\\AqiMonitor\\Resource Files\\Indian_Data(2015-2020).csv"):
        print("   Reading 'Indian_Data(2015-2020).csv'...") 
        df_in = pd.read_csv("C:\\Users\\ankit\\OneDrive\\Documents\\Personal\\Repls\\Complete code\\Random Python\\AqiMonitor\\Resource Files\\Indian_Data(2015-2020).csv")
        
        # Add Lat/Lon
        print("   📍 Mapping Coordinates for India...")
        df_in['lat'] = df_in['location'].map(lambda x: city_coords.get(x, [None, None])[0])
        df_in['lon'] = df_in['location'].map(lambda x: city_coords.get(x, [None, None])[1])
        
        df_in = df_in.dropna(subset=['lat', 'lon'])
        combined_frames.append(df_in)
        print(f"   ✅ Added {len(df_in)} India rows.")
    else:
        print("   ⚠️ 'Indian_Data(2015-2020).csv' not found (Skipping).")

    # --- MERGE & FIX ---
    if not combined_frames:
        print("❌ No data found to merge. Please ensure CSV files are in the folder.")
        return

    print("   Concatenating master file...")
    master_df = pd.concat(combined_frames, ignore_index=True)
    
    print("   Converting timestamps (Handling mixed formats)...")
    # --- THE FIX IS HERE: Use format='mixed' and errors='coerce' ---
    master_df['timestamp'] = pd.to_datetime(master_df['timestamp'], format='mixed', errors='coerce')
    
    # Drop rows where timestamp conversion failed (NaT)
    original_len = len(master_df)
    master_df = master_df.dropna(subset=['timestamp'])
    dropped = original_len - len(master_df)
    if dropped > 0:
        print(f"   ⚠️ Dropped {dropped} rows with invalid dates.")
    
    print("   Sorting data...")
    master_df = master_df.sort_values(by='timestamp')
    
    # Select only necessary columns
    cols = ['timestamp', 'location', 'lat', 'lon', 'pm25', 'temp', 'humidity', 'wind', 'traffic']
    final_cols = [c for c in cols if c in master_df.columns]
    master_df = master_df[final_cols]
    
    # Save
    master_df.to_csv("C:\\Users\\ankit\\OneDrive\\Documents\\Personal\\Repls\\Complete code\\Random Python\\AqiMonitor\\Resource Files\\Merged_Data.csv", index=False)
    print(f"🎉 Success! 'Merged_Data.csv' created with {len(master_df)} rows.")
    print("   You can now run 'streamlit run app.py'")

if __name__ == "__main__":
    merge_datasets()