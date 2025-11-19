import streamlit as st
import pandas as pd
import datetime
import os
import ast
import numpy as np

# ==========================================
# 1. CONFIGURATION & STYLING
# ==========================================
st.set_page_config(page_title="25-26 Off-Season", page_icon="⚾", layout="wide")

st.markdown("""
<style>
    /* Global Font & Spacing */
    .stApp { font-family: 'Segoe UI', sans-serif; }
    
    /* Card Styling */
    .workout-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .dark-mode .workout-card {
        background-color: #262730;
        border: 1px solid #444;
    }
    
    /* Headers */
    h1, h2, h3 { font-weight: 700; letter-spacing: -0.5px; }
    
    /* Metrics */
    .metric-container {
        display: flex; 
        gap: 10px; 
        justify-content: center;
        background: #f9f9f9;
        padding: 10px;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA HANDLING
# ==========================================
FILES = {
    "schedule": "schedule_data.csv",
    "routines": "routines_library.csv",
    "logs": "workout_logs.csv", 
    "velo": "velo_data.csv"
}

SCHED_COLS = [
    "Date", "Lifting Plan", "Warm Up", "Yoga?", "Throwing Plan", 
    "Daily Constraint", "Intent", "Long Toss Distance", 
    "Mound Style", "Goal Velocity", "Command Implement"
]

def load_data(key):
    if not os.path.exists(FILES[key]):
        if key == "routines":
            return pd.DataFrame(columns=["Routine Name", "Type", "Exercises"])
        elif key == "schedule":
            dates = pd.date_range(start=f"{datetime.date.today().year}-01-01", end=f"{datetime.date.today().year}-12-31")
            df = pd.DataFrame({"Date": dates})
            df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
            for col in SCHED_COLS:
                if col != "Date": df[col] = ""
            return df
        elif key == "logs":
            return pd.DataFrame(columns=["Date", "Routine Name", "Exercise", "Set #", "Prescribed Weight", "Actual Weight", "Actual Reps"])
        elif key == "velo":
            return pd.DataFrame(columns=["Date", "Velo"])
        return pd.DataFrame()
    
    df = pd.read_csv(FILES[key])
    if key == "schedule":
        df = df.fillna("")
        df["Date"] = df["Date"].astype(str)
    return df

def save_data(key, df):
    df.to_csv(FILES[key], index=False)

def append_data(key, new_row_dict):
    df = load_data(key)
    new_df = pd.DataFrame([new_row_dict])
    updated_df = pd.concat([df, new_df], ignore_index=True)
    updated_df.to_csv(FILES[key], index=False)

# ==========================================
# 3. ROBUST PARSER (Fixing "Not Pulling Data")
# ==========================================
def parse_nippard_csv(file):
    df = pd.read_csv(file, header=None)
    
    extracted_routines = []
    current_week = "Week 1"
    current_routine_name = None
    current_exercises = []
    
    for index, row in df.iterrows():
        # Safe Get
        def get_col(idx):
            try:
                val = str(row[idx]).strip()
                return "" if val == "nan" else val
            except: return ""

        val_B = get_col(1) # Routine Name
        val_C = get_col(2) # Exercise Name
        
        # 1. Detect Week
        if "Week" in val_B and len(val_B) < 15:
            current_week = val_B
            continue

        # 2. Detect New Session
        # A session row usually has text in Col B, but NOT "Exercise" or "IMPORTANT"
        if val_B and "Week" not in val_B and "Exercise" not in val_B and "IMPORTANT" not in val_B and "Jeff" not in val_B:
            
            # Save previous
            if current_routine_name and current_exercises:
                extracted_routines.append({
                    "Routine Name": current_routine_name,
                    "Type": "Lifting",
                    "Exercises": str(current_exercises)
                })
            
            # Start New
            clean_name = val_B.split(":")[0].strip()
            current_routine_name = f"{current_week} - {clean_name}"
            current_exercises = []
            
            # Check if first exercise is on THIS row (Col C)
            if val_C and val_C != "Exercise":
                ex_obj = extract_exercise_row(row)
                current_exercises.append(ex_obj)
            continue

        # 3. Detect Exercise Rows
        if not val_B and val_C:
            if "Exercise" in val_C or "Warm-up" in val_C: continue
            ex_obj = extract_exercise_row(row)
            current_exercises.append(ex_obj)

    # Save final
    if current_routine_name and current_exercises:
        extracted_routines.append({
            "Routine Name": current_routine_name,
            "Type": "Lifting",
            "Exercises": str(current_exercises)
        })
        
    return extracted_routines

def extract_exercise_row(row):
    def get_col(idx):
        try:
            val = str(row[idx]).strip()
            return "" if val == "nan" else val
        except: return ""

    return {
        "Exercise": get_col(2),
        "Warmup Sets": get_col(3),
        "Working Sets": get_col(4),
        "Reps": get_col(5),
        "Load": get_col(6),
        "Percent": get_col(7),
        "RPE": get_col(8),
        "Rest": get_col(9),
        "Notes": get_col(10)
    }

# ==========================================
# 4. NAVIGATION
# ==========================================
st.sidebar.title("⚾ 25-26 Off-Season")
page = st.sidebar.radio("Menu", ["Today's Plan", "Monthly Schedule", "Routine Library", "Import Sheets"])

# ==========================================
# PAGE: TODAY'S PLAN
# ==========================================
if page == "Today's Plan":
    # Date Header
    col_title, col_pick = st.columns([3, 2])
    with col_title: st.title("🎯 Daily Dashboard")
    with col_pick: selected_date = st.date_input("Select Date", datetime.date.today())
    
    view_str = selected_date.strftime("%Y-%m-%d")
    
    # Load Data
    df_sched = load_data("schedule")
    df_routines = load_data("routines")
    df_logs = load_data("logs")

    today_plan = df_sched[df_sched["Date"] == view_str]
    
    if today_plan.empty:
        st.warning(f"No plan found for {view_str}.")
        st.stop()
    plan = today_plan.iloc[0]

    # --- 1. INTENT & CONSTRAINT CARD ---
    st.markdown(f"""
    <div class="workout-card">
        <h3 style="margin-top:0;">🧠 Game Plan</h3>
        <div style="display:flex; gap:20px; flex-wrap:wrap;">
            <div style="flex:1; background:#ffebee; padding:10px; border-radius:8px; border-left: 4px solid #ef5350;">
                <small style="color:#b71c1c; font-weight:bold;">CONSTRAINT</small><br>
                <span style="font-size:1.1em;">{plan['Daily Constraint'] if plan['Daily Constraint'] else 'None'}</span>
            </div>
            <div style="flex:1; background:#e3f2fd; padding:10px; border-radius:8px; border-left: 4px solid #42a5f5;">
                <small style="color:#0d47a1; font-weight:bold;">INTENT</small><br>
                <span style="font-size:1.1em;">{plan['Intent'] if plan['Intent'] else 'None'}</span>
            </div>
        </div>
        <div style="margin-top:10px; font-style:italic; color:#555;">
             {f"🎯 Command Focus: <b>{plan['Command Implement']}</b>" if plan['Command Implement'] else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- 2. THROWING ---
    t_plan = plan['Throwing Plan']
    with st.expander(f"⚾ Throwing: {t_plan if t_plan else 'Rest Day'}", expanded=(t_plan and t_plan != "Rest")):
        if t_plan and t_plan != "Rest":
            m1, m2, m3 = st.columns(3)
            m1.metric("Distance", plan['Long Toss Distance'])
            m2.metric("Mound", plan['Mound Style'])
            m3.metric("Goal Velo", plan['Goal Velocity'])
            
            # Check Details
            r_row = df_routines[df_routines["Routine Name"] == t_plan]
            if not r_row.empty:
                try:
                    ex_list = ast.literal_eval(r_row.iloc[0]["Exercises"])
                    st.table(pd.DataFrame(ex_list))
                except: pass
        else:
            st.info("Rest Day")

    # --- 3. LIFTING (IMPROVED UI) ---
    l_plan = plan['Lifting Plan']
    st.subheader(f"🏋️ Strength: {l_plan if l_plan else 'Rest'}")
    
    if l_plan:
        # Header Info
        wu = plan['Warm Up']
        st.markdown(f"""
        <div style="margin-bottom: 10px; padding: 8px; background: #f1f8e9; border-radius: 5px; border-left: 4px solid #7cb342;">
            <b>Warm Up:</b> {wu if wu else 'Standard'} {' | 🧘 Yoga' if plan['Yoga?']=='Yes' else ''}
        </div>
        """, unsafe_allow_html=True)
        
        # Find Routine
        routine_row = df_routines[df_routines["Routine Name"] == l_plan]
        
        # Fuzzy Search Fallback
        if routine_row.empty:
             mask = df_routines["Routine Name"].str.contains(l_plan, case=False, na=False)
             if mask.any(): routine_row = df_routines[mask].iloc[[0]]

        if not routine_row.empty:
            try:
                template_exercises = ast.literal_eval(routine_row.iloc[0]["Exercises"])
                existing_logs = df_logs[(df_logs["Date"] == view_str) & (df_logs["Routine Name"] == l_plan)]
                
                display_rows = []
                for ex in template_exercises:
                    ex_name = ex.get("Exercise", "Unknown")
                    match = existing_logs[existing_logs["Exercise"] == ex_name]
                    
                    # Parse % for Progress Bar (remove %)
                    pct_raw = ex.get("Percent", "")
                    try:
                        pct_val = float(pct_raw.replace("%", "").split("-")[0]) / 100
                    except:
                        pct_val = 0.0

                    # ROW BUILDER (New Order)
                    display_rows.append({
                        "Exercise": ex_name,
                        "Warm": ex.get("Warmup Sets", "-"),
                        "Work": ex.get("Working Sets", "-"),
                        "Reps": ex.get("Reps", "-"),
                        "Load (lbs)": ex.get("Load", "-"),
                        "Actual Weight": float(match.iloc[0]["Actual Weight"]) if not match.empty else 0.0,
                        "%1RM": pct_val, # Number 0-1 for progress bar
                        "RPE": ex.get("RPE", "-"),
                        "Rest": ex.get("Rest", "-"),
                        "Notes": ex.get("Notes", ""),
                        "Done": not match.empty
                    })
                
                # --- THE EDITOR ---
                edited_df = st.data_editor(
                    pd.DataFrame(display_rows),
                    column_config={
                        "Exercise": st.column_config.TextColumn(width="medium", disabled=True),
                        "Warm": st.column_config.TextColumn("Warm Sets", width="small", disabled=True),
                        "Work": st.column_config.TextColumn("Work Sets", width="small", disabled=True),
                        "Reps": st.column_config.TextColumn(width="small", disabled=True),
                        "Load (lbs)": st.column_config.TextColumn("Target", width="small", disabled=True),
                        
                        # MOVED HERE
                        "Actual Weight": st.column_config.NumberColumn("Your Load", min_value=0, step=2.5, format="%.1f"),
                        
                        "%1RM": st.column_config.ProgressColumn("Intensity", min_value=0, max_value=1, format="%.0f%%"),
                        "RPE": st.column_config.TextColumn(width="small", disabled=True),
                        "Rest": st.column_config.TextColumn(width="small", disabled=True),
                        "Notes": st.column_config.TextColumn(width="large", disabled=True),
                        "Done": st.column_config.CheckboxColumn(width="small")
                    },
                    hide_index=True, 
                    use_container_width=True,
                    height=600
                )
                
                c_save, c_clear = st.columns([1, 4])
                if c_save.button("💾 Save Workout"):
                    # Remove old logs for this specific routine/day
                    df_clean = df_logs[~((df_logs["Date"] == view_str) & (df_logs["Routine Name"] == l_plan))]
                    
                    new_rows = []
                    for _, row in edited_df.iterrows():
                        # Only save if they entered a weight or marked done
                        if row["Done"] or row["Actual Weight"] > 0:
                            new_rows.append({
                                "Date": view_str, 
                                "Routine Name": l_plan, 
                                "Exercise": row["Exercise"],
                                "Set #": 1, 
                                "Prescribed Weight": row["Load (lbs)"], 
                                "Actual Weight": row["Actual Weight"], 
                                "Actual Reps": 0
                            })
                    
                    save_data("logs", pd.concat([df_clean, pd.DataFrame(new_rows)], ignore_index=True))
                    st.success("Workout Saved!")
                    st.rerun()
                    
            except Exception as e: st.error(f"Error displaying routine: {e}")
        else:
            st.warning(f"Routine '{l_plan}' not found. Please check the 'Monthly Schedule' to ensure the name matches your imported Powerbuilding routines.")

# ==========================================
# PAGE: MONTHLY SCHEDULE
# ==========================================
elif page == "Monthly Schedule":
    st.title("🗓️ Schedule Editor")
    df_sched = load_data("schedule")
    df_routines = load_data("routines")
    
    lift_opts = [""] + sorted([r for r in df_routines["Routine Name"].unique()])
    
    col_d, col_t = st.columns([1, 3])
    with col_d:
        view_dt = st.date_input("Month", datetime.date.today())
        start = view_dt.replace(day=1)
        end = (start + pd.DateOffset(months=1)) - pd.DateOffset(days=1)
    mask = (pd.to_datetime(df_sched['Date']) >= pd.to_datetime(start)) & (pd.to_datetime(df_sched['Date']) <= pd.to_datetime(end))
    df_view = df_sched.loc[mask].copy()
    
    edited = st.data_editor(
        df_view,
        column_config={
            "Date": st.column_config.TextColumn(disabled=True),
            "Lifting Plan": st.column_config.SelectboxColumn("Lifting Routine", options=lift_opts),
            "Goal Velocity": st.column_config.TextColumn("Velo Goal"),
        },
        hide_index=True, use_container_width=True, height=600
    )
    if st.button("💾 Save Changes"):
        df_sched.set_index("Date", inplace=True)
        edited.set_index("Date", inplace=True)
        df_sched.update(edited)
        df_sched.reset_index(inplace=True)
        save_data("schedule", df_sched)
        st.success("Updated!")

# ==========================================
# PAGE: ROUTINE LIBRARY
# ==========================================
elif page == "Routine Library":
    st.title("📚 Library")
    df = load_data("routines")
    st.dataframe(df[["Routine Name", "Type"]], use_container_width=True)
    
    d_sel = st.selectbox("Select Routine to Delete", df["Routine Name"].unique())
    if st.button("Delete"):
        save_data("routines", df[df["Routine Name"] != d_sel])
        st.rerun()

# ==========================================
# PAGE: IMPORT SHEETS
# ==========================================
elif page == "Import Sheets":
    st.title("📂 Import Data")
    tab_sched, tab_pb = st.tabs(["Import Plan CSV", "Import Powerbuilding"])
    
    with tab_sched:
        st.markdown("Upload **25-26 Off-Season Plan**.")
        up = st.file_uploader("Schedule CSV", type=['csv'])
        if up:
            try:
                df = pd.read_csv(up)
                if "Date" in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'], format='mixed').dt.strftime('%Y-%m-%d')
                df = df.fillna("")
                for col in SCHED_COLS:
                    if col not in df.columns: df[col] = ""
                df.to_csv(FILES["schedule"], index=False)
                st.success("✅ Schedule Imported!")
            except Exception as e: st.error(f"Error: {e}")

    with tab_pb:
        st.markdown("Upload **Jeff Nippard Powerbuilding** CSV.")
        up_pb = st.file_uploader("Nippard CSV", type=['csv'])
        if up_pb:
            try:
                routines = parse_nippard_csv(up_pb)
                if routines:
                    df_existing = load_data("routines")
                    new_df = pd.DataFrame(routines)
                    final_df = pd.concat([df_existing, new_df], ignore_index=True)
                    save_data("routines", final_df)
                    st.success(f"✅ Successfully extracted {len(routines)} routines!")
                    st.info("Go to 'Today's Plan' to see the new layout.")
                else:
                    st.warning("No routines found. Check CSV format.")
            except Exception as e: st.error(f"Error parsing: {e}")
