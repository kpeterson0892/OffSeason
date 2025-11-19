import streamlit as st
import pandas as pd
import datetime
import os
import ast # Safe way to read lists stored as strings in CSV

# --- CONFIGURATION ---
st.set_page_config(page_title="Ace Performance", page_icon="⚾", layout="wide")

# --- DATA FILES ---
# We use CSVs for simplicity. In a real app, these would be database connections.
FILES = {
    "schedule": "schedule_data.csv",
    "routines": "routines_library.csv",
    "lifts": "lift_data.csv",
    "velo": "velo_data.csv",
    "bodyweight": "bw_data.csv"
}

# --- FUNCTIONS ---
def load_data(key):
    if not os.path.exists(FILES[key]):
        # Initialize empty dataframes with correct columns
        if key == "routines":
            return pd.DataFrame(columns=["Routine Name", "Type", "Exercises"]) # 'Exercises' will hold a list of dicts
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
    "Routine Builder",   
    "Assign Schedule",   
    "Track Lifts", 
    "Track Velocity", 
    "Track Bodyweight"
])

# --- 1. ROUTINE BUILDER (UPDATED) ---
if page == "Routine Builder":
    st.title("🛠️ Create Standard Routines")
    st.info("Build a routine by adding exercises one by one. When finished, give it a name and save.")

    # Session State to hold the current routine being built
    if "current_routine" not in st.session_state:
        st.session_state.current_routine = []

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Add Exercise")
        with st.form("add_exercise"):
            ex_name = st.text_input("Exercise Name", placeholder="e.g. Back Squat")
            c1, c2 = st.columns(2)
            sets = c1.text_input("Sets", placeholder="3")
            reps = c2.text_input("Reps", placeholder="5")
            c3, c4 = st.columns(2)
            weight = c3.text_input("Weight/Intensity", placeholder="75% or 225lbs")
            rpe = c4.text_input("RPE", placeholder="8")
            tempo = st.text_input("Tempo", placeholder="3-0-X-1")
            
            add_btn = st.form_submit_button("Add to List")
            
            if add_btn and ex_name:
                st.session_state.current_routine.append({
                    "Exercise": ex_name,
                    "Sets": sets,
                    "Reps": reps,
                    "Weight": weight,
                    "RPE": rpe,
                    "Tempo": tempo
                })
                st.success(f"Added {ex_name}")

    with col2:
        st.subheader("Current Routine Preview")
        if len(st.session_state.current_routine) > 0:
            # Show what we have so far as a table
            preview_df = pd.DataFrame(st.session_state.current_routine)
            st.table(preview_df)
            
            # Save the whole routine
            with st.form("save_routine"):
                r_name = st.text_input("Routine Name (e.g. Hypertrophy A)")
                r_type = st.selectbox("Type", ["Lifting", "Throwing"])
                save_btn = st.form_submit_button("💾 Save Routine to Library")
                
                if save_btn and r_name:
                    # Convert list of dicts to string to store in CSV
                    exercises_str = str(st.session_state.current_routine)
                    save_data("routines", {
                        "Routine Name": r_name,
                        "Type": r_type,
                        "Exercises": exercises_str
                    })
                    st.success(f"Saved Routine: {r_name}")
                    # Reset
                    st.session_state.current_routine = []
                    st.rerun()
        else:
            st.write("No exercises added yet.")

    st.divider()
    st.subheader("Existing Library")
    df_lib = load_data("routines")
    if not df_lib.empty:
        st.dataframe(df_lib[["Routine Name", "Type"]])


# --- 2. ASSIGN SCHEDULE (SAME AS BEFORE) ---
elif page == "Assign Schedule":
    st.title("🗓️ Plan Your Month")
    
    df_routines = load_data("routines")
    
    if not df_routines.empty:
        lift_options = ["Rest Day"] + df_routines[df_routines["Type"] == "Lifting"]["Routine Name"].unique().tolist()
        throw_options = ["Rest Day"] + df_routines[df_routines["Type"] == "Throwing"]["Routine Name"].unique().tolist()
    else:
        lift_options = ["Rest Day"]
        throw_options = ["Rest Day"]

    with st.form("assign_form"):
        date = st.date_input("Select Date", datetime.date.today())
        col1, col2 = st.columns(2)
        with col1:
            selected_throw = st.selectbox("Throwing Plan", throw_options)
        with col2:
            selected_lift = st.selectbox("Lifting Plan", lift_options)
        notes = st.text_input("Custom Notes")
        
        if st.form_submit_button("Assign"):
            save_data("schedule", {
                "Date": date,
                "Throwing Routine": selected_throw,
                "Lifting Routine": selected_lift,
                "Custom Notes": notes
            })
            st.success(f"Schedule updated for {date}")


# --- 3. DAILY DASHBOARD (UPDATED FOR STRUCTURED DATA) ---
elif page == "Daily Dashboard":
    st.title("📅 Today's Training")
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    df_sched = load_data("schedule")
    df_routines = load_data("routines")
    
    today_plan = df_sched[df_sched["Date"] == today_str]
    
    if not today_plan.empty:
        plan = today_plan.iloc[-1] 
        
        # --- LIFTING SECTION ---
        st.markdown(f"### 🏋️ Lifting: {plan['Lifting Routine']}")
        if plan['Lifting Routine'] != "Rest Day":
            # Find the routine data
            row = df_routines[df_routines["Routine Name"] == plan['Lifting Routine']]
            if not row.empty:
                # Parse the string representation of list back into a list
                ex_list = ast.literal_eval(row.iloc[0]["Exercises"])
                st.table(pd.DataFrame(ex_list))
            else:
                st.error("Routine not found in library.")
        
        st.divider()

        # --- THROWING SECTION ---
        st.markdown(f"### ⚾ Throwing: {plan['Throwing Routine']}")
        if plan['Throwing Routine'] != "Rest Day":
            row = df_routines[df_routines["Routine Name"] == plan['Throwing Routine']]
            if not row.empty:
                ex_list = ast.literal_eval(row.iloc[0]["Exercises"])
                st.table(pd.DataFrame(ex_list))
            else:
                st.error("Routine not found in library.")

        if pd.notna(plan['Custom Notes']) and plan['Custom Notes']:
            st.warning(f"📝 **Coach Notes:** {plan['Custom Notes']}")

    else:
        st.info("No workout scheduled for today.")


# --- 4. TRACKING PAGES (Standard) ---
elif page == "Track Lifts":
    st.title("🏋️ Log Lifts")
    with st.form("lift"):
        date = st.date_input("Date", datetime.date.today())
        # In a real app, we could dynamically populate this list from your Routine Builder exercises
        exercise = st.text_input("Exercise Name") 
        weight = st.number_input("Weight Used", step=2.5)
        reps = st.number_input("Reps Performed", step=1)
        if st.form_submit_button("Log Set"):
            save_data("lifts", {"Date": date, "Exercise": exercise, "Weight": weight, "Reps": reps})
            st.success("Logged")
            
    df = load_data("lifts")
    if not df.empty:
        st.subheader("History")
        st.dataframe(df.sort_values("Date", ascending=False))

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
