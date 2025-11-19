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
    
    /* Custom Box Styling for your specific fields */
    .metric-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
    }
    .constraint-box {
        background-color: #ffebee; /* Red tint */
        border-left: 5px solid #ef5350;
        padding: 10px;
        border-radius: 5px;
    }
    .intent-box {
        background-color: #e3f2fd; /* Blue tint */
        border-left: 5px solid #42a5f5;
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA STRUCTURE (MATCHING YOUR SHEET)
# ==========================================
FILES = {
    "schedule": "schedule_data.csv",
    "routines": "routines_library.csv",
    "logs": "workout_logs.csv", 
    "velo": "velo_data.csv"
}

# EXACT COLUMNS FROM YOUR SHEET REQUEST
SCHED_COLS = [
    "Date", 
    "Warm-Up", 
    "Throwing", 
    "Constraint", 
    "Intent", 
    "Command Implement", 
    "Lift", 
    "Distance", 
    "Velo Goal"
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
        df["Date"] = df["Date"].astype(str)
        # Ensure all your specific columns exist
        for col in SCHED_COLS:
            if col not in df.columns: df[col] = ""
        # Fill NaNs
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

    today_plan = df_sched[df_sched["Date"] == today_str]
    
    if today_plan.empty:
        st.warning("No plan found for today. Please check the Monthly Schedule.")
        st.stop()
        
    plan = today_plan.iloc[0]

    # --- ROW 1: HIGH LEVEL INFO ---
    c1, c2, c3 = st.columns([1, 1, 1])
    
    with c1:
        st.markdown(f"<div class='constraint-box'><b>⚠️ Constraint</b><br>{plan['Constraint'] if plan['Constraint'] else '-'}</div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='intent-box'><b>🧠 Intent</b><br>{plan['Intent'] if plan['Intent'] else '-'}</div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='intent-box'><b>🎯 Command Implement</b><br>{plan['Command Implement'] if plan['Command Implement'] else '-'}</div>", unsafe_allow_html=True)

    st.divider()

    # --- ROW 2: WARM UP & THROWING ---
    col_warm, col_throw = st.columns(2)
    
    with col_warm:
        st.subheader("🔥 Warm-Up")
        if plan['Warm-Up']:
            st.info(f"**Routine:** {plan['Warm-Up']}")
            # Show details if available
            r_row = df_routines[df_routines["Routine Name"] == plan['Warm-Up']]
            if not r_row.empty:
                try:
                    ex_list = ast.literal_eval(r_row.iloc[0]["Exercises"])
                    st.dataframe(pd.DataFrame(ex_list), hide_index=True)
                except: pass
        else:
            st.write("No specific warm-up assigned.")

    with col_throw:
        st.subheader("⚾ Throwing")
        if plan['Throwing']:
            st.success(f"**Routine:** {plan['Throwing']}")
            
            # Metrics Row
            m1, m2 = st.columns(2)
            m1.metric("Distance", plan['Distance'] if plan['Distance'] else "-")
            m2.metric("Velo Goal", plan['Velo Goal'] if plan['Velo Goal'] else "-")
            
            # Show details
            r_row = df_routines[df_routines["Routine Name"] == plan['Throwing']]
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
            st.write("Rest Day / No Throwing")

    st.divider()

    # --- ROW 3: LIFTING (POWER BUILDING) ---
    st.subheader("🏋️ Lift: " + (plan['Lift'] if plan['Lift'] else "Rest"))
    
    if plan['Lift'] and plan['Lift'] != "Rest":
        routine_row = df_routines[df_routines["Routine Name"] == plan['Lift']]
        
        if not routine_row.empty:
            try:
                template_exercises = ast.literal_eval(routine_row.iloc[0]["Exercises"])
                existing_logs = df_logs[(df_logs["Date"] == today_str) & (df_logs["Routine Name"] == plan['Lift'])]
                
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
                    df_clean = df_logs[~((df_logs["Date"] == today_str) & (df_logs["Routine Name"] == plan['Lift']))]
                    new_rows = []
                    for _, row in edited_df.iterrows():
                        new_rows.append({
                            "Date": today_str, "Routine Name": plan['Lift'], "Exercise": row["Exercise"],
                            "Set #": 1, "Prescribed Weight": row["Target Wt"], 
                            "Actual Weight": row["Actual Wt"], "Actual Reps": row["Actual Reps"]
                        })
                    save_data("logs", pd.concat([df_clean, pd.DataFrame(new_rows)], ignore_index=True))
                    st.success("Lift Saved!")
            except Exception as e: st.error(f"Error loading lift: {e}")
        else:
            st.info("Lift routine found in schedule but details missing from Library. Go to 'Import Sheets' to upload your Power Building sheet.")


# ==========================================
# PAGE: MONTHLY SCHEDULE (PLANNER)
# ==========================================
elif page == "Monthly Schedule":
    st.title("🗓️ Monthly Schedule")
    st.caption("Edit your 25-26 Off-Season Plan here.")
    
    df_sched = load_data("schedule")
    df_routines = load_data("routines")
    
    # Dropdown Options
    routines = df_routines["Routine Name"].unique().tolist() if not df_routines.empty else []
    lift_opts = [""] + [r for r in routines if "Lift" in str(df_routines[df_routines["Routine Name"]==r]["Type"].values)]
    throw_opts = [""] + [r for r in routines if "Throwing" in str(df_routines[df_routines["Routine Name"]==r]["Type"].values)]
    warm_opts = [""] + [r for r in routines if "Warm-Up" in str(df_routines[df_routines["Routine Name"]==r]["Type"].values)]
    
    # Fallback if types aren't set strictly
    if not lift_opts: lift_opts = [""] + routines
    if not throw_opts: throw_opts = [""] + routines
    
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
                "Warm-Up": st.column_config.SelectboxColumn("Warm Up", options=warm_opts),
                "Throwing": st.column_config.SelectboxColumn("Throwing", options=throw_opts),
                "Lift": st.column_config.SelectboxColumn("Lift", options=lift_opts),
                "Constraint": st.column_config.TextColumn("Constraint"),
                "Intent": st.column_config.TextColumn("Intent"),
                "Command Implement": st.column_config.TextColumn("Cmd Implement"),
                "Distance": st.column_config.TextColumn("Dist"),
                "Velo Goal": st.column_config.TextColumn("Velo Goal"),
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
            name = c_name.text_input("Routine Name (e.g. Power Building Day 1)")
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
    st.info("Upload your Power Building sheet or Master Schedule here.")
    
    tab_sched, tab_pb = st.tabs(["Import Schedule", "Import Power Building"])
    
    with tab_sched:
        st.markdown("Upload a CSV matching the 25-26 Off-Season columns.")
        up = st.file_uploader("Schedule CSV", type=['csv'])
        if up:
            try:
                df = pd.read_csv(up)
                # Basic validation
                if "Constraint" in df.columns and "Intent" in df.columns:
                    df.to_csv(FILES["schedule"], index=False)
                    st.success("Schedule Imported!")
                else: st.error("Headers don't match.")
            except Exception as e: st.error(f"{e}")

    with tab_pb:
        st.markdown("""
        **Import Power Building Lifts:**
        Upload a CSV with columns: `Routine Name`, `Exercise`, `Sets`, `Reps`, `Weight`
        """)
        up_pb = st.file_uploader("Power Building CSV", type=['csv'])
        if up_pb:
            try:
                df_pb = pd.read_csv(up_pb)
                # Logic to convert flat CSV to routine structure
                # Group by Routine Name and create list of dicts
                import_count = 0
                for name, group in df_pb.groupby("Routine Name"):
                    exercises = []
                    for _, row in group.iterrows():
                        exercises.append({
                            "Exercise": row.get("Exercise", ""),
                            "Sets": row.get("Sets", ""),
                            "Reps": row.get("Reps", ""),
                            "Weight": row.get("Weight", "")
                        })
                    # Save
                    append_data("routines", {
                        "Routine Name": name,
                        "Type": "Lifting",
                        "Exercises": str(exercises)
                    })
                    import_count += 1
                st.success(f"Successfully imported {import_count} routines!")
            except Exception as e: st.error(f"Error: {e}")
