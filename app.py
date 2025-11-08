# app.py

import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
import re  # <-- Added new import for validation

# --- Authentication and Database Imports ---
import database as db
import auth

# --- Backend Function Import ---
from backend import run_analysis 

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="FinOpti AI",
    #page_icon="💡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- FILE PATHS ---
DATA_FILE_PATH = os.path.join("data", "final.xlsx")
OUTPUT_DIR = "outputs"
ASSETS_DIR = "assets"
BACKGROUND_IMAGE_PATH = os.path.join(ASSETS_DIR, "bg_img.png")
LOGIN_BACKGROUND_IMAGE_PATH = os.path.join(ASSETS_DIR, "login.png") # <-- Added new path

# --- HELPER FUNCTIONS ---
@st.cache_data
def get_bank_list(file_path):
    try:
        df = pd.read_excel(file_path, sheet_name="Final")
        return sorted(df['Banks'].astype(str).str.strip().unique()) if 'Banks' in df.columns else []
    except Exception:
        return []

# --- NEW: HELPER FUNCTIONS FOR THE ADVANCED LOGIN PAGE ---
def set_login_style(image_file):
    with open(image_file, "rb") as f:
        img_data = f.read()
    b64_encoded = base64.b64encode(img_data).decode()
    style = f"""
        <style>
        .stApp {{
            background-image: url(data:image/png;base64,{b64_encoded});
            background-size: cover; background-repeat: no-repeat; background-attachment: fixed;
        }}
        [data-testid="stHeader"], [data-testid="stToolbar"] {{ background: none; }}
        div[data-testid="stHorizontalBlock"] > div:nth-child(2) > div[data-testid="stVerticalBlock"] {{
            background: rgba(40, 40, 50, 0.6); backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px;
            padding: 2.5rem; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        }}
        h1, h3, label, p, a {{ color: #FFFFFF !important; }}
        div[data-testid="stTextInput"] svg {{ fill: #6c757d; }}
        </style>
    """
    st.markdown(style, unsafe_allow_html=True)

def is_valid_gmail(email):
    if not email or not email.endswith('@gmail.com'): return False
    return re.match(r'^[a-zA-Z0-9._%+-]+@gmail\.com$', email) is not None

def is_strong_password(password):
    if len(password) < 8: return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password): return False, "Password must contain an uppercase letter."
    if not re.search(r'[a-z]', password): return False, "Password must contain a lowercase letter."
    if not re.search(r'[0-9]', password): return False, "Password must contain a number."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password): return False, "Password must contain a special character."
    return True, "Password is strong."
# --- END OF NEW HELPERS ---

# --- THIS IS THE ONLY FUNCTION TO MODIFY ---

def set_background(image_file):
    with open(image_file, "rb") as f:
        img_data = f.read()
    b64_encoded = base64.b64encode(img_data).decode()
    style = f"""
        <style>
        /* This targets the header container */
        [data-testid="stHeader"] {{
            background: none;
        }}

        /* This targets the toolbar buttons inside the header */
        [data-testid="stToolbar"] {{
            right: 2rem;
        }}

        .stApp {{
            background-image: url(data:image/png;base64,{b64_encoded});
            background-size: cover; background-repeat: no-repeat; background-attachment: fixed;
        }}
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] small, [data-testid="stSidebar"] li {{
            color: #262730 !important;
        }}
        .stApp h1, .stApp h3, .stApp p, .stApp .stMarkdown, .stApp label {{ color: #FFFFFF; }}
        .main-title-container {{ text-align: center; padding-bottom: 2rem; }}
        div[data-testid="stSelectbox"], div[data-testid="stNumberInput"] {{
            background-color: rgba(10, 23, 41, 0.7); border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 10px; padding: 0.5rem 1rem;
        }}
        div[data-testid="stSelectbox"] > div, div[data-testid="stNumberInput"] > div {{ border: none; }}
        .run-button-container button {{
            border: 2px solid #FFFFFF !important; background-color: transparent !important;
            color: #FFFFFF !important; transition: all 0.2s ease-in-out;
        }}
        .run-button-container button:hover {{ background-color: rgba(255, 255, 255, 0.15) !important; }}
        </style>
    """
    st.markdown(style, unsafe_allow_html=True)

# --- NEW LOGIN / SIGNUP PAGE ---
def login_signup_page():
    set_login_style(LOGIN_BACKGROUND_IMAGE_PATH)
    st.markdown("<br>", unsafe_allow_html=True)
    _ , col, _ = st.columns([3, 2, 3]) 
    with col:
        st.markdown("<h1 style='text-align: center;'>FinOpti AI</h1>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        login_tab, signup_tab = st.tabs(["Sign In", "Create Account"])
        with login_tab:
            username = st.text_input("Email", key="login_username", placeholder="Email", label_visibility="collapsed")
            password = st.text_input("Password", type="password", key="login_password", placeholder="Password", label_visibility="collapsed")
            st.caption("[Forgot password?](#)") 
            if st.button("Log In", use_container_width=True, type="primary"):
                stored_hash = db.check_user(username)
                if stored_hash and auth.verify_password(stored_hash, password):
                    st.session_state.update(authenticated=True, username=username, run_clicked=False, results=None, error=None)
                    st.rerun()
                else: st.error("Incorrect email or password.")
        with signup_tab:
            new_username = st.text_input("Email", key="signup_username", placeholder="your@email.com", label_visibility="collapsed")
            new_password = st.text_input("Choose a password", type="password", key="signup_password", placeholder="Choose a password", label_visibility="collapsed")
            st.markdown("""<p style='color: rgba(255, 255, 255, 0.8); font-size: 0.8rem; text-align: left;'>
            Password must contain:<br>- At least 8 characters<br>- An uppercase and a lowercase letter<br>- A number and a special character (!@#$ etc.)</p>""", unsafe_allow_html=True)
            if st.button("Create Account", use_container_width=True, type="primary"):
                is_strong, message = is_strong_password(new_password)
                if not new_username or not new_password: st.warning("Please fill out all fields.")
                elif not is_valid_gmail(new_username): st.error("Invalid email. Please use a valid @gmail.com address.")
                elif not is_strong: st.error(message) 
                else:
                    if db.add_user(new_username, auth.hash_password(new_password)): st.success("Account created! Please sign in.")
                    else: st.error("Email already exists.")
# --- END OF NEW LOGIN PAGE ---

def logout():
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.run_clicked = False
    st.session_state.active_tab = "chart"

def set_active_tab(tab_name):
    st.session_state.active_tab = tab_name

# --- MAIN APPLICATION VIEW (UNCHANGED) ---
def show_main_app():
    if not st.session_state.run_clicked:
        set_background(BACKGROUND_IMAGE_PATH)
        st.sidebar.success(f"Logged in as **{st.session_state.username}**")
        st.sidebar.button("Logout", on_click=logout, use_container_width=True)
        _, main_content_col, _ = st.columns([1, 3, 1])
        with main_content_col:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown('<div class="main-title-container"><h1>FinOpti AI</h1><h3>Your AI-Powered Financial Planning Co-pilot.</h3></div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([3, 1, 1])
            selected_bank = col1.selectbox("Select Institution", get_bank_list(DATA_FILE_PATH), index=None, placeholder="Select...", label_visibility="visible")
            current_year = col2.number_input("Current Year", min_value=2010, max_value=2100, value=datetime.now().year, label_visibility="visible")
            forecast_horizon = col3.number_input("Forecast Years", min_value=1, max_value=10, value=3, label_visibility="visible")
            st.markdown("<br><br>", unsafe_allow_html=True)
            if st.button("Generate Forecast", type="primary", use_container_width=True, disabled=(not selected_bank)):
                st.session_state.update(run_clicked=True, selected_bank=selected_bank, active_tab="chart")
                with st.spinner(f"Running analysis for {selected_bank}..."):
                    try: st.session_state.results = run_analysis(DATA_FILE_PATH, selected_bank, forecast_horizon, current_year, OUTPUT_DIR)
                    except Exception as e: st.session_state.error = str(e)
                st.rerun()
    

    else:
        # --- Custom CSS for the Results Page, including the new Header Grid ---
        st.markdown("""
            <style>
            .stApp { background: #FFFFFF; }
            .kpi-container .st-emotion-cache-12w0qpk { border: 1px solid black !important; }
            .rainbow-divider { height: 3px; background: linear-gradient(to right, #86A8E7, #7F7FD5, #91EAE4); margin-bottom: 2rem; }
            h1, h2, h3, p, label { color: #262730 !important; }
            [data-testid="stToolbar"] { display: none !important; }

            /* --- NEW CSS FOR THE CUSTOM HEADER --- */
            .custom-header {
                display: grid;
                grid-template-columns: 1fr 3fr; /* 1 part for button, 3 for title */
                align-items: center; /* Vertically align items */
                gap: 1rem; /* Space between button and title */
                margin-bottom: 1rem; /* Space below the header */
            }
            .custom-header .stButton button {
                /* Style for the 'New Analysis' button */
                background-color: #F0F2F6;
                color: #262730;
                border: 1px solid #DCDCDC;
            }
            </style>
        """, unsafe_allow_html=True)

        # --- Sidebar (Unchanged) ---
        st.sidebar.success(f"Logged in as **{st.session_state.username}**")
        st.sidebar.info(f"Showing results for **{st.session_state.selected_bank}**.")
        st.sidebar.divider()
        st.sidebar.button("Logout", on_click=logout, use_container_width=True)
        
        # --- NEW CUSTOM HEADER ---
        # We manually create the layout using markdown and st.empty()
        st.markdown('<div class="custom-header">', unsafe_allow_html=True)
        
        # Column 1: Button
        button_placeholder = st.empty()
        
        # Column 2: Title
        title_placeholder = st.empty()
        title_placeholder.title(f"Analysis for {st.session_state.selected_bank}")
        
        # Now, render the button inside the first column's placeholder
        with button_placeholder.container():
             if st.button("⬅️ New Analysis"):
                st.session_state.run_clicked = False
                st.session_state.active_tab = "chart"
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
        # --- END OF NEW CUSTOM HEADER ---

        #st.divider()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="rainbow-divider"></div>', unsafe_allow_html=True)

        if st.session_state.error:
            st.error(f"An error occurred: {st.session_state.error}")
        elif st.session_state.results:
            kpi_metrics = st.session_state.results['kpi_metrics']
            st.markdown('<div class="kpi-container">', unsafe_allow_html=True)
            kpi1, kpi2, kpi3 = st.columns(3)
            with kpi1:
                with st.container(border=True):
                    st.metric("Projected Savings", f"₹{kpi_metrics['total_savings']:,.2f}Cr", f"{kpi_metrics['savings_pct']:.2f}% Reduction")
            with kpi2:
                with st.container(border=True):
                    st.metric("Total Forecasted Expenditure", f"₹{kpi_metrics['total_forecast']:,.2f}Cr")
                    st.markdown("<div style='height: 29px;'></div>", unsafe_allow_html=True)
            with kpi3:
                with st.container(border=True):
                    st.metric("Total Optimized Expenditure", f"₹{kpi_metrics['total_optimized']:,.2f}Cr")
                    st.markdown("<div style='height: 29px;'></div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="rainbow-divider"></div>', unsafe_allow_html=True)
            
            # --- Tab Navigation (Unchanged) ---
            tab_cols = st.columns(3)
            tab_cols[0].button("📈 Forecast Chart", use_container_width=True, type=("primary" if st.session_state.active_tab == 'chart' else 'secondary'), on_click=set_active_tab, args=('chart',))
            tab_cols[1].button("📄 Detailed Data", use_container_width=True, type=("primary" if st.session_state.active_tab == 'data' else 'secondary'), on_click=set_active_tab, args=('data',))
            tab_cols[2].button("💡 Recommendations", use_container_width=True, type=("primary" if st.session_state.active_tab == 'recs' else 'secondary'), on_click=set_active_tab, args=('recs',))
            
            # --- Main Content Container (Unchanged) ---
            with st.container(border=True):
                if st.session_state.active_tab == 'chart':
                    st.subheader(f"Expenditure Forecast & Optimization for {st.session_state.selected_bank}")
                    chart_config = {'displaylogo': False, 'modeBarButtonsToRemove': ['zoom', 'pan', 'select2d', 'lasso2d', 'zoomIn', 'zoomOut', 'toImage']}
                    st.plotly_chart(st.session_state.results['chart_fig'], use_container_width=True, config=chart_config)
                elif st.session_state.active_tab == 'data':
                    st.subheader("Forecast vs. Optimized Data Table")
                    st.dataframe(st.session_state.results['combined_df'], use_container_width=True, height=400)
                elif st.session_state.active_tab == 'recs':
                    st.subheader("AI-Generated Recommendations")
                    st.info(st.session_state.results.get("recommendations", "No recommendations available."))
            
            #st.divider()
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('<div class="rainbow-divider"></div>', unsafe_allow_html=True)
            st.header("Download")
            dl1, dl2, dl3 = st.columns(3)
            with open(st.session_state.results['pdf_path'], "rb") as f: dl1.download_button("📥 Download PDF Report", f, os.path.basename(st.session_state.results['pdf_path']), use_container_width=True)
            with open(st.session_state.results['excel_path'], "rb") as f: dl2.download_button("📥 Download Excel Data", f, os.path.basename(st.session_state.results['excel_path']), use_container_width=True)
            with open(st.session_state.results['chart_path'], "rb") as f: dl3.download_button("📥 Download Chart Image", f, os.path.basename(st.session_state.results['chart_path']), use_container_width=True)
# --- MAIN APP ROUTER (UNCHANGED) ---
def main():
    keys_to_init = ['authenticated', 'username', 'results', 'error', 'run_clicked', 'selected_bank', 'active_tab']
    for key in keys_to_init:
        if key not in st.session_state:
            if key in ['authenticated', 'run_clicked']: st.session_state[key] = False
            elif key == 'active_tab': st.session_state[key] = 'chart'
            else: st.session_state[key] = None
    db.setup_database() 
    if not st.session_state['authenticated']: 
        login_signup_page()
    else: 
        show_main_app()

if __name__ == "__main__":
    main()