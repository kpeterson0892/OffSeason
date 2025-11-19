import streamlit as st
import pandas as pd
import datetime
import os
import ast
import numpy as np

# ==========================================
# 1. CONFIGURATION
# ==========================================
st.set_page_config(page_title="25-26 Off-Season", page_icon="⚾", layout="wide")

# High contrast styling
st.markdown("""
<style>
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        background-color: white;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
    }
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
# 3. FIXED PARSER FOR NIPPARD SHEET
# ==========================================
def parse_nippard_csv(file):
    """
    Parses the Jeff Nippard Powerbuilding CSV structure.
    Adjusted for CSVs where Column A is empty and data starts in Column B.
    """
    # Read without header because the header is messy
    df = pd.read_csv(file, header=None)
    
    extracted_routines = []
    
    current_week = "Week 1" # Default
    current_routine_name = None
    current_exercises = []
    
    # Iterate through every row
    for index, row in df.iterrows():
        # Col A (0) is usually empty in your file
        # Col B (1) contains Week info or Routine Names
        # Col C (2) contains Exercise Names
        
        val_1 = str(row[1]).strip() # Column B
        val_2 = str(row[2]).strip() # Column C (Exercise)
        
        # 1. Detect Week Change (e.g., "Week 1", "Week 2")
        if "Week" in val_1 and len(val_1) < 15:
            current_week = val_1
            continue

        # 2. Detect New Session 
        # It is a session if Col B has text, but it is NOT "Week" and NOT "Exercise"
        # Also ignoring metadata rows
        if val_1 != "nan" and val_1 != "" and "Week" not in val_1 and "Exercise" not in val_1 and "IMPORTANT" not in val_1:
            
            # Save previous routine if exists
            if current_routine_name and current_exercises:
                extracted_routines.append({
                    "Routine Name": current_routine_name,
                    "Type": "Lifting",
                    "Exercises": str(current_exercises)
                })
            
            # Start new routine
            clean_name = val_1.split(":")[0] # Remove description after colon
            current_routine_name = f"{current_week} - {clean_name}"
            current_exercises = []
            
            # CRITICAL: In your sheet, the first exercise is often on the SAME ROW as the routine name (in Col C)
            if val_2 != "nan" and val_2 != "" and val_2 != "Exercise":
                 # Col E (4) = Working Sets, F (5) = Reps, G (6) = Load
                ex_obj = {
                    "Exercise": val_2,
                    "Sets": str(row[4]) if str(row[4]) != "nan" else "3",
                    "Reps": str(row[5]) if str(row[5]) != "nan" else "10",
                    "Weight": str(row[6]) if str(row[6]) != "nan" else "-"
                }
                current_exercises.append(ex_obj)
            continue

        # 3. Detect Exercise Rows (Col B is empty, Col C has exercise)
        if (val_1 == "nan" or val_1 == "") and (val_2 != "nan" and val_2 != ""):
            # Skip headers
            if "Exercise" in val_2 or "Warm-up" in val_2:
                continue
                
            # It's an exercise
            ex_obj = {
                "Exercise": val_2,
                "Sets": str(row[4]) if str(row[4]) != "nan" else "3",
                "Reps": str(row[5]) if str(row[5]) != "nan" else "10",
                "Weight": str(row[6]) if str(row[6]) != "nan" else "-"
            }
            current_exercises.append(ex_obj)

    # Save the final routine found
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
    with col_title: st.title("📅 Daily Plan")
    with col_pick: selected_date = st.date_input("Viewing Date:", datetime.date.today())
    
    view_str = selected_date.strftime("%Y-%m-%d")
    df_sched = load_data("schedule")
    df_routines = load_data("routines")
    df_logs = load_data("logs")

    today_plan = df_sched[df_sched["Date"] == view_str]
    
    if today_plan.empty:
        st.warning(f"No plan found for {view_str}.")
        st.stop()
    plan = today_plan.iloc[0]

    # TOP CARDS
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1:
            st.caption("⚠️ CONSTRAINT")
            st.markdown(f"### {plan['Daily Constraint'] if plan['Daily Constraint'] else 'None'}")
        with c2:
            st.caption("🧠 INTENT")
            st.markdown(f"### {plan['Intent'] if plan['Intent'] else 'None'}")
        if plan['Command Implement']:
            st.caption("🎯 COMMAND")
            st.write(f"**{plan['Command Implement']}**")

    # THROWING
    st.subheader("⚾ Throwing")
    with st.container(border=True):
        t_plan = plan['Throwing Plan']
        if t_plan and t_plan != "Rest":
            st.markdown(f"## {t_plan}")
            m1, m2, m3 = st.columns(3)
            m1.metric("Distance", plan['Long Toss Distance'])
            m2.metric("Mound", plan['Mound Style'])
            m3.metric("Goal Velo", plan['Goal Velocity'])
            
            with st.expander("View Routine"):
                r_row = df_routines[df_routines["Routine Name"] == t_plan]
                if not r_row.empty:
                    try:
                        ex_list = ast.literal_eval(r_row.iloc[0]["Exercises"])
                        st.table(pd.DataFrame(ex_list))
                    except: pass
        else:
            st.markdown("## Rest Day")

    # LIFTING
    st.subheader("🏋️ Strength")
    with st.container(border=True):
        wu = plan['Warm Up']
        if wu or plan['Yoga?'] == "Yes":
            st.markdown(f"**Warm Up:** {wu} {' | 🧘 Yoga' if plan['Yoga?']=='Yes' else ''}")
        
        st.divider()
        l_plan = plan['Lifting Plan']
        
        if l_plan:
            st.markdown(f"## {l_plan}")
            
            # 1. Exact Match Check
            routine_row = df_routines[df_routines["Routine Name"] == l_plan]
            
            # 2. Fuzzy Match / Short Name Check (e.g. User has 'FB1' in schedule but 'Week 1 - Full Body 1' in library)
            if routine_row.empty:
                # Try to find a routine that CONTAINS this text
                mask = df_routines["Routine Name"].str.contains(l_plan, case=False, na=False)
                if mask.any():
                    routine_row = df_routines[mask].iloc[[0]] # Take first match
                    st.info(f"Matched short name '{l_plan}' to '{routine_row.iloc[0]['Routine Name']}'")
            
            if not routine_row.empty:
                try:
                    template_exercises = ast.literal_eval(routine_row.iloc[0]["Exercises"])
                    existing_logs = df_logs[(df_logs["Date"] == view_str) & (df_logs["Routine Name"] == l_plan)]
                    
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
                    
                    edited_df = st.data_editor(pd.DataFrame(display_rows), hide_index=True, use_container_width=True)
                    
                    if st.button("💾 Save Lift"):
                        df_clean = df_logs[~((df_logs["Date"] == view_str) & (df_logs["Routine Name"] == l_plan))]
                        new_rows = []
                        for _, row in edited_df.iterrows():
                            new_rows.append({
                                "Date": view_str, "Routine Name": l_plan, "Exercise": row["Exercise"],
                                "Set #": 1, "Prescribed Weight": row["Target"], "Actual Weight": row["Actual Wt"], "Actual Reps": 0
                            })
                        save_data("logs", pd.concat([df_clean, pd.DataFrame(new_rows)], ignore_index=True))
                        st.success("Saved!")
                except: st.error("Error parsing routine.")
            else:
                st.warning(f"Routine '{l_plan}' not found. Check 'Routine Library' to see exact names.")
        else:
            st.markdown("## Rest Day")

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
    
    st.subheader("Delete Routine")
    d_sel = st.selectbox("Select Routine", df["Routine Name"].unique())
    if st.button("Delete Selected"):
        df_new = df[df["Routine Name"] != d_sel]
        save_data("routines", df_new)
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
                else:
                    st.warning("No routines found. Check CSV format.")
            except Exception as e: st.error(f"Error parsing: {e}")
