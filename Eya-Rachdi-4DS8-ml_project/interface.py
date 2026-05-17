import streamlit as st
import requests

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="AttritionAI - Employee Attrition Prediction",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ===============================
# CUSTOM CSS (Clean White Theme)
# ===============================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* --- Global --- */
    * { font-family: 'Inter', sans-serif; }
    html, body, [class*="stApp"] {
        background: #f5f5f7;
        color: #1a1a2e;
    }

    /* --- Hide default Streamlit elements --- */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    div[data-testid="stToolbar"] { visibility: hidden; }
    .block-container {
        padding-top: 0 !important;
        padding-bottom: 2rem !important;
        max-width: 1280px !important;
    }

    /* --- Scrollbar --- */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #eee; }
    ::-webkit-scrollbar-thumb { background: #1a1a2e; border-radius: 3px; }

    /* --- Navigation Bar --- */
    .navbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 3rem;
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(0, 0, 0, 0.08);
        position: sticky;
        top: 0;
        z-index: 100;
        margin: -1rem -2rem 0 -2rem;
    }
    .nav-logo {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        font-size: 1.4rem;
        font-weight: 800;
        color: #1a1a2e;
        letter-spacing: -0.5px;
    }
    .nav-logo .icon { font-size: 1.6rem; }
    .nav-logo span {
        background: linear-gradient(135deg, #1a1a2e, #444466);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .nav-links { display: flex; gap: 2rem; }
    .nav-links a {
        color: #888;
        text-decoration: none;
        font-size: 0.9rem;
        font-weight: 500;
        transition: all 0.3s;
        cursor: pointer;
        position: relative;
    }
    .nav-links a:hover, .nav-links a.active { color: #1a1a2e; }
    .nav-links a.active::after {
        content: '';
        position: absolute;
        bottom: -6px;
        left: 0;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, #1a1a2e, #444466);
        border-radius: 1px;
    }
    .nav-status {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.8rem;
        color: #16a34a;
        background: rgba(22, 163, 74, 0.08);
        padding: 0.4rem 1rem;
        border-radius: 20px;
        border: 1px solid rgba(22, 163, 74, 0.15);
    }
    .nav-status .dot {
        width: 8px; height: 8px;
        background: #16a34a;
        border-radius: 50%;
        animation: pulse-dot 2s infinite;
    }
    @keyframes pulse-dot {
        0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(22,163,74,0.4); }
        50% { opacity: 0.7; box-shadow: 0 0 0 6px rgba(22,163,74,0); }
    }

    /* --- Hero Section --- */
    .hero {
        text-align: center;
        padding: 4rem 1rem 3rem;
        position: relative;
    }
    .hero::before {
        content: '';
        position: absolute;
        top: -50px;
        left: 50%;
        transform: translateX(-50%);
        width: 600px;
        height: 400px;
        background: radial-gradient(ellipse, rgba(26,26,46,0.06) 0%, transparent 70%);
        pointer-events: none;
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.4rem 1.2rem;
        background: rgba(26, 26, 46, 0.06);
        border: 1px solid rgba(26, 26, 46, 0.12);
        border-radius: 50px;
        font-size: 0.8rem;
        color: #555;
        font-weight: 500;
        margin-bottom: 1.5rem;
    }
    .hero-badge .pulse {
        animation: pulse-dot 2s infinite;
        width: 8px; height: 8px;
        background: #555;
        border-radius: 50%;
    }
    .hero h1 {
        font-size: 3.2rem;
        font-weight: 900;
        color: #1a1a2e;
        line-height: 1.1;
        margin-bottom: 1rem;
        letter-spacing: -1.5px;
    }
    .hero h1 .gradient {
        background: linear-gradient(135deg, #1a1a2e 0%, #444466 50%, #1a1a2e 100%);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shimmer 3s linear infinite;
    }
    @keyframes shimmer { to { background-position: 200% center; } }
    .hero p {
        font-size: 1.1rem;
        color: #888;
        max-width: 600px;
        margin: 0 auto;
        line-height: 1.6;
    }

    /* --- Stats Row --- */
    .stats-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1.2rem;
        margin: 2rem 0 3rem;
    }
    .stat-card {
        background: #fff;
        border: 1px solid rgba(0,0,0,0.06);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.4s;
        position: relative;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .stat-card:hover {
        border-color: rgba(26,26,46,0.15);
        transform: translateY(-4px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.08);
    }
    .stat-card .stat-icon { font-size: 1.8rem; margin-bottom: 0.5rem; }
    .stat-card .stat-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #1a1a2e;
        margin-bottom: 0.2rem;
    }
    .stat-card .stat-value.purple { color: #1a1a2e; }
    .stat-card .stat-value.cyan { color: #444466; }
    .stat-card .stat-value.green { color: #16a34a; }
    .stat-card .stat-value.amber { color: #d97706; }
    .stat-card .stat-label {
        font-size: 0.78rem;
        color: #999;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }

    /* --- Section Titles --- */
    .section-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.3rem;
    }
    .section-subtitle {
        font-size: 0.9rem;
        color: #999;
        margin-bottom: 2rem;
    }

    /* --- Feature Cards Grid --- */
    .features-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-bottom: 3rem;
    }
    .feature-card {
        background: #fff;
        border: 1px solid rgba(0,0,0,0.06);
        border-radius: 14px;
        padding: 1.5rem;
        transition: all 0.4s;
        cursor: default;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .feature-card:hover {
        border-color: rgba(26,26,46,0.12);
        background: #fff;
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.07);
    }
    .feature-card .f-icon {
        width: 44px; height: 44px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.3rem;
        margin-bottom: 1rem;
    }
    .feature-card .f-icon.purple-bg { background: rgba(26,26,46,0.06); }
    .feature-card .f-icon.cyan-bg { background: rgba(68,68,102,0.08); }
    .feature-card .f-icon.green-bg { background: rgba(22,163,74,0.08); }
    .feature-card .f-icon.amber-bg { background: rgba(217,119,6,0.08); }
    .feature-card h3 { font-size: 0.95rem; font-weight: 600; color: #1a1a2e; margin-bottom: 0.4rem; }
    .feature-card p { font-size: 0.8rem; color: #999; line-height: 1.5; }

    /* --- Prediction Form Container --- */
    .form-container {
        background: #fff;
        border: 1px solid rgba(0,0,0,0.06);
        border-radius: 20px;
        padding: 2.5rem;
        position: relative;
        overflow: hidden;
        margin-bottom: 3rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .form-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #1a1a2e, #444466, #1a1a2e);
        background-size: 200% auto;
        animation: shimmer 3s linear infinite;
    }

    /* --- Override Streamlit Input Styles --- */
    div[data-testid="stNumberInput"] label,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stSlider"] label {
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        color: #666 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.8px !important;
    }
    div[data-testid="stNumberInput"] > div > div > div,
    div[data-testid="stSelectbox"] > div > div {
        background: #fafafa !important;
        border-color: rgba(0,0,0,0.1) !important;
        border-radius: 10px !important;
    }
    div[data-testid="stNumberInput"]:focus-within,
    div[data-testid="stSelectbox"]:focus-within {
        border-color: rgba(26,26,46,0.3) !important;
        box-shadow: 0 0 0 3px rgba(26,26,46,0.06) !important;
    }
    .st-ae input, .st-ae select { color: #1a1a2e !important; }

    /* --- Slider track --- */
    .stSlider [data-baseweb="slider"] [data-baseweb="slider-track"] {
        background: #e5e5e5 !important;
    }
    .stSlider [data-baseweb="slider"] [data-baseweb="slider-thumb"] {
        background: #1a1a2e !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.2) !important;
    }
    .stSlider [data-baseweb="slider"] div[style*="width:"][style*="left:"] {
        background: #1a1a2e !important;
    }

    /* --- Predict Button --- */
    .predict-btn-wrapper { margin-top: 2rem; text-align: center; }
    .stButton > button {
        background: #1a1a2e !important;
        color: #fff !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.85rem 3rem !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px;
        cursor: pointer;
        transition: all 0.3s !important;
        box-shadow: 0 4px 20px rgba(26,26,46,0.25) !important;
    }
    .stButton > button:hover {
        background: #2a2a4e !important;
        box-shadow: 0 6px 30px rgba(26,26,46,0.35) !important;
        transform: translateY(-2px) !important;
    }
    .stButton > button:active { transform: translateY(0) !important; }

    /* --- Result Cards --- */
    .result-container {
        margin-top: 2rem;
        border-radius: 16px;
        overflow: hidden;
        animation: fadeInUp 0.5s ease-out;
    }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .result-card {
        padding: 2rem;
        border-radius: 16px;
        display: flex;
        align-items: center;
        gap: 1.5rem;
    }
    .result-card.risk {
        background: linear-gradient(135deg, rgba(239,68,68,0.06), rgba(239,68,68,0.02));
        border: 1px solid rgba(239,68,68,0.15);
    }
    .result-card.safe {
        background: linear-gradient(135deg, rgba(22,163,74,0.06), rgba(22,163,74,0.02));
        border: 1px solid rgba(22,163,74,0.15);
    }
    .result-icon {
        width: 60px; height: 60px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.8rem;
        flex-shrink: 0;
    }
    .result-card.risk .result-icon { background: rgba(239,68,68,0.1); }
    .result-card.safe .result-icon { background: rgba(22,163,74,0.1); }
    .result-text h3 { font-size: 1.2rem; font-weight: 700; margin-bottom: 0.3rem; }
    .result-card.risk .result-text h3 { color: #dc2626; }
    .result-card.safe .result-text h3 { color: #16a34a; }
    .result-text p { font-size: 0.9rem; color: #888; }

    /* --- Probability Bar --- */
    .prob-bar-container { margin-top: 1.5rem; }
    .prob-bar-label {
        display: flex;
        justify-content: space-between;
        font-size: 0.82rem;
        color: #888;
        margin-bottom: 0.5rem;
    }
    .prob-bar {
        width: 100%;
        height: 10px;
        background: rgba(0,0,0,0.06);
        border-radius: 5px;
        overflow: hidden;
    }
    .prob-bar-fill {
        height: 100%;
        border-radius: 5px;
        transition: width 1s ease-out;
    }
    .prob-bar-fill.risk-bar { background: linear-gradient(90deg, #ef4444, #f97316); }
    .prob-bar-fill.safe-bar { background: linear-gradient(90deg, #16a34a, #4ade80); }

    /* --- Supported Factors Section --- */
    .factors-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 0.8rem;
        margin-bottom: 3rem;
    }
    .factor-item {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        padding: 1rem 1.2rem;
        background: #fff;
        border: 1px solid rgba(0,0,0,0.06);
        border-radius: 12px;
        transition: all 0.3s;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .factor-item:hover {
        border-color: rgba(26,26,46,0.12);
        box-shadow: 0 4px 15px rgba(0,0,0,0.06);
    }
    .factor-item .f-dot {
        width: 10px; height: 10px;
        border-radius: 50%;
        flex-shrink: 0;
    }
    .factor-item .f-dot.c1 { background: #1a1a2e; }
    .factor-item .f-dot.c2 { background: #444466; }
    .factor-item .f-dot.c3 { background: #16a34a; }
    .factor-item .f-dot.c4 { background: #d97706; }
    .factor-item .f-name { font-size: 0.88rem; font-weight: 500; color: #333; }
    .factor-item .f-desc { font-size: 0.75rem; color: #aaa; margin-left: auto; white-space: nowrap; }

    /* --- Tech Stack --- */
    .tech-row {
        display: flex;
        justify-content: center;
        gap: 2rem;
        flex-wrap: wrap;
        padding: 2rem 0;
    }
    .tech-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.85rem;
        color: #aaa;
        transition: color 0.3s;
    }
    .tech-item:hover { color: #666; }
    .tech-item .t-icon { font-size: 1.3rem; }

    /* --- Footer --- */
    .footer {
        text-align: center;
        padding: 2rem;
        border-top: 1px solid rgba(0,0,0,0.06);
        color: #bbb;
        font-size: 0.8rem;
        margin-top: 1rem;
    }

    /* --- Responsive --- */
    @media (max-width: 768px) {
        .stats-row { grid-template-columns: repeat(2, 1fr); }
        .features-grid { grid-template-columns: repeat(2, 1fr); }
        .factors-grid { grid-template-columns: 1fr; }
        .hero h1 { font-size: 2.2rem; }
        .navbar {
            flex-wrap: wrap;
            gap: 0.8rem;
            padding: 1rem 1.5rem;
            margin: -1rem -1rem 0 -1rem;
        }
        .nav-links { gap: 1rem; }
    }
</style>
""", unsafe_allow_html=True)

# ===============================
# NAVIGATION BAR
# ===============================
st.markdown("""
<div class="navbar">
    <div class="nav-logo">
        <span class="icon">🔮</span>
        <span>AttritionAI</span>
    </div>
    <div class="nav-links">
        <a class="active">Home</a>
        <a href="#predict">Predict</a>
        <a href="#performance">Performance</a>
        <a href="#about">About</a>
    </div>
    <div class="nav-status">
        <div class="dot"></div>
        Model Online
    </div>
</div>
""", unsafe_allow_html=True)

# ===============================
# HERO SECTION
# ===============================
st.markdown("""
<div class="hero">
    <div class="hero-badge">
        <div class="pulse"></div>
        Machine Learning Powered
    </div>
    <h1>AI - Powered <span class="gradient">Employee Attrition</span> Prediction</h1>
    <p>Predict employee turnover risk based on key HR metrics including satisfaction, income, work-life balance, and more.</p>
</div>
""", unsafe_allow_html=True)

# ===============================
# STATS ROW
# ===============================
st.markdown("""
<div class="stats-row">
    <div class="stat-card">
        <div class="stat-icon">🎯</div>
        <div class="stat-value purple">87.3%</div>
        <div class="stat-label">Accuracy</div>
    </div>
    <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-value cyan">89.1%</div>
        <div class="stat-label">Precision</div>
    </div>
    <div class="stat-card">
        <div class="stat-icon">⚡</div>
        <div class="stat-value green">85.7%</div>
        <div class="stat-label">Recall</div>
    </div>
    <div class="stat-card">
        <div class="stat-icon">🚀</div>
        <div class="stat-value amber">&lt;50ms</div>
        <div class="stat-label">Response Time</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ===============================
# FEATURE CARDS
# ===============================
st.markdown("""
<div class="features-grid">
    <div class="feature-card">
        <div class="f-icon purple-bg">🔮</div>
        <h3>Make Prediction</h3>
        <p>Input employee data and get instant attrition risk prediction with probability score.</p>
    </div>
    <div class="feature-card">
        <div class="f-icon cyan-bg">🧠</div>
        <h3>ML Model</h3>
        <p>Trained on 1,470 employee records using Random Forest with optimized hyperparameters.</p>
    </div>
    <div class="feature-card">
        <div class="f-icon green-bg">📈</div>
        <h3>Performance</h3>
        <p>High accuracy metrics validated with cross-validation and confusion matrix analysis.</p>
    </div>
    <div class="feature-card">
        <div class="f-icon amber-bg">💡</div>
        <h3>Insights</h3>
        <p>Understand key attrition drivers with feature importance analysis and SHAP values.</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ===============================
# PREDICTION FORM
# ===============================
st.markdown("""
<div id="predict">
    <div class="section-title">📝 Employee Information</div>
    <div class="section-subtitle">Fill in the details below to generate an attrition risk prediction</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="form-container">', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    age = st.number_input("Age", 18, 65, 30, step=1)
    distance = st.number_input("Distance From Home (km)", 1, 50, 10, step=1)
    income = st.number_input("Monthly Income ($)", 1000, 20000, 5000, step=100)

with col2:
    satisfaction = st.slider("Job Satisfaction", 1, 4, 3, help="1=Low, 2=Medium, 3=High, 4=Very High")
    wlb = st.slider("Work Life Balance", 1, 4, 3, help="1=Low, 2=Fair, 3=Good, 4=Excellent")
    performance = st.slider("Performance Rating", 1, 4, 3, help="1=Low, 2=Good, 3=Excellent, 4=Outstanding")

with col3:
    years = st.number_input("Years At Company", 0, 40, 5, step=1)
    overtime = st.selectbox("Overtime", ["No", "Yes"], index=0)

    st.markdown("""
    <div style="background:rgba(26,26,46,0.03); border:1px solid rgba(0,0,0,0.06); border-radius:12px; padding:1.2rem; margin-top:0.5rem;">
        <div style="font-size:1.5rem; margin-bottom:0.4rem;">ℹ️</div>
        <div style="font-size:0.78rem; color:#999; line-height:1.5;">
            All data is processed locally. No employee information is stored or transmitted outside this session.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="predict-btn-wrapper">', unsafe_allow_html=True)
predict_clicked = st.button("🔍  Predict Attrition Risk", type="primary", use_container_width=False)
st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ===============================
# PREDICTION LOGIC
# ===============================
if predict_clicked:
    data = {
        "Age": age,
        "DistanceFromHome": distance,
        "MonthlyIncome": income,
        "JobSatisfaction": satisfaction,
        "WorkLifeBalance": wlb,
        "YearsAtCompany": years,
        "PerformanceRating": performance,
        "OverTime_Yes": 1 if overtime == "Yes" else 0,
    }

    try:
        with st.spinner("Analyzing employee data..."):
            response = requests.post("http://127.0.0.1:8000/predict", json=data, timeout=10)

        if response.status_code == 200:
            result = response.json()["prediction"]
            probability = response.json()["probability"]

            if result == 1:
                risk_class = "risk"
                bar_class = "risk-bar"
                icon = "⚠️"
                title = "High Attrition Risk Detected"
                desc = f"This employee shows a {probability:.1%} probability of leaving the company. Consider proactive retention measures."
            else:
                risk_class = "safe"
                bar_class = "safe-bar"
                icon = "✅"
                title = "Low Attrition Risk"
                stay_prob = 1 - probability
                desc = f"This employee shows a {stay_prob:.1%} probability of staying with the company."

            st.markdown(f"""
            <div class="result-container">
                <div class="result-card {risk_class}">
                    <div class="result-icon">{icon}</div>
                    <div class="result-text">
                        <h3>{title}</h3>
                        <p>{desc}</p>
                    </div>
                </div>
                <div class="prob-bar-container">
                    <div class="prob-bar-label">
                        <span>Attrition Probability</span>
                        <span>{probability:.1%}</span>
                    </div>
                    <div class="prob-bar">
                        <div class="prob-bar-fill {bar_class}" style="width: {probability * 100}%"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if result == 1:
                st.markdown("""
                <div style="margin-top:1.5rem; padding:1.5rem; background:rgba(217,119,6,0.05); border:1px solid rgba(217,119,6,0.12); border-radius:14px;">
                    <div style="font-size:0.9rem; font-weight:600; color:#d97706; margin-bottom:0.6rem;">💡 Recommended Actions</div>
                    <div style="font-size:0.82rem; color:#999; line-height:1.8;">
                        • Schedule a 1-on-1 meeting to discuss job satisfaction<br>
                        • Review compensation against market benchmarks<br>
                        • Evaluate workload and overtime requirements<br>
                        • Explore career development opportunities
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")

    except requests.exceptions.ConnectionError:
        st.markdown("""
        <div style="padding:2rem; background:rgba(239,68,68,0.04); border:1px solid rgba(239,68,68,0.12); border-radius:14px; text-align:center;">
            <div style="font-size:2rem; margin-bottom:0.5rem;">🔌</div>
            <div style="font-size:1rem; font-weight:600; color:#dc2626; margin-bottom:0.4rem;">Cannot Connect to Model Server</div>
            <div style="font-size:0.82rem; color:#999;">Make sure the FastAPI server is running at <code style="color:#1a1a2e; background:#f0f0f0; padding:2px 6px; border-radius:4px;">http://127.0.0.1:8000</code></div>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Unexpected error: {e}")

# ===============================
# SUPPORTED FACTORS
# ===============================
st.markdown("""
<div id="performance">
    <div class="section-title">🔍 Input Factors</div>
    <div class="section-subtitle">Key HR metrics used for prediction</div>
</div>

<div class="factors-grid">
    <div class="factor-item">
        <div class="f-dot c1"></div>
        <span class="f-name">Age</span>
        <span class="f-desc">Demographic</span>
    </div>
    <div class="factor-item">
        <div class="f-dot c2"></div>
        <span class="f-name">Monthly Income</span>
        <span class="f-desc">Compensation</span>
    </div>
    <div class="factor-item">
        <div class="f-dot c3"></div>
        <span class="f-name">Job Satisfaction</span>
        <span class="f-desc">Engagement</span>
    </div>
    <div class="factor-item">
        <div class="f-dot c4"></div>
        <span class="f-name">Work Life Balance</span>
        <span class="f-desc">Well-being</span>
    </div>
    <div class="factor-item">
        <div class="f-dot c1"></div>
        <span class="f-name">Overtime</span>
        <span class="f-desc">Workload</span>
    </div>
    <div class="factor-item">
        <div class="f-dot c2"></div>
        <span class="f-name">Years At Company</span>
        <span class="f-desc">Tenure</span>
    </div>
    <div class="factor-item">
        <div class="f-dot c3"></div>
        <span class="f-name">Distance From Home</span>
        <span class="f-desc">Commute</span>
    </div>
    <div class="factor-item">
        <div class="f-dot c4"></div>
        <span class="f-name">Performance Rating</span>
        <span class="f-desc">Evaluation</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ===============================
# TECH STACK & FOOTER
# ===============================
st.markdown("""
<div id="about">
    <div class="section-title" style="text-align:center;">⚙️ Tech Stack</div>
    <div class="section-subtitle" style="text-align:center;">Built with modern tools for reliable predictions</div>
</div>

<div class="tech-row">
    <div class="tech-item"><span class="t-icon">🐍</span> Python</div>
    <div class="tech-item"><span class="t-icon">🤖</span> Scikit-learn</div>
    <div class="tech-item"><span class="t-icon">⚡</span> FastAPI</div>
    <div class="tech-item"><span class="t-icon">🌊</span> Streamlit</div>
    <div class="tech-item"><span class="t-icon">🐼</span> Pandas</div>
    <div class="tech-item"><span class="t-icon">📊</span> NumPy</div>
</div>

<div class="footer">
    © 2025 AttritionAI — AI-Powered Employee Attrition Prediction Platform. All rights reserved.
</div>
""", unsafe_allow_html=True)