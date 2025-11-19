import streamlit as st
import pandas as pd
import datetime
import os
import ast

# ==========================================
# 1. CONFIGURATION (Native & Clean)
# ==========================================
st.set_page_config(page_title="Ace Performance", page_icon="⚾", layout="wide")

# We remove complex CSS to ensure readability. 
# We only add a small tweak to make tables look cleaner.
st.markdown("""
<style>
    .stDataFrame { border-radius: 10px; overflow: hidden; }
    .stButton button { border-radius: 20px; font-weight: bold; }
    /* Metric cards styling */
    div[data-testid="stMetric"] {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    /* Dark mode compatibility for metric cards */
    @media (prefers-color-scheme: dark) {
        div[data-testid="stMetric"] {
            background-color: #262730;
        }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA HANDLING
# ==========================================
FILES = {
    "schedule": "schedule_data.csv",
    "routines": "routines_library.csv",
    "logs": "workout_logs.csv", # NEW: Stores the actual vs prescribed data
    "velo": "velo_data.csv",
    "bodyweight": "bw_data.csv"
}

def load_data(key):
    if not os.path.exists(FILES[key]):
        if key == "routines":
            return pd.DataFrame(columns=["Routine Name", "Type", "Exercises"])
        elif key == "schedule":
            # Default schedule
            dates = pd.date_range(start=f"{datetime.date.today().year}-01-01", end=f"{datetime.date.today().year}-12-31")
            df = pd.DataFrame({"Date": dates})
            df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
            df["Throwing Routine"] = "Rest Day"
            df["Lifting Routine"] = "Rest Day"
            df["Custom Notes"] = ""
            return df
        elif key == "logs":
            # Stores detailed set-by-set logs
            return pd.DataFrame(columns=["Date", "Routine Name", "Exercise", "Set #", "Prescribed Weight", "Actual Weight", "Actual Reps"])
        elif key == "velo":
            return pd.DataFrame(columns=["Date", "Velo"])
        elif key == "bodyweight":
            return pd.DataFrame(columns=["Date", "Weight"])
        return pd.DataFrame()
    
    df = pd.read_csv(FILES[key])
    if key == "schedule":
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
# 3. NAVIGATION (Top Bar)
# ==========================================
# Using a sleek radio button that looks like tabs
st.sidebar.title("⚾ Ace Ops")
page = st.sidebar.radio("Go to:", ["Today's Workout", "Calendar Planner", "Routine Builder", "Analytics"])

# ==========================================
# PAGE: TODAY'S WORKOUT (The Logger)
# ==========================================
if page == "Today's Workout":
    st.title("💪 Today's Session")
    st.caption(f"Date: {datetime.date.today().strftime('%A, %B %d')}")
    
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    df_sched = load_data("schedule")
    df_routines = load_data("routines")
    df_logs = load_data("logs")

    # 1. Get Schedule
    today_plan = df_sched[df_sched["Date"] == today_str]
    
    if today_plan.empty:
        st.info("No schedule generated for this year yet.")
        st.stop()

    plan = today_plan.iloc[0]
    lift_name = plan.get("Lifting Routine", "Rest Day")
    throw_name = plan.get("Throwing Routine", "Rest Day")
    note = plan.get("Custom Notes", "")

    if note and not pd.isna(note):
        st.warning(f"📝 **Coach Note:** {note}")

    # --- TABS for Lift vs Throw ---
    tab_lift, tab_throw = st.tabs(["🏋️ Lifting Log", "⚾ Throwing Log"])

    # === LIFTING LOGIC ===
    with tab_lift:
        if lift_name == "Rest Day" or pd.isna(lift_name):
            st.success("Rest Day / Recovery")
        else:
            st.subheader(f"Routine: {lift_name}")
            
            # Find the routine template
            routine_row = df_routines[df_routines["Routine Name"] == lift_name]
            
            if not routine_row.empty:
                # Parse the template exercises
                try:
                    template_exercises = ast.literal_eval(routine_row.iloc[0]["Exercises"])
                    # template_exercises is a list of dicts: [{'Exercise': 'Squat', 'Sets': '3', 'Weight': '225'}, ...]
                except:
                    st.error("Error reading routine data.")
                    st.stop()

                # Check if we already logged data for TODAY and THIS ROUTINE
                existing_logs = df_logs[
                    (df_logs["Date"] == today_str) & 
                    (df_logs["Routine Name"] == lift_name)
                ]

                # PREPARE THE DATA FOR THE EDITOR
                # We want a row for every exercise.
                # If log exists, use that. If not, use template.
                
                display_rows = []
                
                for ex in template_exercises:
                    # Default values from template
                    ex_name = ex.get("Exercise", "Unknown")
                    prescribed_wt = ex.get("Weight", "-")
                    prescribed_reps = ex.get("Reps", "-")
                    prescribed_sets = ex.get("Sets", "3") # Default to 3 if missing
                    
                    # Try to find existing log for this exercise
                    # (Simplified: we just track one main set for the summary, 
                    # or we can list multiple sets. Let's list 1 row per exercise for simplicity first)
                    
                    log_match = existing_logs[existing_logs["Exercise"] == ex_name]
                    
                    if not log_match.empty:
                        # Load saved actuals
                        actual_wt = log_match.iloc[0]["Actual Weight"]
                        actual_reps = log_match.iloc[0]["Actual Reps"]
                    else:
                        # Default to empty or 0
                        actual_wt = 0.0
                        actual_reps = 0.0

                    display_rows.append({
                        "Exercise": ex_name,
                        "Sets": prescribed_sets,
                        "Target Reps": prescribed_reps,
                        "Target Weight": prescribed_wt,
                        "Actual Weight (lbs)": float(actual_wt),
                        "Actual Reps": float(actual_reps),
                        "Completed": False # Checkbox
                    })

                # Create DataFrame
                df_display = pd.DataFrame(display_rows)

                # SHOW THE EDITOR
                st.markdown("##### Log your numbers below:")
                edited_df = st.data_editor(
                    df_display,
                    column_config={
                        "Exercise": st.column_config.TextColumn(disabled=True),
                        "Sets": st.column_config.TextColumn(disabled=True),
                        "Target Reps": st.column_config.TextColumn(disabled=True),
                        "Target Weight": st.column_config.TextColumn("Prescribed Wt", disabled=True),
                        "Actual Weight (lbs)": st.column_config.NumberColumn("Actual Wt", min_value=0, step=5),
                        "Actual Reps": st.column_config.NumberColumn("Actual Reps", min_value=0, step=1),
                        "Completed": st.column_config.CheckboxColumn("Done?")
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="lift_editor"
                )

                if st.button("💾 Save Workout Log"):
                    # Process the edited dataframe and save to CSV
                    # We remove old entries for this day/routine and replace with new ones
                    
                    # 1. Filter out old logs for today/routine
                    df_clean_logs = df_logs[
                        ~((df_logs["Date"] == today_str) & (df_logs["Routine Name"] == lift_name))
                    ]
                    
                    # 2. Create new rows
                    new_rows = []
                    for index, row in edited_df.iterrows():
                        new_rows.append({
                            "Date": today_str,
                            "Routine Name": lift_name,
                            "Exercise": row["Exercise"],
                            "Set #": 1, # Simplified for table view
                            "Prescribed Weight": row["Target Weight"],
                            "Actual Weight": row["Actual Weight (lbs)"],
                            "Actual Reps": row["Actual Reps"]
                        })
                    
                    # 3. Combine and Save
                    df_final = pd.concat([df_clean_logs, pd.DataFrame(new_rows)], ignore_index=True)
                    save_data("logs", df_final)
                    st.success("Workout saved!")
            else:
                st.error("Routine not found in library.")

    # === THROWING LOGIC (Simplified View) ===
    with tab_throw:
        if throw_name == "Rest Day" or pd.isna(throw_name):
            st.success("Rest Day")
        else:
            st.subheader(f"Throwing: {throw_name}")
            r_row = df_routines[df_routines["Routine Name"] == throw_name]
            if not r_row.empty:
                try:
                    ex_list = ast.literal_eval(r_row.iloc[0]["Exercises"])
                    st.table(pd.DataFrame(ex_list))
                except: pass
            
            st.divider()
            st.markdown("#### Quick Velo Log")
            c1, c2 = st.columns(2)
            v = c1.number_input("Max Velo Today", step=0.1)
            if c2.button("Log Velo"):
                append_data("velo", {"Date": today_str, "Velo": v})
                st.success("Logged")

# ==========================================
# PAGE: CALENDAR PLANNER (Drag & Drop Style)
# ==========================================
elif page == "Calendar Planner":
    st.title("🗓️ Monthly Planner")
    
    df_routines = load_data("routines")
    df_sched = load_data("schedule")
    
    if df_routines.empty:
        st.warning("Create some routines in the 'Routine Builder' first!")
        st.stop()

    throw_opts = ["Rest Day"] + df_routines[df_routines["Type"] == "Throwing"]["Routine Name"].unique().tolist()
    lift_opts = ["Rest Day"] + df_routines[df_routines["Type"] == "Lifting"]["Routine Name"].unique().tolist()

    col1, col2 = st.columns([1, 3])
    
    with col1:
        view_date = st.date_input("Select Month", datetime.date.today())
        # Calculate start/end of month
        start_date = view_date.replace(day=1)
        end_date = (start_date + pd.DateOffset(months=1)) - pd.DateOffset(days=1)
        st.info(f"Editing: {start_date.strftime('%B %Y')}")
        st.markdown("Use the table to assign routines. You can copy/paste and drag handle to fill cells.")

    with col2:
        # Filter schedule for this month
        mask = (pd.to_datetime(df_sched['Date']) >= pd.to_datetime(start_date)) & \
               (pd.to_datetime(df_sched['Date']) <= pd.to_datetime(end_date))
        df_view = df_sched.loc[mask].copy()
        
        edited_sched = st.data_editor(
            df_view,
            column_config={
                "Date": st.column_config.TextColumn(disabled=True),
                "Throwing Routine": st.column_config.SelectboxColumn("Throwing", options=throw_opts, required=True),
                "Lifting Routine": st.column_config.SelectboxColumn("Lifting", options=lift_opts, required=True),
                "Custom Notes": st.column_config.TextColumn("Notes")
            },
            hide_index=True,
            use_container_width=True,
            height=600
        )

        if st.button("💾 Save Calendar Changes"):
            # Merge changes back to main dataframe
            df_sched.set_index("Date", inplace=True)
            edited_sched.set_index("Date", inplace=True)
            df_sched.update(edited_sched)
            df_sched.reset_index(inplace=True)
            save_data("schedule", df_sched)
            st.success("Calendar Updated!")

# ==========================================
# PAGE: ROUTINE BUILDER (With Prescribed Wts)
# ==========================================
elif page == "Routine Builder":
    st.title("🛠️ Routine Builder")
    
    tab_create, tab_view = st.tabs(["Create New", "View Library"])

    with tab_create:
        st.subheader("Create New Routine")
        
        if "temp_routine" not in st.session_state:
            st.session_state.temp_routine = []

        # INPUTS
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        ex = c1.text_input("Exercise Name")
        sets = c2.text_input("Sets", value="3")
        reps = c3.text_input("Target Reps", value="10")
        wt = c4.text_input("Target Weight", value="RPE 7") # Prescribed

        if st.button("Add Exercise"):
            st.session_state.temp_routine.append({
                "Exercise": ex, "Sets": sets, "Reps": reps, "Weight": wt
            })

        # PREVIEW
        if st.session_state.temp_routine:
            st.write("---")
            st.write("### Routine Preview")
            df_preview = pd.DataFrame(st.session_state.temp_routine)
            # Allow deletion in preview
            edited_preview = st.data_editor(df_preview, num_rows="dynamic", key="routine_preview")

            c_name, c_type, c_btn = st.columns([2, 1, 1])
            r_name = c_name.text_input("Routine Name")
            r_type = c_type.selectbox("Type", ["Lifting", "Throwing"])
            
            if c_btn.button("Save to Library"):
                if r_name:
                    final_list = edited_preview.to_dict('records')
                    append_data("routines", {
                        "Routine Name": r_name,
                        "Type": r_type,
                        "Exercises": str(final_list)
                    })
                    st.success(f"Saved {r_name}!")
                    st.session_state.temp_routine = []
                    st.rerun()

    with tab_view:
        st.subheader("Your Library")
        df_lib = load_data("routines")
        if not df_lib.empty:
            st.dataframe(df_lib[["Routine Name", "Type"]], use_container_width=True)
            
            sel_routine = st.selectbox("Select to View Details", df_lib["Routine Name"].unique())
            row = df_lib[df_lib["Routine Name"] == sel_routine]
            if not row.empty:
                try:
                    details = ast.literal_eval(row.iloc[0]["Exercises"])
                    st.table(pd.DataFrame(details))
                    
                    if st.button(f"Delete {sel_routine}"):
                        df_new = df_lib[df_lib["Routine Name"] != sel_routine]
                        save_data("routines", df_new)
                        st.rerun()
                except: pass

# ==========================================
# PAGE: ANALYTICS
# ==========================================
elif page == "Analytics":
    st.title("📈 Performance Tracking")
    
    df_velo = load_data("velo")
    df_bw = load_data("bodyweight")
    df_logs = load_data("logs")

    # Top Metrics
    c1, c2, c3 = st.columns(3)
    
    max_v = df_velo["Velo"].max() if not df_velo.empty else 0
    curr_bw = df_bw["Weight"].iloc[-1] if not df_bw.empty else 0
    vol_lift = len(df_logs)
    
    c1.metric("Top Velo (MPH)", f"{max_v}")
    c2.metric("Bodyweight (lbs)", f"{curr_bw}")
    c3.metric("Sets Logged", f"{vol_lift}")

    st.divider()
    
    c_chart1, c_chart2 = st.columns(2)
    
    with c_chart1:
        st.subheader("Velocity Trend")
        if not df_velo.empty:
            st.line_chart(df_velo, x="Date", y="Velo")
        else:
            st.info("No Velo Data")

    with c_chart2:
        st.subheader("Bodyweight Trend")
        if not df_bw.empty:
            st.line_chart(df_bw, x="Date", y="Weight")
        else:
            st.info("No Bodyweight Data")
    
    st.divider()
    st.subheader("Strength Progression")
    if not df_logs.empty:
        ex_list = df_logs["Exercise"].unique()
        sel_ex = st.selectbox("Select Exercise", ex_list)
        
        df_chart = df_logs[df_logs["Exercise"] == sel_ex]
        df_chart["Actual Weight"] = pd.to_numeric(df_chart["Actual Weight"], errors='coerce')
        
        st.line_chart(df_chart, x="Date", y="Actual Weight")
