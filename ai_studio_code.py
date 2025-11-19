import streamlit as st
import pandas as pd
import datetime
import os
import ast

# ==========================================
# 1. CONFIGURATION
# ==========================================
st.set_page_config(page_title="25-26 Off-Season", page_icon="⚾", layout="wide")

st.markdown("""
<style>
    .stDataFrame { border-radius: 10px; overflow: hidden; }
    .stButton button { border-radius: 20px; font-weight: bold; }
    
    .metric-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
    }
    .constraint-box {
        background-color: #ffebee;
        border-left: 5px solid #ef5350;
        padding: 10px;
        border-radius: 5px;
    }
    .intent-box {
        background-color: #e3f2fd;
        border-left: 5px solid #42a5f5;
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA STRUCTURE
# ==========================================
FILES = {
    "schedule": "schedule_data.csv",
    "routines": "routines_library.csv",
    "logs": "workout_logs.csv", 
    "velo": "velo_data.csv"
}

# EXACT COLUMNS FROM YOUR CSV
SCHED_COLS = [
    "Date", 
    "Lifting Plan", 
    "Warm Up", 
    "Yoga?", 
    "Throwing Plan", 
    "Daily Constraint", 
    "Intent", 
    "Long Toss Distance", 
    "Mound Style", 
    "Goal Velocity", 
    "Command Implement"
]

def load_data(key):
    if not os.path.exists(FILES[key]):
        if key == "routines":
            return pd.DataFrame(columns=["Routine Name", "Type", "Exercises"])
        elif key == "schedule":
            # Default empty year
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
        # Ensure Date is String
        df["Date"] = df["Date"].astype(str)
        # Ensure all columns exist
        for col in SCHED_COLS:
            if col not in df.columns: df[col] = ""
        # Fill NaNs with empty strings to prevent display errors
        df = df.fillna("")
        
    return df

def save_data(key, df):
    df.to_csv(FILES[key], index=False)

def append_data(key, new_row_dict):
    df = load_data(key)
    new_df = pd.DataFrame([new_row_dict])
    updated_df = pd.concat([df, new_df], ignore_index=True)
    updated_df.to_csv(FILES[key], index=False)

# ==========================================
# 3. NAVIGATION
# ==========================================
st.sidebar.title("⚾ 25-26 Off-Season")
page = st.sidebar.radio("Menu", ["Today's Plan", "Monthly Schedule", "Routine Library", "Import Sheets"])

# ==========================================
# PAGE: TODAY'S PLAN (DASHBOARD)
# ==========================================
if page == "Today's Plan":
    st.title("📅 Today's Plan")
    st.caption(f"{datetime.date.today().strftime('%A, %B %d, %Y')}")
    
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    df_sched = load_data("schedule")
    df_routines = load_data("routines")
    df_logs = load_data("logs")

    # Find Today
    today_plan = df_sched[df_sched["Date"] == today_str]
    
    if today_plan.empty:
        st.warning("No plan found for this date. (If you just uploaded a CSV, check if the Date format matched YYYY-MM-DD)")
        st.stop()
        
    plan = today_plan.iloc[0]

    # --- ROW 1: HIGH LEVEL INFO ---
    c1, c2, c3 = st.columns([1, 1, 1])
    
    # Mapping your CSV headers to the display
    constraint = plan.get('Daily Constraint', '')
    intent = plan.get('Intent', '')
    cmd_imp = plan.get('Command Implement', '')

    with c1:
        st.markdown(f"<div class='constraint-box'><b>⚠️ Constraint</b><br>{constraint if constraint else '-'}</div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='intent-box'><b>🧠 Intent</b><br>{intent if intent else '-'}</div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='intent-box'><b>🎯 Command Implement</b><br>{cmd_imp if cmd_imp else '-'}</div>", unsafe_allow_html=True)

    st.divider()

    # --- ROW 2: WARM UP & THROWING ---
    col_warm, col_throw = st.columns(2)
    
    with col_warm:
        st.subheader("🔥 Warm-Up")
        wu_name = str(plan.get('Warm Up', ''))
        yoga = str(plan.get('Yoga?', ''))
        
        if wu_name or yoga == "Yes":
            if wu_name: st.info(f"**Routine:** {wu_name}")
            if yoga == "Yes": st.success("🧘 Yoga Session Prescribed")
        else:
            st.write("Standard Prep")

    with col_throw:
        st.subheader("⚾ Throwing")
        throw_name = plan.get('Throwing Plan', '')
        
        if throw_name:
            st.success(f"**Routine:** {throw_name}")
            
            # Metrics Row
            m1, m2, m3 = st.columns(3)
            m1.metric("Distance", plan.get('Long Toss Distance', '-'))
            m2.metric("Goal Velo", plan.get('Goal Velocity', '-'))
            m3.metric("Mound", plan.get('Mound Style', '-'))
            
            # Show details if in library
            r_row = df_routines[df_routines["Routine Name"] == throw_name]
            if not r_row.empty:
                try:
                    ex_list = ast.literal_eval(r_row.iloc[0]["Exercises"])
                    st.dataframe(pd.DataFrame(ex_list), hide_index=True)
                except: pass
                
            # Quick Log Velo
            v = st.number_input("Log Actual Velo", step=0.1)
            if st.button("Save Velo"):
                append_data("velo", {"Date": today_str, "Velo": v})
                st.success("Logged!")
        else:
            st.write("Rest Day")

    st.divider()

    # --- ROW 3: LIFTING ---
    lift_name = plan.get('Lifting Plan', '')
    st.subheader("🏋️ Lift: " + (lift_name if lift_name else "Rest"))
    
    if lift_name:
        routine_row = df_routines[df_routines["Routine Name"] == lift_name]
        
        if not routine_row.empty:
            try:
                template_exercises = ast.literal_eval(routine_row.iloc[0]["Exercises"])
                existing_logs = df_logs[(df_logs["Date"] == today_str) & (df_logs["Routine Name"] == lift_name)]
                
                display_rows = []
                for ex in template_exercises:
                    ex_name = ex.get("Exercise", "Unknown")
                    match = existing_logs[existing_logs["Exercise"] == ex_name]
                    
                    display_rows.append({
                        "Exercise": ex_name,
                        "Sets": ex.get("Sets", "3"),
                        "Reps": ex.get("Reps", "10"),
                        "Target Wt": ex.get("Weight", "-"),
                        "Actual Wt": float(match.iloc[0]["Actual Weight"]) if not match.empty else 0.0,
                        "Actual Reps": float(match.iloc[0]["Actual Reps"]) if not match.empty else 0.0,
                        "Done": not match.empty
                    })
                
                df_display = pd.DataFrame(display_rows)
                
                edited_df = st.data_editor(
                    df_display,
                    column_config={
                        "Exercise": st.column_config.TextColumn(disabled=True),
                        "Sets": st.column_config.TextColumn(disabled=True),
                        "Reps": st.column_config.TextColumn(disabled=True),
                        "Target Wt": st.column_config.TextColumn(disabled=True),
                        "Actual Wt": st.column_config.NumberColumn(min_value=0, step=5),
                        "Actual Reps": st.column_config.NumberColumn(min_value=0, step=1),
                        "Done": st.column_config.CheckboxColumn("Completed?")
                    },
                    hide_index=True, use_container_width=True
                )
                
                if st.button("💾 Save Lift"):
                    df_clean = df_logs[~((df_logs["Date"] == today_str) & (df_logs["Routine Name"] == lift_name))]
                    new_rows = []
                    for _, row in edited_df.iterrows():
                        new_rows.append({
                            "Date": today_str, "Routine Name": lift_name, "Exercise": row["Exercise"],
                            "Set #": 1, "Prescribed Weight": row["Target Wt"], 
                            "Actual Weight": row["Actual Wt"], "Actual Reps": row["Actual Reps"]
                        })
                    save_data("logs", pd.concat([df_clean, pd.DataFrame(new_rows)], ignore_index=True))
                    st.success("Lift Saved!")
            except Exception as e: st.error(f"Error loading lift: {e}")
        else:
            st.info(f"Routine '{lift_name}' not found in library. Go to 'Import Sheets' to upload your Power Building CSV.")


# ==========================================
# PAGE: MONTHLY SCHEDULE
# ==========================================
elif page == "Monthly Schedule":
    st.title("🗓️ Monthly Schedule")
    
    df_sched = load_data("schedule")
    df_routines = load_data("routines")
    
    # Dropdowns
    routines = df_routines["Routine Name"].unique().tolist() if not df_routines.empty else []
    
    # Date Picker
    col_date, col_table = st.columns([1, 4])
    with col_date:
        view_dt = st.date_input("Month View", datetime.date.today())
        start = view_dt.replace(day=1)
        end = (start + pd.DateOffset(months=1)) - pd.DateOffset(days=1)
    
    with col_table:
        mask = (pd.to_datetime(df_sched['Date']) >= pd.to_datetime(start)) & (pd.to_datetime(df_sched['Date']) <= pd.to_datetime(end))
        df_view = df_sched.loc[mask].copy()
        
        edited = st.data_editor(
            df_view,
            column_config={
                "Date": st.column_config.TextColumn(disabled=True),
                "Lifting Plan": st.column_config.SelectboxColumn("Lift", options=[""]+routines),
                "Throwing Plan": st.column_config.SelectboxColumn("Throwing", options=[""]+routines),
                "Yoga?": st.column_config.TextColumn("Yoga (Yes/No)"),
                "Goal Velocity": st.column_config.TextColumn("Goal Velo"), # Text for ranges like "~80"
            },
            hide_index=True, use_container_width=True, height=600
        )
        
        if st.button("💾 Update Schedule"):
            df_sched.set_index("Date", inplace=True)
            edited.set_index("Date", inplace=True)
            df_sched.update(edited)
            df_sched.reset_index(inplace=True)
            save_data("schedule", df_sched)
            st.success("Plan Updated!")

# ==========================================
# PAGE: ROUTINE LIBRARY
# ==========================================
elif page == "Routine Library":
    st.title("📚 Routine Library")
    
    tab1, tab2 = st.tabs(["Create New", "View All"])
    
    with tab1:
        if "new_rout" not in st.session_state: st.session_state.new_rout = []
        
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        ex = c1.text_input("Exercise")
        s = c2.text_input("Sets", "3")
        r = c3.text_input("Reps", "10")
        w = c4.text_input("Wt", "RPE 7")
        
        if st.button("Add"):
            st.session_state.new_rout.append({"Exercise": ex, "Sets": s, "Reps": r, "Weight": w})
            
        if st.session_state.new_rout:
            st.dataframe(pd.DataFrame(st.session_state.new_rout))
            
            c_name, c_type, c_save = st.columns([2, 1, 1])
            name = c_name.text_input("Routine Name (e.g. FB3)")
            r_type = c_type.selectbox("Category", ["Lifting", "Throwing", "Warm-Up"])
            
            if c_save.button("Save Routine"):
                if name:
                    append_data("routines", {
                        "Routine Name": name, "Type": r_type, 
                        "Exercises": str(st.session_state.new_rout)
                    })
                    st.success("Saved!")
                    st.session_state.new_rout = []
    
    with tab2:
        df = load_data("routines")
        st.dataframe(df[["Routine Name", "Type"]], use_container_width=True)


# ==========================================
# PAGE: IMPORT SHEETS
# ==========================================
elif page == "Import Sheets":
    st.title("📂 Import Data")
    
    tab_sched, tab_pb = st.tabs(["Import Plan CSV", "Import Power Building"])
    
    with tab_sched:
        st.markdown("Upload your **25-26 Off-Season Plan** CSV.")
        up = st.file_uploader("Schedule CSV", type=['csv'])
        if up:
            try:
                df = pd.read_csv(up)
                
                # DATE CONVERSION FIX
                # Your CSV has dates like 11-20-25 (M-D-YY)
                # App needs YYYY-MM-DD
                if "Date" in df.columns:
                    # Try to parse the format
                    df['Date'] = pd.to_datetime(df['Date'], format='%m-%d-%y').dt.strftime('%Y-%m-%d')
                
                # Check headers
                required = ["Lifting Plan", "Throwing Plan", "Daily Constraint"]
                if any(col in df.columns for col in required):
                    # Force columns to string to handle Velo ranges like "~80"
                    df = df.astype(str)
                    # Save
                    df.to_csv(FILES["schedule"], index=False)
                    st.success("✅ Schedule Imported & Dates Fixed!")
                else:
                    st.error(f"Headers mismatch. Expected something like: {SCHED_COLS}")
            except Exception as e: st.error(f"Error: {e}")

    with tab_pb:
        st.markdown("Import Power Building Lifts CSV.")
        up_pb = st.file_uploader("Power Building CSV", type=['csv'])
        if up_pb:
            try:
                df_pb = pd.read_csv(up_pb)
                count = 0
                for name, group in df_pb.groupby("Routine Name"):
                    exercises = []
                    for _, row in group.iterrows():
                        exercises.append({
                            "Exercise": row.get("Exercise", ""),
                            "Sets": row.get("Sets", ""),
                            "Reps": row.get("Reps", ""),
                            "Weight": row.get("Weight", "")
                        })
                    append_data("routines", {
                        "Routine Name": name,
                        "Type": "Lifting",
                        "Exercises": str(exercises)
                    })
                    count += 1
                st.success(f"Imported {count} routines!")
            except Exception as e: st.error(f"Error: {e}")
