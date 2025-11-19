import streamlit as st
import pandas as pd
import datetime
import os
import ast # Safe way to read lists stored as strings in CSV

# --- CONFIGURATION ---
st.set_page_config(page_title="Ace Performance", page_icon="⚾", layout="wide")

# --- DATA FILES ---
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
        if key == "routines":
            # Structure: Routine Name | Type | Exercises (List of Dicts)
            return pd.DataFrame(columns=["Routine Name", "Type", "Exercises"])
        elif key == "schedule":
            return pd.DataFrame(columns=["Date", "Throwing Routine", "Lifting Routine", "Custom Notes"])
        return pd.DataFrame()
    return pd.read_csv(FILES[key])

def save_full_dataframe(key, df):
    """Overwrites the entire CSV with the new dataframe (used for edits/deletes)"""
    df.to_csv(FILES[key], index=False)

def append_data(key, new_row_dict):
    """Appends a single row to the CSV"""
    df = load_data(key)
    new_df = pd.DataFrame([new_row_dict])
    updated_df = pd.concat([df, new_df], ignore_index=True)
    updated_df.to_csv(FILES[key], index=False)

# --- SIDEBAR ---
st.sidebar.title("⚾ Ace Performance")
page = st.sidebar.radio("Menu", [
    "Daily Dashboard", 
    "Routine Manager",   # Renamed
    "Assign Schedule",   
    "Track Lifts", 
    "Track Velocity", 
    "Track Bodyweight"
])

# ==========================================
# PAGE: ROUTINE MANAGER (Create / Edit / Delete)
# ==========================================
if page == "Routine Manager":
    st.title("🛠️ Routine Manager")
    
    tab1, tab2 = st.tabs(["➕ Create New", "✏️ Edit / Delete"])

    # --- TAB 1: CREATE NEW ROUTINE ---
    with tab1:
        st.subheader("Build a New Routine")
        
        # We use a temporary dataframe in session state to build the list
        if "new_routine_rows" not in st.session_state:
            st.session_state.new_routine_rows = []

        # 1. Add Exercises Form
        with st.expander("Add Exercise Inputs", expanded=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            ex_name = c1.text_input("Exercise Name", key="new_ex")
            sets = c2.text_input("Sets", key="new_sets")
            reps = c3.text_input("Reps", key="new_reps")
            
            c4, c5, c6 = st.columns([1, 1, 1])
            weight = c4.text_input("Weight", key="new_weight")
            rpe = c5.text_input("RPE", key="new_rpe")
            tempo = c6.text_input("Tempo", key="new_tempo")

            if st.button("Add to List"):
                if ex_name:
                    st.session_state.new_routine_rows.append({
                        "Exercise": ex_name, "Sets": sets, "Reps": reps, 
                        "Weight": weight, "RPE": rpe, "Tempo": tempo
                    })
                else:
                    st.error("Exercise Name is required.")

        # 2. Preview & Save
        if len(st.session_state.new_routine_rows) > 0:
            st.write("### Preview (You can edit this table directly before saving)")
            
            # Create a DataFrame from the list
            df_preview = pd.DataFrame(st.session_state.new_routine_rows)
            
            # Allow user to edit the preview (delete rows, fix typos)
            edited_df = st.data_editor(df_preview, num_rows="dynamic", key="create_editor")

            st.divider()
            col_a, col_b = st.columns(2)
            with col_a:
                r_name = st.text_input("Routine Name (e.g., Upper Hypertrophy)")
            with col_b:
                r_type = st.selectbox("Routine Type", ["Lifting", "Throwing"])

            if st.button("💾 Save New Routine"):
                if r_name:
                    # Convert the edited dataframe back to a list of dicts
                    final_exercises = edited_df.to_dict('records')
                    
                    append_data("routines", {
                        "Routine Name": r_name,
                        "Type": r_type,
                        "Exercises": str(final_exercises) # Save as string
                    })
                    st.success(f"Saved '{r_name}'!")
                    st.session_state.new_routine_rows = [] # Clear form
                    st.rerun()
                else:
                    st.error("Please name the routine.")

    # --- TAB 2: EDIT / DELETE EXISTING ---
    with tab2:
        st.subheader("Manage Existing Routines")
        
        df_library = load_data("routines")
        
        if df_library.empty:
            st.info("No routines found. Go to 'Create New' first.")
        else:
            # Select Routine
            routine_names = df_library["Routine Name"].unique()
            selected_routine_name = st.selectbox("Select Routine to Edit", routine_names)
            
            # Get the row for this routine
            current_row = df_library[df_library["Routine Name"] == selected_routine_name].iloc[0]
            
            # Parse the exercises string back into a list/dataframe
            try:
                current_exercises = ast.literal_eval(current_row["Exercises"])
                df_exercises = pd.DataFrame(current_exercises)
            except:
                df_exercises = pd.DataFrame(columns=["Exercise", "Sets", "Reps"])

            st.write(f"**Editing:** {selected_routine_name} ({current_row['Type']})")
            
            # EDITABLE TABLE
            # num_rows="dynamic" allows you to add or delete rows directly in the UI
            updated_exercises_df = st.data_editor(
                df_exercises, 
                num_rows="dynamic", 
                use_container_width=True,
                key="edit_editor"
            )
            
            col_save, col_del = st.columns([1, 1])
            
            # UPDATE BUTTON
            with col_save:
                if st.button("✅ Update Routine"):
                    # Convert back to list of dicts
                    updated_list = updated_exercises_df.to_dict('records')
                    
                    # Update the specific row in the main dataframe
                    df_library.loc[df_library["Routine Name"] == selected_routine_name, "Exercises"] = str(updated_list)
                    
                    # Save to CSV
                    save_full_dataframe("routines", df_library)
                    st.success("Routine updated successfully!")
            
            # DELETE BUTTON
            with col_del:
                if st.button("🗑️ Delete Routine", type="primary"):
                    # Filter out the selected routine
                    df_library = df_library[df_library["Routine Name"] != selected_routine_name]
                    save_full_dataframe("routines", df_library)
                    st.success(f"Deleted {selected_routine_name}")
                    st.rerun()

# ==========================================
# PAGE: ASSIGN SCHEDULE
# ==========================================
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
            # Simple append logic (The dashboard always reads the LAST entry for a specific date)
            append_data("schedule", {
                "Date": date,
                "Throwing Routine": selected_throw,
                "Lifting Routine": selected_lift,
                "Custom Notes": notes
            })
            st.success(f"Schedule updated for {date}")

# ==========================================
# PAGE: DAILY DASHBOARD
# ==========================================
elif page == "Daily Dashboard":
    st.title("📅 Today's Training")
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    df_sched = load_data("schedule")
    df_routines = load_data("routines")
    
    today_plan = df_sched[df_sched["Date"] == today_str]
    
    if not today_plan.empty:
        plan = today_plan.iloc[-1] 
        
        # --- LIFTING ---
        st.markdown(f"### 🏋️ Lifting: {plan['Lifting Routine']}")
        if plan['Lifting Routine'] != "Rest Day":
            row = df_routines[df_routines["Routine Name"] == plan['Lifting Routine']]
            if not row.empty:
                ex_list = ast.literal_eval(row.iloc[0]["Exercises"])
                st.table(pd.DataFrame(ex_list))
            else:
                st.error("Routine not found (it might have been deleted).")
        
        st.divider()

        # --- THROWING ---
        st.markdown(f"### ⚾ Throwing: {plan['Throwing Routine']}")
        if plan['Throwing Routine'] != "Rest Day":
            row = df_routines[df_routines["Routine Name"] == plan['Throwing Routine']]
            if not row.empty:
                ex_list = ast.literal_eval(row.iloc[0]["Exercises"])
                st.table(pd.DataFrame(ex_list))
            else:
                st.error("Routine not found.")

        if pd.notna(plan['Custom Notes']) and plan['Custom Notes']:
            st.info(f"📝 **Coach Notes:** {plan['Custom Notes']}")

    else:
        st.info("No workout scheduled for today.")

# ==========================================
# PAGE: TRACKING (Lifts, Velo, Bodyweight)
# ==========================================
elif page == "Track Lifts":
    st.title("🏋️ Log Lifts")
    with st.form("lift"):
        date = st.date_input("Date", datetime.date.today())
        exercise = st.text_input("Exercise Name") 
        weight = st.number_input("Weight Used", step=2.5)
        reps = st.number_input("Reps Performed", step=1)
        if st.form_submit_button("Log Set"):
            append_data("lifts", {"Date": date, "Exercise": exercise, "Weight": weight, "Reps": reps})
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
            append_data("velo", {"Date": date, "Velo": velo})
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
            append_data("bodyweight", {"Date": date, "Weight": bw})
            st.success("Logged")
    df = load_data("bodyweight")
    if not df.empty:
        st.line_chart(df, x="Date", y="Weight")
