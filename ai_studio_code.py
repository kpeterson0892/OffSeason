import streamlit as st
import pandas as pd
import datetime
import os
import ast

# ==========================================
# 1. CONFIGURATION
# ==========================================
st.set_page_config(page_title="Ace Performance", page_icon="⚾", layout="wide")

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
    "velo": "velo_data.csv",
    "bodyweight": "bw_data.csv"
}

def load_data(key):
    if not os.path.exists(FILES[key]):
        # Initialize default files if they don't exist
        if key == "routines":
            return pd.DataFrame(columns=["Routine Name", "Type", "Exercises"])
        elif key == "schedule":
            # Create full year schedule
            dates = pd.date_range(start=f"{datetime.date.today().year}-01-01", end=f"{datetime.date.today().year}-12-31")
            df = pd.DataFrame({"Date": dates})
            df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
            df["Throwing Routine"] = "Rest Day"
            df["Lifting Routine"] = "Rest Day"
            df["Custom Notes"] = ""
            return df
        elif key == "logs":
            return pd.DataFrame(columns=["Date", "Routine Name", "Exercise", "Set #", "Prescribed Weight", "Actual Weight", "Actual Reps"])
        elif key == "velo":
            return pd.DataFrame(columns=["Date", "Velo"])
        elif key == "bodyweight":
            return pd.DataFrame(columns=["Date", "Weight"])
        return pd.DataFrame()
    
    # Load CSV
    df = pd.read_csv(FILES[key])
    
    # --- CRITICAL FIX: SANITIZE DATA ---
    # This prevents the "StreamlitAPIException" by ensuring no NaNs exist in text columns
    if key == "schedule":
        df["Date"] = df["Date"].astype(str)
        df["Throwing Routine"] = df["Throwing Routine"].fillna("Rest Day").astype(str)
        df["Lifting Routine"] = df["Lifting Routine"].fillna("Rest Day").astype(str)
        df["Custom Notes"] = df["Custom Notes"].fillna("").astype(str)
    
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
st.sidebar.title("⚾ Ace Ops")
page = st.sidebar.radio("Go to:", ["Today's Workout", "Calendar Planner", "Routine Builder", "Analytics"])

# ==========================================
# PAGE: TODAY'S WORKOUT
# ==========================================
if page == "Today's Workout":
    st.title("💪 Today's Session")
    st.caption(f"Date: {datetime.date.today().strftime('%A, %B %d')}")
    
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    df_sched = load_data("schedule")
    df_routines = load_data("routines")
    df_logs = load_data("logs")

    # Get Schedule
    today_plan = df_sched[df_sched["Date"] == today_str]
    
    if today_plan.empty:
        st.info("No schedule found for today. Go to Calendar Planner to set it up.")
    else:
        plan = today_plan.iloc[0]
        lift_name = plan.get("Lifting Routine", "Rest Day")
        throw_name = plan.get("Throwing Routine", "Rest Day")
        note = plan.get("Custom Notes", "")

        if note and note != "nan" and note != "":
            st.warning(f"📝 **Coach Note:** {note}")

        tab_lift, tab_throw = st.tabs(["🏋️ Lifting Log", "⚾ Throwing Log"])

        # === LIFTING ===
        with tab_lift:
            if lift_name == "Rest Day" or lift_name == "nan":
                st.success("Rest Day / Recovery")
            else:
                st.subheader(f"Routine: {lift_name}")
                routine_row = df_routines[df_routines["Routine Name"] == lift_name]
                
                if not routine_row.empty:
                    try:
                        template_exercises = ast.literal_eval(routine_row.iloc[0]["Exercises"])
                        
                        # Check for existing logs
                        existing_logs = df_logs[
                            (df_logs["Date"] == today_str) & 
                            (df_logs["Routine Name"] == lift_name)
                        ]

                        display_rows = []
                        for ex in template_exercises:
                            ex_name = ex.get("Exercise", "Unknown")
                            prescribed_wt = ex.get("Weight", "-")
                            prescribed_reps = ex.get("Reps", "-")
                            prescribed_sets = ex.get("Sets", "3")
                            
                            log_match = existing_logs[existing_logs["Exercise"] == ex_name]
                            
                            if not log_match.empty:
                                actual_wt = log_match.iloc[0]["Actual Weight"]
                                actual_reps = log_match.iloc[0]["Actual Reps"]
                                completed = True
                            else:
                                actual_wt = 0.0
                                actual_reps = 0.0
                                completed = False

                            display_rows.append({
                                "Exercise": ex_name,
                                "Sets": prescribed_sets,
                                "Target Reps": prescribed_reps,
                                "Target Weight": prescribed_wt,
                                "Actual Weight": float(actual_wt) if pd.notna(actual_wt) else 0.0,
                                "Actual Reps": float(actual_reps) if pd.notna(actual_reps) else 0.0,
                                "Done": completed
                            })

                        df_display = pd.DataFrame(display_rows)

                        st.markdown("##### Log your numbers below:")
                        edited_df = st.data_editor(
                            df_display,
                            column_config={
                                "Exercise": st.column_config.TextColumn(disabled=True),
                                "Sets": st.column_config.TextColumn(disabled=True),
                                "Target Reps": st.column_config.TextColumn(disabled=True),
                                "Target Weight": st.column_config.TextColumn("Prescribed", disabled=True),
                                "Actual Weight": st.column_config.NumberColumn("Actual Wt", min_value=0, step=5),
                                "Actual Reps": st.column_config.NumberColumn("Actual Reps", min_value=0, step=1),
                                "Done": st.column_config.CheckboxColumn("Done?")
                            },
                            hide_index=True,
                            use_container_width=True,
                            key="lift_editor"
                        )

                        if st.button("💾 Save Workout Log"):
                            # Remove old logs for this day/routine
                            df_clean_logs = df_logs[
                                ~((df_logs["Date"] == today_str) & (df_logs["Routine Name"] == lift_name))
                            ]
                            
                            new_rows = []
                            for index, row in edited_df.iterrows():
                                new_rows.append({
                                    "Date": today_str,
                                    "Routine Name": lift_name,
                                    "Exercise": row["Exercise"],
                                    "Set #": 1,
                                    "Prescribed Weight": row["Target Weight"],
                                    "Actual Weight": row["Actual Weight"],
                                    "Actual Reps": row["Actual Reps"]
                                })
                            
                            df_final = pd.concat([df_clean_logs, pd.DataFrame(new_rows)], ignore_index=True)
                            save_data("logs", df_final)
                            st.success("Workout saved!")
                    except Exception as e:
                        st.error(f"Error loading routine: {e}")
                else:
                    st.error("Routine not found in library.")

        # === THROWING ===
        with tab_throw:
            if throw_name == "Rest Day" or throw_name == "nan":
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
# PAGE: CALENDAR PLANNER
# ==========================================
elif page == "Calendar Planner":
    st.title("🗓️ Monthly Planner")
    
    df_routines = load_data("routines")
    df_sched = load_data("schedule")
    
    # 1. Prepare Dropdown Options
    # We must convert numpy array to python list and filter out NaNs
    if not df_routines.empty:
        throw_opts = ["Rest Day"] + [x for x in df_routines[df_routines["Type"] == "Throwing"]["Routine Name"].unique() if pd.notna(x)]
        lift_opts = ["Rest Day"] + [x for x in df_routines[df_routines["Type"] == "Lifting"]["Routine Name"].unique() if pd.notna(x)]
    else:
        throw_opts = ["Rest Day"]
        lift_opts = ["Rest Day"]

    col1, col2 = st.columns([1, 3])
    
    with col1:
        view_date = st.date_input("Select Month", datetime.date.today())
        start_date = view_date.replace(day=1)
        end_date = (start_date + pd.DateOffset(months=1)) - pd.DateOffset(days=1)
        st.info(f"Editing: {start_date.strftime('%B %Y')}")
        st.markdown("Click cells to select routines.")

    with col2:
        # Filter for month
        mask = (pd.to_datetime(df_sched['Date']) >= pd.to_datetime(start_date)) & \
               (pd.to_datetime(df_sched['Date']) <= pd.to_datetime(end_date))
        df_view = df_sched.loc[mask].copy()
        
        # --- DOUBLE CHECK TYPES BEFORE EDITOR ---
        df_view["Throwing Routine"] = df_view["Throwing Routine"].astype(str)
        df_view["Lifting Routine"] = df_view["Lifting Routine"].astype(str)
        df_view["Custom Notes"] = df_view["Custom Notes"].astype(str)

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
            height=600,
            key="planner_editor"
        )

        if st.button("💾 Save Calendar Changes"):
            df_sched.set_index("Date", inplace=True)
            edited_sched.set_index("Date", inplace=True)
            df_sched.update(edited_sched)
            df_sched.reset_index(inplace=True)
            save_data("schedule", df_sched)
            st.success("Calendar Updated!")

# ==========================================
# PAGE: ROUTINE BUILDER
# ==========================================
elif page == "Routine Builder":
    st.title("🛠️ Routine Builder")
    
    tab_create, tab_view = st.tabs(["Create New", "View Library"])

    with tab_create:
        st.subheader("Create New Routine")
        
        if "temp_routine" not in st.session_state:
            st.session_state.temp_routine = []

        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        ex = c1.text_input("Exercise Name")
        sets = c2.text_input("Sets", value="3")
        reps = c3.text_input("Target Reps", value="10")
        wt = c4.text_input("Target Weight", value="RPE 7")

        if st.button("Add Exercise"):
            st.session_state.temp_routine.append({
                "Exercise": ex, "Sets": sets, "Reps": reps, "Weight": wt
            })

        if st.session_state.temp_routine:
            st.write("---")
            df_preview = pd.DataFrame(st.session_state.temp_routine)
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
            
            sel_routine = st.selectbox("Select to Delete", df_lib["Routine Name"].unique())
            if st.button(f"Delete {sel_routine}"):
                df_new = df_lib[df_lib["Routine Name"] != sel_routine]
                save_data("routines", df_new)
                st.rerun()

# ==========================================
# PAGE: ANALYTICS
# ==========================================
elif page == "Analytics":
    st.title("📈 Performance Tracking")
    
    df_velo = load_data("velo")
    df_bw = load_data("bodyweight")
    df_logs = load_data("logs")

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

    with c_chart2:
        st.subheader("Bodyweight Trend")
        if not df_bw.empty:
            st.line_chart(df_bw, x="Date", y="Weight")
            
    if not df_logs.empty:
        st.divider()
        st.subheader("Strength Progression")
        ex_list = df_logs["Exercise"].unique()
        sel_ex = st.selectbox("Select Exercise", ex_list)
        
        df_chart = df_logs[df_logs["Exercise"] == sel_ex].copy()
        df_chart["Actual Weight"] = pd.to_numeric(df_chart["Actual Weight"], errors='coerce')
        st.line_chart(df_chart, x="Date", y="Actual Weight")
