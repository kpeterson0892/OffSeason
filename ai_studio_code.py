import streamlit as st
import pandas as pd
import datetime
import calendar
import os
import ast

# ==========================================
# 1. APPLE / IOS STYLING CONFIGURATION
# ==========================================
st.set_page_config(page_title="Ace Performance", page_icon="⚾", layout="wide")

# This CSS injects the "Apple Look" (Rounded corners, soft shadows, SF Font)
apple_css = """
<style>
    /* Main Background - iOS Light Gray */
    .stApp {
        background-color: #F2F2F7;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Card Styling (Like iOS Widgets) */
    .css-card {
        background-color: #FFFFFF;
        border-radius: 18px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #1C1C1E;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* Inputs (Rounded Gray Fields) */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        border-radius: 10px;
        background-color: #E5E5EA; /* iOS Input Gray */
        border: none;
        color: #000;
    }
    
    /* Buttons (Apple Blue Pills) */
    .stButton button {
        background-color: #007AFF;
        color: white;
        border-radius: 20px;
        border: none;
        font-weight: 600;
        padding: 0.5rem 1rem;
        box-shadow: 0 2px 5px rgba(0,122,255,0.2);
        transition: all 0.2s;
    }
    .stButton button:hover {
        background-color: #005ECB;
        transform: scale(1.02);
    }
    
    /* Remove Streamlit default decoration */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom container for dashboard stats */
    .stat-box {
        text-align: center;
        padding: 10px;
        border-radius: 14px;
        background: #F2F2F7;
        margin: 5px;
    }
    .stat-val { font-size: 24px; font-weight: bold; color: #007AFF; }
    .stat-label { font-size: 12px; color: #8E8E93; font-weight: 600; text-transform: uppercase; }

</style>
"""
st.markdown(apple_css, unsafe_allow_html=True)

# ==========================================
# 2. DATA HANDLING
# ==========================================
FILES = {
    "schedule": "schedule_data.csv",
    "routines": "routines_library.csv",
    "lifts": "lift_data.csv",
    "velo": "velo_data.csv",
    "bodyweight": "bw_data.csv"
}

def load_data(key):
    if not os.path.exists(FILES[key]):
        if key == "routines":
            return pd.DataFrame(columns=["Routine Name", "Type", "Exercises"])
        elif key == "schedule":
            # Create a default schedule for the current year to make the calendar editor work
            dates = pd.date_range(start=f"{datetime.date.today().year}-01-01", end=f"{datetime.date.today().year}-12-31")
            df = pd.DataFrame({"Date": dates})
            df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
            df["Throwing Routine"] = "Rest Day"
            df["Lifting Routine"] = "Rest Day"
            df["Custom Notes"] = ""
            return df
        elif key == "lifts":
            return pd.DataFrame(columns=["Date", "Exercise", "Weight", "Reps"])
        elif key == "velo":
            return pd.DataFrame(columns=["Date", "Velo"])
        elif key == "bodyweight":
            return pd.DataFrame(columns=["Date", "Weight"])
        return pd.DataFrame()
    
    df = pd.read_csv(FILES[key])
    # Ensure schedule has all dates if loaded from CSV (fill gaps)
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
# 3. NAVIGATION
# ==========================================
# Using Columns as a top navigation bar for a more "App-like" feel
col_nav1, col_nav2, col_nav3, col_nav4 = st.columns(4)
with col_nav1:
    if st.button("📅 Dashboard", use_container_width=True): st.session_state.page = "Dashboard"
with col_nav2:
    if st.button("🗓️ Planner", use_container_width=True): st.session_state.page = "Planner"
with col_nav3:
    if st.button("🛠️ Routines", use_container_width=True): st.session_state.page = "Routines"
with col_nav4:
    if st.button("📈 Tracking", use_container_width=True): st.session_state.page = "Tracking"

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

page = st.session_state.page

# ==========================================
# PAGE: DASHBOARD (The "Today" View)
# ==========================================
if page == "Dashboard":
    st.title(f"Today")
    st.markdown(f"<h3 style='color: #8E8E93; margin-top: -20px;'>{datetime.date.today().strftime('%A, %B %d')}</h3>", unsafe_allow_html=True)
    
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    df_sched = load_data("schedule")
    df_routines = load_data("routines")
    
    # Get today's plan
    today_plan = df_sched[df_sched["Date"] == today_str]
    
    if not today_plan.empty:
        plan = today_plan.iloc[0]
        throw_name = plan.get("Throwing Routine", "Rest Day")
        lift_name = plan.get("Lifting Routine", "Rest Day")
        note = plan.get("Custom Notes", "")
    else:
        throw_name = "Rest Day"
        lift_name = "Rest Day"
        note = ""

    # --- THROWING CARD ---
    with st.container():
        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        st.subheader("⚾ Throwing")
        if throw_name == "Rest Day" or pd.isna(throw_name):
            st.write("Recovery / Rest Day")
        else:
            st.write(f"**Routine:** {throw_name}")
            row = df_routines[df_routines["Routine Name"] == throw_name]
            if not row.empty and "Exercises" in row.columns:
                try:
                    ex_list = ast.literal_eval(row.iloc[0]["Exercises"])
                    st.dataframe(pd.DataFrame(ex_list), hide_index=True, use_container_width=True)
                except: st.write("No details found.")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- LIFTING CARD ---
    with st.container():
        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        st.subheader("🏋️ Lifting")
        if lift_name == "Rest Day" or pd.isna(lift_name):
            st.write("Recovery / Rest Day")
        else:
            st.write(f"**Routine:** {lift_name}")
            row = df_routines[df_routines["Routine Name"] == lift_name]
            if not row.empty and "Exercises" in row.columns:
                try:
                    ex_list = ast.literal_eval(row.iloc[0]["Exercises"])
                    st.dataframe(pd.DataFrame(ex_list), hide_index=True, use_container_width=True)
                except: st.write("No details found.")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- NOTES CARD ---
    if note and not pd.isna(note):
        st.info(f"📝 **Note:** {note}")


# ==========================================
# PAGE: VISUAL PLANNER (The Month Editor)
# ==========================================
elif page == "Planner":
    st.title("🗓️ Schedule")
    st.markdown("Select the month, then click the table cells to assign routines from the dropdowns.")
    
    df_routines = load_data("routines")
    df_sched = load_data("schedule")
    
    # Create dropdown options
    if not df_routines.empty:
        throw_opts = ["Rest Day"] + df_routines[df_routines["Type"] == "Throwing"]["Routine Name"].unique().tolist()
        lift_opts = ["Rest Day"] + df_routines[df_routines["Type"] == "Lifting"]["Routine Name"].unique().tolist()
    else:
        throw_opts = ["Rest Day"]
        lift_opts = ["Rest Day"]

    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Filter by Month
        view_month = st.date_input("Jump to Date", datetime.date.today())
        start_date = view_month.replace(day=1)
        end_date = (start_date + pd.DateOffset(months=1)) - pd.DateOffset(days=1)
        
        st.caption("Tips: You can copy-paste rows in the table or drag the handle on the bottom right of a cell to fill down!")

    with col2:
        # Filter dataframe for this month
        mask = (pd.to_datetime(df_sched['Date']) >= pd.to_datetime(start_date)) & \
               (pd.to_datetime(df_sched['Date']) <= pd.to_datetime(end_date))
        
        df_view = df_sched.loc[mask].copy()
        
        # CONFIG: Make the columns dropdowns using st.column_config
        edited_df = st.data_editor(
            df_view,
            column_config={
                "Date": st.column_config.TextColumn(disabled=True), # Lock date
                "Throwing Routine": st.column_config.SelectboxColumn(
                    "Throwing",
                    options=throw_opts,
                    required=True,
                    width="medium"
                ),
                "Lifting Routine": st.column_config.SelectboxColumn(
                    "Lifting",
                    options=lift_opts,
                    required=True,
                    width="medium"
                ),
                "Custom Notes": st.column_config.TextColumn("Notes")
            },
            hide_index=True,
            use_container_width=True,
            height=600,
            key="scheduler_editor"
        )

        if st.button("💾 Save Schedule Changes"):
            # Update the main dataframe with changes
            df_sched.set_index("Date", inplace=True)
            edited_df.set_index("Date", inplace=True)
            df_sched.update(edited_df)
            df_sched.reset_index(inplace=True)
            save_data("schedule", df_sched)
            st.success("Schedule Updated!")


# ==========================================
# PAGE: ROUTINE BUILDER (Apple Style)
# ==========================================
elif page == "Routines":
    st.title("🛠️ Routines")
    
    tab1, tab2 = st.tabs(["Create", "Library"])
    
    with tab1:
        st.markdown("<div class='css-card'>", unsafe_allow_html=True)
        st.subheader("New Routine")
        
        if "new_routine_rows" not in st.session_state:
            st.session_state.new_routine_rows = []

        # Input Row
        c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
        ex = c1.text_input("Exercise")
        s = c2.text_input("Sets")
        r = c3.text_input("Reps")
        w = c4.text_input("Weight/RPE")
        
        if st.button("➕ Add Exercise"):
            if ex:
                st.session_state.new_routine_rows.append({"Exercise": ex, "Sets": s, "Reps": r, "Weight": w})

        # Preview Table
        if st.session_state.new_routine_rows:
            st.markdown("---")
            preview_df = pd.DataFrame(st.session_state.new_routine_rows)
            edited_preview = st.data_editor(preview_df, num_rows="dynamic", use_container_width=True)
            
            col_name, col_type, col_save = st.columns([2, 1, 1])
            r_name = col_name.text_input("Routine Name", placeholder="e.g. Leg Day A")
            r_type = col_type.selectbox("Type", ["Lifting", "Throwing"])
            
            if col_save.button("Save Routine"):
                if r_name:
                    final_data = edited_preview.to_dict('records')
                    append_data("routines", {
                        "Routine Name": r_name, "Type": r_type, "Exercises": str(final_data)
                    })
                    st.success(f"Saved {r_name}!")
                    st.session_state.new_routine_rows = []
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        df_lib = load_data("routines")
        if not df_lib.empty:
            for index, row in df_lib.iterrows():
                st.markdown("<div class='css-card'>", unsafe_allow_html=True)
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"### {row['Routine Name']}")
                c1.caption(row['Type'])
                
                if c2.button("🗑️", key=f"del_{index}"):
                    df_lib = df_lib.drop(index)
                    save_data("routines", df_lib)
                    st.rerun()
                    
                with st.expander("View Exercises"):
                    try:
                        ex_data = ast.literal_eval(row["Exercises"])
                        st.table(pd.DataFrame(ex_data))
                    except: st.write("Error loading details.")
                st.markdown("</div>", unsafe_allow_html=True)


# ==========================================
# PAGE: TRACKING (Clean Metrics)
# ==========================================
elif page == "Tracking":
    st.title("📈 Progress")
    
    # Apple Health Style Top Cards
    df_velo = load_data("velo")
    df_lifts = load_data("lifts")
    df_bw = load_data("bodyweight")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        max_v = df_velo["Velo"].max() if not df_velo.empty else 0
        st.markdown(f"<div class='stat-box'><div class='stat-val'>{max_v} MPH</div><div class='stat-label'>Top Velo</div></div>", unsafe_allow_html=True)
    with c2:
        curr_bw = df_bw.iloc[-1]["Weight"] if not df_bw.empty else 0
        st.markdown(f"<div class='stat-box'><div class='stat-val'>{curr_bw} lbs</div><div class='stat-label'>Bodyweight</div></div>", unsafe_allow_html=True)
    with c3:
        lifts_logged = len(df_lifts)
        st.markdown(f"<div class='stat-box'><div class='stat-val'>{lifts_logged}</div><div class='stat-label'>Sets Logged</div></div>", unsafe_allow_html=True)

    st.markdown("---")

    # Logging Area
    tab_l, tab_v, tab_b = st.tabs(["Lifts", "Velocity", "Bodyweight"])
    
    with tab_l:
        with st.form("log_lift"):
            c1, c2, c3 = st.columns(3)
            l_date = c1.date_input("Date")
            l_ex = c2.text_input("Exercise")
            l_wt = c3.number_input("Weight", step=5)
            if st.form_submit_button("Log Lift"):
                append_data("lifts", {"Date": l_date, "Exercise": l_ex, "Weight": l_wt, "Reps": 0})
                st.success("Logged")
        
        if not df_lifts.empty:
            st.line_chart(df_lifts, x="Date", y="Weight")

    with tab_v:
        with st.form("log_velo"):
            c1, c2 = st.columns(2)
            v_date = c1.date_input("Date")
            v_mph = c2.number_input("MPH", step=0.1)
            if st.form_submit_button("Log Velo"):
                append_data("velo", {"Date": v_date, "Velo": v_mph})
                st.success("Logged")
        if not df_velo.empty:
            st.line_chart(df_velo, x="Date", y="Velo")
            
    with tab_b:
        with st.form("log_bw"):
            c1, c2 = st.columns(2)
            b_date = c1.date_input("Date")
            b_lbs = c2.number_input("Weight", step=0.1)
            if st.form_submit_button("Log Weight"):
                append_data("bodyweight", {"Date": b_date, "Weight": b_lbs})
                st.success("Logged")
        if not df_bw.empty:
            st.line_chart(df_bw, x="Date", y="Weight")
