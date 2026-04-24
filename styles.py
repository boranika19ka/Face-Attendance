import streamlit as st

def apply_styles(theme="dark"):
    if theme == "light":
        bg_main = "#f0f2f5"
        bg_card = "#ffffff"
        text_color = "#1f2328"
        border_color = "#d0d7de"
        sidebar_bg = "#ffffff"
        text_muted = "#636c76"
        header_color = "#1f2328"
        input_bg = "#f6f8fa"
    else: # dark
        bg_main = "#0e1117"
        bg_card = "#161b22"
        text_color = "#ffffff"
        border_color = "#30363d"
        sidebar_bg = "#161b22"
        text_muted = "#8b949e"
        header_color = "#f0f6fc"
        input_bg = "#0d1117"

    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
        
        /* Global Font */
        html, body, [class*="css"]  {{
            font-family: 'Outfit', sans-serif;
        }}

        .main {{
            background-color: {bg_main};
            color: {text_color};
        }}
        
        /* Sidebar */
        [data-testid="stSidebar"] {{
            background-color: {sidebar_bg};
            border-right: 1px solid {border_color};
        }}
        
        /* Dashboard Cards */
        .metric-card {{
            background-color: {bg_card};
            border: 1px solid {border_color};
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.4);
            border-color: #58a6ff;
        }}
        
        .metric-value {{
            font-size: 2.5rem;
            font-weight: bold;
            color: #58a6ff;
            margin-bottom: 5px;
        }}
        
        .metric-label {{
            font-size: 1rem;
            color: {text_muted};
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        /* Buttons */
        .stButton>button {{
            width: 100%;
            border-radius: 8px;
            height: 45px;
            background-color: #238636;
            color: white;
            border: none;
            font-weight: 600;
            transition: all 0.3s ease;
        }}
        
        .stButton>button:hover {{
            background-color: #2ea043;
            box-shadow: 0 4px 12px rgba(46, 160, 67, 0.3);
        }}
        
        /* Form Inputs */
        .stTextInput>div>div>input, .stSelectbox>div>div>div {{
            background-color: {input_bg};
            border: 1px solid {border_color};
            color: {text_color} !important;
            border-radius: 8px;
        }}
        
        /* Success/Error Messages */
        .stAlert {{
            border-radius: 10px;
            border: none;
        }}
        
        /* Header Styling */
        h1, h2, h3, h4, h5, h6, label, .stMarkdown p {{
            color: {header_color};
        }}
        
        /* Webcam Container */
        .webcam-container {{
            border: 3px solid {border_color};
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }}
        
        /* Title Bar */
        .title-container {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 30px;
        }}
        
        .title-icon {{
            font-size: 40px;
            color: #58a6ff;
        }}

        /* Hiding Streamlit Elements */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        .stDeployButton, .stAppDeployButton, [data-testid="stAppDeploy"] {{
            display: none !important;
        }}

        /* Scanning Animation */
        @keyframes scan {{
            0% {{ top: 0%; }}
            100% {{ top: 100%; }}
        }}
        
        .scanner-container {{
            position: relative;
            border: 2px solid #58a6ff;
            border-radius: 10px;
            overflow: hidden;
        }}
        
        .scanner-line {{
            position: absolute;
            width: 100%;
            height: 2px;
            background: rgba(88, 166, 255, 0.5);
            box-shadow: 0 0 15px #58a6ff;
            animation: scan 3s linear infinite;
            z-index: 10;
        }}

        .live-indicator {{
            color: #da3633;
            font-weight: bold;
            animation: blink 1.5s step-start infinite;
        }}

        @keyframes blink {{
            50% {{ opacity: 0; }}
        }}
        </style>
    """, unsafe_allow_html=True)

def metric_card(label, value, icon=""):
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{icon} {label}</div>
            <div class="metric-value">{value}</div>
        </div>
    """, unsafe_allow_html=True)
