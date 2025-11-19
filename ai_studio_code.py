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

# Native Streamlit Styling (High Contrast / No Custom Colors)
st.markdown("""
<style>
    /* Increase font size for data tables for readability */
    div[data-testid="stDataFrame"] { width: 100%; }
    
    /* Make the Metric Cards look clean */
    div[data-testid="stMetric"] {
        background-color: #f0f2f6;
        border-radius: 8px;
        padding: 10px;
    }
    @media (prefers-color-scheme: dark) {
        div[data-testid="stMetric"] { background-color: #262730; }
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
# 3. PARSER (Fixing Data Loading Issues)
# ==========================================
def extract_row_data(row):
    """Helper to map CSV columns to Dict Keys based on your file structure"""
    def get_val(idx):
        try:
            s = str(row[idx]).strip()
            return "" if s == "nan" else s
        except: return ""

    # MAPPING BASED ON YOUR CSV:
    # Col 2 (Index 2): Exercise
    # Col 3 (Index 3): Warm-up Sets
    # Col 4 (Index 4): Working Sets
    # Col 5 (Index 5): Reps
    # Col 6 (Index 6): Load (lbs)
    # Col 7 (Index 7): %1RM
    # Col 8 (Index 8): RPE
    # Col 9 (Index 9): Rest
    # Col 10 (Index 10): Notes
    
    return {
        "Exercise": get_val(2),
        "Warm": get_val(3),
        "Work": get_val(4),
        "Reps": get_val(5),
        "Load": get_val(6),
        "Percent": get_val(7),
        "RPE": get_val(8),
        "Rest": get_val(9),
        "Notes": get_val(10)
    }

def parse_nippard_csv(file):
    """
    Parses the Powerbuilding CSV using the helper above.
    """
    df = pd.read_csv(file, header=None)
    
    extracted_routines = []
    current_week = "Week 1"
    current_routine_name = None
    current_exercises = []
    
    for index, row in df.iterrows():
        def get_val(idx):
            try:
                s = str(row[idx]).strip()
                return "" if s == "nan" else s
            except: return ""

        col_1 = get_val(1) # Week / Routine
        col_2 = get_val(2) # Exercise
        
        # 1. Detect Week Change
        if "Week" in col_1 and len(col_1) < 15:
            current_week = col_1
            continue

        # 2. Detect New Routine Header
        if col_1 and "Week" not in col_1 and "IMPORTANT" not in col_1 and "Jeff" not in col_1:
            # Save previous
            if current_routine_name and current_exercises:
                extracted_routines.append({
                    "Routine Name": current_routine_name,
                    "Type": "Lifting",
                    "Exercises": str(current_exercises)
                })
            
            # Start New
            clean_name = col_1.split(":")[0].strip()
            current_routine_name = f"{current_week} - {clean_name}"
            current_exercises = []
            
            # Check if first exercise is on same row (Col 2)
            if col_2 and col_2 != "Exercise":
                current_exercises.append(extract_row_data(row))
            continue

        # 3. Detect Standard Exercise Row
        if not col_1 and col_2:
            if "Exercise" in col_2 or "Warm-up" in col_2: continue
            current_exercises.append(extract_row_data(row))

    # Save final routine
    if current_routine_name and current_exercises:
        extracted_routines.append({
            "Routine Name": current_routine_name,
            "Type": "Lifting",
            "Exercises": str(current_exercises)
        })
        
    return extracted_routines

# ==========================================
# 4. NAVIGATION
# ==========================================
st.sidebar.title("⚾ 25-26 Off-Season")
page = st.sidebar.radio("Menu", ["Today's Plan", "Monthly Schedule", "Routine Library", "Import Sheets"])

# ==========================================
# PAGE: TODAY'S PLAN
# ==========================================
if page == "Today's Plan":
    col_title, col_pick = st.columns([3, 2])
    with col_title: st.title("🎯 Daily Dashboard")
    with col_pick: selected_date = st.date_input("Select Date", datetime.date.today())
    
    view_str = selected_date.strftime("%Y-%m-%d")
    
    df_sched = load_data("schedule")
    df_routines = load_data("routines")
    df_logs = load_data("logs")

    today_plan = df_sched[df_sched["Date"] == view_str]
    
    if today_plan.empty:
        st.warning(f"No plan found for {view_str}.")
        st.stop()
    plan = today_plan.iloc[0]

    # --- 1. INTENT & CONSTRAINT ---
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            st.caption("⚠️ CONSTRAINT")
            st.subheader(plan['Daily Constraint'] if plan['Daily Constraint'] else 'None')
        with c2:
            st.caption("🧠 INTENT")
            st.subheader(plan['Intent'] if plan['Intent'] else 'None')
        
        if plan['Command Implement']:
            st.divider()
            st.caption("🎯 COMMAND FOCUS")
            st.write(f"**{plan['Command Implement']}**")

    # --- 2. THROWING ---
    t_plan = plan['Throwing Plan']
    st.subheader("⚾ Throwing")
    with st.container(border=True):
        if t_plan and t_plan != "Rest":
            st.markdown(f"**Routine: {t_plan}**")
            m1, m2, m3 = st.columns(3)
            m1.metric("Dist", plan['Long Toss Distance'])
            m2.metric("Mound", plan['Mound Style'])
            m3.metric("Velo", plan['Goal Velocity'])
            
            r_row = df_routines[df_routines["Routine Name"] == t_plan]
            if not r_row.empty:
                with st.expander("View Routine Details"):
                    try:
                        ex_list = ast.literal_eval(r_row.iloc[0]["Exercises"])
                        st.table(pd.DataFrame(ex_list))
                    except: pass
        else:
            st.write("Rest Day")

    # --- 3. LIFTING (DASHBOARD FIXES) ---
    l_plan = plan['Lifting Plan']
    st.subheader("🏋️ Strength")
    
    if l_plan:
        with st.container(border=True):
            wu = plan['Warm Up']
            st.markdown(f"**Lift:** {l_plan}")
            st.caption(f"Warm Up: {wu if wu else 'Standard'} {' | 🧘 Yoga' if plan['Yoga?']=='Yes' else ''}")
            
            # Search Logic
            routine_row = df_routines[df_routines["Routine Name"] == l_plan]
            if routine_row.empty:
                mask = df_routines["Routine Name"].str.contains(l_plan, case=False, na=False)
                if mask.any(): routine_row = df_routines[mask].iloc[[0]]
            
            if not routine_row.empty:
                try:
                    template_exercises = ast.literal_eval(routine_row.iloc[0]["Exercises"])
                    existing_logs = df_logs[(df_logs["Date"] == view_str) & (df_logs["Routine Name"] == l_plan)]
                    
                    # --- BUILD TABLE DATA ---
                    display_rows = []
                    for ex in template_exercises:
                        ex_name = ex.get("Exercise", "Unknown")
                        match = existing_logs[existing_logs["Exercise"] == ex_name]
                        
                        display_rows.append({
                            "Exercise": ex_name,
                            "Sets": ex.get("Work", "3"), 
                            "Reps": ex.get("Reps", "10"),
                            "Target Load": ex.get("Load", "-"), 
                            # ACTUAL WEIGHT RIGHT NEXT TO TARGET
                            "Actual Weight": float(match.iloc[0]["Actual Weight"]) if not match.empty else 0.0,
                            "RPE": ex.get("RPE", "-"),
                            "Rest": ex.get("Rest", "-"),
                            "Notes": ex.get("Notes", ""),
                            "Done": not match.empty
                        })
                    
                    # --- RENDER TABLE WITH COLUMNS ---
                    edited_df = st.data_editor(
                        pd.DataFrame(display_rows),
                        column_config={
                            "Exercise": st.column_config.TextColumn(width="medium", disabled=True),
                            "Sets": st.column_config.TextColumn(width="small", disabled=True),
                            "Reps": st.column_config.TextColumn(width="small", disabled=True),
                            
                            "Target Load": st.column_config.TextColumn("Target", width="small", disabled=True),
                            "Actual Weight": st.column_config.NumberColumn("Actual", min_value=0, step=2.5),
                            
                            "RPE": st.column_config.TextColumn("RPE", width="small", disabled=True),
                            "Rest": st.column_config.TextColumn("Rest", width="small", disabled=True),
                            "Notes": st.column_config.TextColumn("Notes", width="large", disabled=True),
                            
                            "Done": st.column_config.CheckboxColumn(width="small")
                        },
                        hide_index=True, 
                        use_container_width=True
                    )
                    
                    if st.button("💾 Save Workout"):
                        df_clean = df_logs[~((df_logs["Date"] == view_str) & (df_logs["Routine Name"] == l_plan))]
                        new_rows = []
                        for _, row in edited_df.iterrows():
                            if row["Done"] or row["Actual Weight"] > 0:
                                new_rows.append({
                                    "Date": view_str, "Routine Name": l_plan, "Exercise": row["Exercise"],
                                    "Set #": 1, "Prescribed Weight": row["Target Load"], 
                                    "Actual Weight": row["Actual Weight"], "Actual Reps": 0
                                })
                        save_data("logs", pd.concat([df_clean, pd.DataFrame(new_rows)], ignore_index=True))
                        st.success("Saved!")
                except Exception as e: st.error(f"Error: {e}")
            else:
                st.warning("Routine not found. Check 'Monthly Schedule' to match names.")
    else:
        st.write("Rest Day")

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
                    st.info("Go to 'Today's Plan' to see the new columns.")
                else:
                    st.warning("No routines found. Check CSV format.")
            except Exception as e: st.error(f"Error parsing: {e}")
