import streamlit as st
import pandas as pd
import datetime
import os
import ast

# ==========================================
# 1. CONFIGURATION
# ==========================================
st.set_page_config(page_title="25-26 Off-Season", page_icon="⚾", layout="wide")

# High contrast styling for mobile readability
st.markdown("""
<style>
    /* Make cards stand out */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        background-color: white;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
    }
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .stMetric { background-color: #262730; }
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

# The exact headers from your CSV
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
        # cleaning data so it shows up
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
# 3. NAVIGATION
# ==========================================
st.sidebar.title("⚾ 25-26 Off-Season")
page = st.sidebar.radio("Menu", ["Today's Plan", "Monthly Schedule", "Routine Library", "Import Sheets"])

# ==========================================
# PAGE: TODAY'S PLAN (DASHBOARD)
# ==========================================
if page == "Today's Plan":
    
    # --- DATE SELECTOR (For Testing) ---
    # Since your CSV starts on Nov 20, this lets you check future dates easily
    col_title, col_pick = st.columns([3, 2])
    with col_title:
        st.title("📅 Daily Plan")
    with col_pick:
        selected_date = st.date_input("Viewing Date:", datetime.date.today())
    
    view_str = selected_date.strftime("%Y-%m-%d")
    
    df_sched = load_data("schedule")
    df_routines = load_data("routines")
    df_logs = load_data("logs")

    # Find Plan
    today_plan = df_sched[df_sched["Date"] == view_str]
    
    if today_plan.empty:
        st.warning(f"No data found for {view_str}. If you uploaded a CSV, check the date format.")
        st.info("Tip: Your CSV starts on Nov 20. Try changing the date above.")
        st.stop()
        
    plan = today_plan.iloc[0]

    # --- SECTION 1: INTENT & CONSTRAINT ---
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            st.caption("⚠️ DAILY CONSTRAINT")
            # Bold, Large Text
            val = plan['Daily Constraint'] if plan['Daily Constraint'] else "None"
            st.markdown(f"### {val}")
        with c2:
            st.caption("🧠 INTENT")
            val = plan['Intent'] if plan['Intent'] else "None"
            st.markdown(f"### {val}")
            
        if plan['Command Implement']:
            st.caption("🎯 COMMAND FOCUS")
            st.write(f"**{plan['Command Implement']}**")

    # --- SECTION 2: THROWING ---
    st.subheader("⚾ Throwing")
    with st.container(border=True):
        t_plan = plan['Throwing Plan']
        
        if t_plan and t_plan != "Rest":
            st.markdown(f"## {t_plan}") # Big Header
            
            # 3 Column Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Long Toss", plan['Long Toss Distance'])
            m2.metric("Mound", plan['Mound Style'])
            m3.metric("Velo Goal", plan['Goal Velocity'])
            
            with st.expander("View Routine Details"):
                r_row = df_routines[df_routines["Routine Name"] == t_plan]
                if not r_row.empty:
                    try:
                        ex_list = ast.literal_eval(r_row.iloc[0]["Exercises"])
                        st.table(pd.DataFrame(ex_list))
                    except: st.write("Error reading exercises.")
                else:
                    st.warning(f"Routine '{t_plan}' not found in Library.")
            
            # Velo Log
            c_log, c_btn = st.columns([3, 1])
            v = c_log.number_input("Log Max Velo (MPH)", step=0.1)
            if c_btn.button("Save"):
                append_data("velo", {"Date": view_str, "Velo": v})
                st.success("Saved")
        else:
            st.markdown("## Rest Day")
            st.caption("No throwing scheduled.")

    # --- SECTION 3: LIFTING ---
    st.subheader("🏋️ Strength & Prep")
    with st.container(border=True):
        # Warm Up
        wu = plan['Warm Up']
        yoga = plan['Yoga?']
        if wu or yoga == "Yes":
            st.markdown(f"**Warm Up:** {wu if wu else 'Standard'}")
            if yoga == "Yes": st.success("🧘 Yoga Prescribed")
        
        st.divider()
        
        # Lift
        l_plan = plan['Lifting Plan']
        if l_plan:
            st.markdown(f"## {l_plan}")
            
            # Check Library
            routine_row = df_routines[df_routines["Routine Name"] == l_plan]
            
            if not routine_row.empty:
                try:
                    template_exercises = ast.literal_eval(routine_row.iloc[0]["Exercises"])
                    existing_logs = df_logs[(df_logs["Date"] == view_str) & (df_logs["Routine Name"] == l_plan)]
                    
                    # Prepare Table Data
                    display_rows = []
                    for ex in template_exercises:
                        ex_name = ex.get("Exercise", "Unknown")
                        match = existing_logs[existing_logs["Exercise"] == ex_name]
                        
                        display_rows.append({
                            "Exercise": ex_name,
                            "Sets": ex.get("Sets", "3"),
                            "Reps": ex.get("Reps", "10"),
                            "Target": ex.get("Weight", "-"),
                            "Actual Wt": float(match.iloc[0]["Actual Weight"]) if not match.empty else 0.0,
                            "Done": not match.empty
                        })
                    
                    df_display = pd.DataFrame(display_rows)
                    
                    edited_df = st.data_editor(
                        df_display,
                        column_config={
                            "Exercise": st.column_config.TextColumn(disabled=True),
                            "Sets": st.column_config.TextColumn(disabled=True),
                            "Reps": st.column_config.TextColumn(disabled=True),
                            "Target": st.column_config.TextColumn(disabled=True),
                            "Actual Wt": st.column_config.NumberColumn(min_value=0, step=5),
                            "Done": st.column_config.CheckboxColumn("?")
                        },
                        hide_index=True, use_container_width=True
                    )
                    
                    if st.button("💾 Save Lift Logs"):
                        df_clean = df_logs[~((df_logs["Date"] == view_str) & (df_logs["Routine Name"] == l_plan))]
                        new_rows = []
                        for _, row in edited_df.iterrows():
                            new_rows.append({
                                "Date": view_str, "Routine Name": l_plan, "Exercise": row["Exercise"],
                                "Set #": 1, "Prescribed Weight": row["Target"], 
                                "Actual Weight": row["Actual Wt"], "Actual Reps": 0 # Simplified
                            })
                        save_data("logs", pd.concat([df_clean, pd.DataFrame(new_rows)], ignore_index=True))
                        st.success("Lift Saved!")
                except: st.error("Error loading routine.")
            else:
                st.warning(f"Routine '{l_plan}' not found in Library. Please upload Power Building CSV.")
        else:
            st.markdown("## Rest Day")

# ==========================================
# PAGE: MONTHLY SCHEDULE
# ==========================================
elif page == "Monthly Schedule":
    st.title("🗓️ Schedule Editor")
    
    df_sched = load_data("schedule")
    
    col_date, col_info = st.columns([1, 3])
    with col_date:
        view_dt = st.date_input("Jump to Month", datetime.date.today())
        start = view_dt.replace(day=1)
        end = (start + pd.DateOffset(months=1)) - pd.DateOffset(days=1)
    
    mask = (pd.to_datetime(df_sched['Date']) >= pd.to_datetime(start)) & (pd.to_datetime(df_sched['Date']) <= pd.to_datetime(end))
    df_view = df_sched.loc[mask].copy()
    
    edited = st.data_editor(
        df_view,
        column_config={
            "Date": st.column_config.TextColumn(disabled=True),
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
        st.success("Schedule Updated!")

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
            r_type = c_type.selectbox("Category", ["Lifting", "Throwing"])
            
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
    
    tab_sched, tab_pb = st.tabs(["Import Schedule", "Import Power Building"])
    
    with tab_sched:
        st.markdown("Upload **25-26 Off-Season Plan** CSV.")
        up = st.file_uploader("Schedule CSV", type=['csv'])
        if up:
            try:
                df = pd.read_csv(up)
                
                # --- DATE FIXER ---
                # Convert "11-20-25" -> "2025-11-20"
                if "Date" in df.columns:
                    # Coerce any weird formats to datetime
                    df['Date'] = pd.to_datetime(df['Date'], format='mixed').dt.strftime('%Y-%m-%d')
                
                # Standardize NaN to empty string
                df = df.fillna("")
                
                # Ensure all columns exist (even if CSV is missing one)
                for col in SCHED_COLS:
                    if col not in df.columns:
                        df[col] = ""
                
                df.to_csv(FILES["schedule"], index=False)
                st.success(f"✅ Imported! Date range: {df['Date'].min()} to {df['Date'].max()}")
            except Exception as e: st.error(f"Error: {e}")

    with tab_pb:
        st.markdown("Upload Power Building CSV.")
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
