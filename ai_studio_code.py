import streamlit as st
import pandas as pd
import datetime
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Ace Performance", page_icon="⚾", layout="wide")

# --- DATA FILES ---
# We use CSVs for simplicity. In a real app, these would be database connections.
FILES = {
    "schedule": "schedule_data.csv",
    "routines": "routines_library.csv",  # NEW FILE for saving templates
    "lifts": "lift_data.csv",
    "velo": "velo_data.csv",
    "bodyweight": "bw_data.csv"
}

# --- FUNCTIONS ---
def load_data(key):
    if not os.path.exists(FILES[key]):
        # Initialize empty dataframes with correct columns if file doesn't exist
        if key == "routines":
            return pd.DataFrame(columns=["Routine Name", "Type", "Details"])
        elif key == "schedule":
            return pd.DataFrame(columns=["Date", "Throwing Routine", "Lifting Routine", "Custom Notes"])
        return pd.DataFrame()
    return pd.read_csv(FILES[key])

def save_data(key, new_row_dict):
    df = load_data(key)
    new_df = pd.DataFrame([new_row_dict])
    updated_df = pd.concat([df, new_df], ignore_index=True)
    updated_df.to_csv(FILES[key], index=False)
    return updated_df

# --- SIDEBAR ---
st.sidebar.title("⚾ Ace Performance")
page = st.sidebar.radio("Menu", [
    "Daily Dashboard", 
    "Routine Builder",   # NEW
    "Assign Schedule",   # UPDATED
    "Track Lifts", 
    "Track Velocity", 
    "Track Bodyweight"
])

# --- 1. ROUTINE BUILDER (NEW) ---
if page == "Routine Builder":
    st.title("🛠️ Create Standard Routines")
    st.info("Create your standard workouts here so you don't have to type them every time.")

    with st.form("create_routine"):
        r_name = st.text_input("Routine Name (e.g., 'Hypertrophy A', 'Long Toss')")
        r_type = st.selectbox("Type", ["Lifting", "Throwing"])
        r_details = st.text_area("Details (Exercises, Sets, Reps, Distances)")
        
        submitted = st.form_submit_button("Save to Library")
        if submitted and r_name:
            save_data("routines", {
                "Routine Name": r_name, 
                "Type": r_type, 
                "Details": r_details
            })
            st.success(f"Saved routine: {r_name}")

    # Show current library
    st.subheader("Your Library")
    df_routines = load_data("routines")
    if not df_routines.empty:
        st.dataframe(df_routines)

# --- 2. ASSIGN SCHEDULE (UPDATED) ---
elif page == "Assign Schedule":
    st.title("Pf🗓️ Plan Your Month")
    
    # Load routines to populate dropdowns
    df_routines = load_data("routines")
    
    # Separate lift routines from throwing routines
    lift_options = ["Rest Day"] + df_routines[df_routines["Type"] == "Lifting"]["Routine Name"].tolist()
    throw_options = ["Rest Day"] + df_routines[df_routines["Type"] == "Throwing"]["Routine Name"].tolist()

    with st.form("assign_form"):
        date = st.date_input("Select Date", datetime.date.today())
        
        col1, col2 = st.columns(2)
        with col1:
            selected_throw = st.selectbox("Throwing Plan", throw_options)
        with col2:
            selected_lift = st.selectbox("Lifting Plan", lift_options)
            
        notes = st.text_input("Custom Notes (Optional)")
        
        if st.form_submit_button("Assign to Date"):
            # We overwrite if date exists, or append if new (simplified logic for CSV)
            # In a real DB, you'd use an UPDATE query.
            # For CSV, we just save a new row. Dashboard logic picks the latest entry for that date.
            save_data("schedule", {
                "Date": date,
                "Throwing Routine": selected_throw,
                "Lifting Routine": selected_lift,
                "Custom Notes": notes
            })
            st.success(f"Schedule updated for {date}")

# --- 3. DAILY DASHBOARD (UPDATED) ---
elif page == "Daily Dashboard":
    st.title("📅 Today's Training")
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    # Load Schedule
    df_sched = load_data("schedule")
    df_routines = load_data("routines")
    
    # Find plan for today
    today_plan = df_sched[df_sched["Date"] == today_str]
    
    if not today_plan.empty:
        # Get the most recent entry for today (in case of updates)
        plan = today_plan.iloc[-1] 
        
        col1, col2 = st.columns(2)
        
        # -- THROWING COLUMN --
        with col1:
            st.markdown(f"### ⚾ Throwing: {plan['Throwing Routine']}")
            if plan['Throwing Routine'] != "Rest Day":
                # Lookup details from routine library
                r_detail = df_routines[df_routines["Routine Name"] == plan['Throwing Routine']]["Details"]
                if not r_detail.empty:
                    st.info(r_detail.values[0])
        
        # -- LIFTING COLUMN --
        with col2:
            st.markdown(f"### 🏋️ Lifting: {plan['Lifting Routine']}")
            if plan['Lifting Routine'] != "Rest Day":
                # Lookup details
                r_detail = df_routines[df_routines["Routine Name"] == plan['Lifting Routine']]["Details"]
                if not r_detail.empty:
                    st.success(r_detail.values[0])

        if pd.notna(plan['Custom Notes']) and plan['Custom Notes']:
            st.warning(f"📝 **Coach Notes:** {plan['Custom Notes']}")
            
    else:
        st.header("No workout scheduled today.")
        st.markdown("*Enjoy your recovery or check with coach.*")

# --- 4. TRACKING PAGES (SAME AS BEFORE) ---
elif page == "Track Lifts":
    st.title("🏋️ Log Lifts")
    with st.form("lift"):
        date = st.date_input("Date", datetime.date.today())
        exercise = st.selectbox("Exercise", ["Squat", "Bench", "Deadlift", "Chinup"])
        weight = st.number_input("Weight", step=5)
        reps = st.number_input("Reps", step=1)
        if st.form_submit_button("Log"):
            save_data("lifts", {"Date": date, "Exercise": exercise, "Weight": weight, "Reps": reps})
            st.success("Logged")
            
    df = load_data("lifts")
    if not df.empty:
        st.line_chart(df[df["Exercise"]==exercise], x="Date", y="Weight")

elif page == "Track Velocity":
    st.title("🔥 Log Velocity")
    with st.form("velo"):
        date = st.date_input("Date", datetime.date.today())
        velo = st.number_input("Max Velo (MPH)", step=0.1)
        if st.form_submit_button("Log"):
            save_data("velo", {"Date": date, "Velo": velo})
            st.success("Logged")
            
    df = load_data("velo")
    if not df.empty:
        st.line_chart(df, x="Date", y="Velo")

elif page == "Track Bodyweight":
    st.title("⚖️ Log Bodyweight")
    with st.form("bw"):
        date = st.date_input("Date", datetime.date.today())
        bw = st.number_input("Weight (lbs)", step=0.1)
        if st.form_submit_button("Log"):
            save_data("bodyweight", {"Date": date, "Weight": bw})
            st.success("Logged")
            
    df = load_data("bodyweight")
    if not df.empty:
        st.line_chart(df, x="Date", y="Weight")