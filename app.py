from datetime import datetime
import gc
from pathlib import Path
import pandas as pd
from PIL import Image
import streamlit as st
from dateutil import parser as date_parser

from ird_api import fetch_winners
from ocr import extract_coupons_from_image

# =============================================================================
# Constants
# =============================================================================
CACHE_TTL_SECONDS = 3600
MAX_COUPON_LENGTH = 12
COUPON_DIGIT_ONLY_PATTERN = r"\b\d{12}\b"

# =============================================================================
# 1. Page Configuration & Custom Styling
# =============================================================================
PAGE_ICON = (
    "data:image/svg+xml,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' "
    "stroke='%23059669' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E"
    "%3Crect x='2' y='6' width='20' height='12' rx='2'/%3E"
    "%3Ccircle cx='12' cy='12' r='2'/%3E"
    "%3Cpath d='M6 12h.01M18 12h.01'/%3E"
    "%3C/svg%3E"
)

st.set_page_config(
    page_title="IRD Prize Winner Checker",
    page_icon=PAGE_ICON,
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    /* Inline green Help text button with no border, frame, or vertical wrapping */
    div[data-testid="stColumn"]:first-child button[key="help_text_btn"] {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        color: #10b981 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        padding: 0 !important;
        margin: 0 !important;
        min-height: auto !important;
        height: auto !important;
        width: auto !important;
        white-space: nowrap !important;
        cursor: pointer;
        text-decoration: underline;
    }

    div[data-testid="stColumn"]:first-child button[key="help_text_btn"]:hover {
        color: #059669 !important;
        background: transparent !important;
        text-decoration: underline;
    }

    div[data-testid="stColumn"]:first-child button[key="help_text_btn"]:focus {
        box-shadow: none !important;
        outline: none !important;
    }

    /* Card containers & border styling */
    div[data-testid="stForm"], div[data-testid="column"] {
        border-radius: 12px;
    }

    /* Primary button styling */
    div.stButton > button[kind="primary"] {
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.2s ease;
    }

    /* Modern Theme-Adaptive Metric Cards */
    div[data-testid="stMetric"] {
        background-color: var(--secondary-background-color);
        border: 1px solid var(--gray-20, rgba(128, 128, 128, 0.2));
        padding: 12px 18px;
        border-radius: 10px;
    }

    /* Professional Brand Header & Logo Styling */
    .brand-container {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 0 0 16px 0;
    }

    .brand-icon-box {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 52px;
        height: 52px;
        min-width: 52px;
        background: linear-gradient(135deg, #10b981, #059669);
        color: #ffffff;
        border-radius: 14px;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
    }

    .brand-text-group {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }

    .brand-status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #10b981;
    }

    .brand-title {
        font-size: 1.65rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        line-height: 1.2;
        margin: 0;
    }

    /* Dividers */
    hr {
        margin: 1.25rem 0 !important;
        border-color: var(--gray-20, rgba(128, 128, 128, 0.2)) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# 2. Help Modal Dialog & Horizontal Green Text Button Trigger
# =============================================================================


@st.dialog("How It Works & User Guide")
def show_help_modal():
    st.markdown("""
    **How the IRD Draw Verification Works**
    * **Automated Data Retrieval:** Cross-references your 12-digit transaction codes against official Inland Revenue Department (IRD) winning draw records.
    * **Instant Verification:** Matching codes are flagged as **WINNER** along with rank, draw title, and claim deadline.

    ---

    **How to Use This Tool**

    1. **Upload Payment Screenshots:** Drag and drop payment receipt screenshots with 12-digit codes into the uploader.
    2. **Manual Input:** Alternatively, type 12-digit coupon codes into the manual text area.
    3. **Run Verification:** Click **Check Prize Status**.
    4. **Export Results:** View your breakdown or download results as a CSV file.
    """)
    
    st.divider()
    
    # Define your link and SVG
    youtube_link = "https://www.youtube.com/watch?v=PsixvrDJZD8" 
    svg_icon = '''<svg fill="#ff0000" height="24px" width="24px" version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="-143 145 512 512" xml:space="preserve" stroke="#ff0000"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <g> <path d="M-143,145v512h512V145H-143z M339,627h-452V175h452V627z"></path> <path d="M29.1,490.9h167.8c0,0,44.1,0,44.1-44.1v-91.5c0,0,0-44.1-44.1-44.1H29.1c0,0-44.1,0-44.1,44.1v91.5 C-15,446.8-15,490.9,29.1,490.9z M78.9,351.8l83.8,49.3l-83.8,49.2V351.8z"></path> </g> </g></svg>'''
    
    # Create a custom HTML button that opens in a new tab
    custom_button_html = f"""
    <a href="{youtube_link}" target="_blank" style="
        display: flex; 
        align-items: center; 
        justify-content: center; 
        background-color: transparent; 
        color: inherit; 
        text-decoration: none; 
        padding: 0.5rem 1rem; 
        border: 1px solid rgba(128, 128, 128, 0.4); 
        border-radius: 0.5rem; 
        transition: border-color 0.2s;
    ">
        {svg_icon}
        <span style="margin-left: 10px; font-weight: 500;">Watch YouTube Tutorial</span>
    </a>
    """
    
    # Render the custom HTML in Streamlit
    st.markdown(custom_button_html, unsafe_allow_html=True)

# Columns ratio set to [2, 14] to allow the text button to extend naturally left-to-right
help_col, _ = st.columns([2, 14])
with help_col:
    if st.button("Help ?", key="help_text_btn", help="Click to view details on how to use this tool"):
        show_help_modal()

# =============================================================================
# 3. Cash Icon Brand Header
# =============================================================================
st.markdown(
    """
    <div class="brand-container">
        <div class="brand-icon-box">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="2" y="6" width="20" height="12" rx="2"></rect>
                <circle cx="12" cy="12" r="2"></circle>
                <path d="M6 12h.01M18 12h.01"></path>
            </svg>
        </div>
        <div class="brand-text-group">
            <div class="brand-status-pill">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor">
                    <circle cx="12" cy="12" r="10"></circle>
                </svg>
                Give me the money!
            </div>
            <h1 class="brand-title">Taxpayer Incentive Winner Checker</h1>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "Upload eligible payment history screenshots (containing multiple 12-digit coupons) or type codes directly to check for winning matches."
)

# =============================================================================
# 4. Load Winners Data with Caching
# =============================================================================
@st.cache_data(ttl=CACHE_TTL_SECONDS)
def load_winners() -> tuple[dict, str | None]:
    """Fetches and caches IRD winners data."""
    try:
        return fetch_winners(), None
    except Exception as e:
        return {}, str(e)

winning_dict, api_error = load_winners()

if api_error:
    st.error(f"⚠️ Unable to fetch IRD winning records: {api_error}")
    st.info("The checker will not work until the API connection is restored.")

st.divider()

# =============================================================================
# 5. Input Section Layout
# =============================================================================
col1, col2 = st.columns([1, 1], gap="medium")

with col1:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 6px; font-weight: 600; margin-bottom: 6px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
            Eligible Payment History Screenshots
        </div>
        """,
        unsafe_allow_html=True,
    )
    uploaded_files = st.file_uploader(
        "Upload mobile payment history screenshots",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

with col2:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 6px; font-weight: 600; margin-bottom: 6px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
            Manual Coupon List
        </div>
        """,
        unsafe_allow_html=True,
    )
    manual_input = st.text_area(
        "Enter 12-digit numbers",
        placeholder="e.g. 027538139157\n026954870201\n025986630944",
        height=130,
        label_visibility="collapsed",
    )

st.write("")
process_btn = st.button("Check Prize Status", type="primary", use_container_width=True)

# =============================================================================
# 6. Results Processing
# =============================================================================
if process_btn:
    if not winning_dict:
        st.error("Cannot process: IRD winners data is not loaded. Please refresh or check your connection.")
    else:
        ocr_coupons = []

        if uploaded_files:
            with st.spinner("Scanning coupons from payment history..."):
                for uploaded_file in uploaded_files:
                    try:
                        image_bytes = uploaded_file.getvalue()
                        extracted = extract_coupons_from_image(image_bytes)
                        ocr_coupons.extend(extracted)
                    except Exception as exc:
                        st.error(f"Error reading {uploaded_file.name}: {exc}")
                    finally:
                        gc.collect()

        manual_coupons = []
        if manual_input.strip():
            raw_tokens = manual_input.replace(",", " ").split()
            for token in raw_tokens:
                clean_token = "".join(filter(str.isdigit, token))
                if len(clean_token) == MAX_COUPON_LENGTH:
                    manual_coupons.append(clean_token)

        # Deduplicate across all sources
        all_coupons = list(dict.fromkeys(ocr_coupons + manual_coupons))

        if not all_coupons:
            st.warning("No valid 12-digit coupon numbers detected.")
        else:
            st.divider()
            
            results = []
            winners_count = 0

            for coupon in all_coupons:
                if coupon in winning_dict:
                    info = winning_dict[coupon]
                    raw_deadline = info.get("claim_deadline")
                    
                    formatted_deadline = "N/A"
                    if raw_deadline:
                        try:
                            dt = date_parser.parse(raw_deadline)
                            formatted_deadline = dt.strftime("%d %b %Y, %I:%M %p")
                        except (ValueError, TypeError):
                            formatted_deadline = str(raw_deadline)

                    results.append(
                        {
                            "Result": "WINNER",
                            "Coupon Code": coupon,
                            "Prize Rank": info.get("rank", "N/A"),
                            "Draw Title": info.get("draw", info.get("category", "N/A")),
                            "Claim Deadline": formatted_deadline,
                        }
                    )
                    winners_count += 1
                else:
                    results.append(
                        {
                            "Result": "No Prize Won",
                            "Coupon Code": coupon,
                            "Prize Rank": "—",
                            "Draw Title": "—",
                            "Claim Deadline": "—",
                        }
                    )

            df = pd.DataFrame(results)
            df["Prize Rank"] = df["Prize Rank"].astype(str)

            # Overview Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Coupons Checked", len(all_coupons))
            m2.metric("Winning Matches", winners_count)
            m3.metric("OCR Scanned", len(ocr_coupons))

            st.write("")

            if winners_count > 0:
                st.balloons()
                st.success(f"🎉 Match found! You have {winners_count} winning coupon(s).")
            else:
                st.info("None of the checked coupons matched the current winning draw list.")

            # Highlight winning entries cleanly
            def highlight_winning_rows(row):
                if row["Result"] == "WINNER":
                    return ["background-color: rgba(46, 125, 50, 0.25); font-weight: 600;"] * len(row)
                return [""] * len(row)

            st.dataframe(
                df.style.apply(highlight_winning_rows, axis=1),
                use_container_width=True,
                hide_index=True,
            )

            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Draw Results CSV",
                data=csv_data,
                file_name="ird_draw_results.csv",
                mime="text/csv",
                use_container_width=True,
            )
