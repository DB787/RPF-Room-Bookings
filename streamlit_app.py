import streamlit as st
import datetime
import urllib.parse
from supabase import create_client, Client
from streamlit_calendar import calendar

# ==========================================
# 1. DATABASE & ADMIN CONFIGURATION
# ==========================================
ADMIN_PASSCODE = st.secrets["ADMIN_PASSCODE"]
# System automatically looks for a USER_PASSCODE in secrets, defaults to 'RPF2026' if not set
USER_PASSCODE = st.secrets.get("USER_PASSCODE", "RPF2026")

@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()

# ==========================================
# 2. PAGE CONFIGURATION & VISUAL THEME
# ==========================================
st.set_page_config(page_title="RPF Room Bookings", layout="wide")

st.logo("🏢", size="large")

# Custom Responsive CSS injection
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');
        
        html, body, [data-testid="stWidgetLabel"], .main-title, .stTabs {
            font-family: 'Montserrat', sans-serif !important;
        }
        
        .main-title {
            color: #1e293b;
            text-align: center;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 25px;
        }
        
        div[data-testid="stForm"] {
            background-color: #f0f5fc !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 20px !important;
        }
        
        div[data-testid="stForm"] input, 
        div[data-testid="stForm"] select, 
        div[data-testid="stForm"] div[role="combobox"],
        div[data-testid="stForm"] div[data-baseweb="select"] {
            color: #1e293b !important;
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 8px !important;
        }
        
        div[data-baseweb="select"] *, 
        div[data-baseweb="calendar"] *,
        ul[role="listbox"] li,
        div[role="listbox"] * {
            color: #1e293b !important;
        }
        
        div[data-baseweb="select"] > div {
            background-color: #ffffff !important;
        }
        
        .sms-btn {
            display: inline-block;
            background-color: #25d366;
            color: white !important;
            font-weight: 600;
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            text-align: center;
            margin-top: 10px;
        }

        @media screen and (max-width: 768px) {
            .main-title { font-size: 1.8rem; }
        }
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------
# 🔒 MASTER PRIVACY SECURITY GATEWAY
# ------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown('<h1 class="main-title">🔐 Private Portal Access</h1>', unsafe_allow_html=True)
    st.write("This application is private. Please enter your community's access passcode to view and request room bookings.")
    
    entry_key = st.text_input("Enter Passcode:", type="password", placeholder="Type password here...")
    if st.button("Unlock Application"):
        if entry_key == USER_PASSCODE or entry_key == ADMIN_PASSCODE:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect Passcode. Access denied.", icon="🛑")
    st.stop()  # Rigidly stops execution here if password isn't verified yet!

# ==========================================
# 3. LIVE APPLICATION (ONLY SEEN IF LOGGED IN)
# ==========================================
st.markdown('<h1 class="main-title">RPF Room Bookings</h1>', unsafe_allow_html=True)

ROOMS = [
    "Main Hall", "Youth Hall", "Common Room", 
    "Retreat Room 1", "Retreat Room 2", "Retreat Room 3", "Retreat Room 4",
    "Retreat Room 5", "Retreat Room 6", "Retreat Room 7", "Retreat Room 8"
]

time_slots = [datetime.time(h, 0).strftime("%H:%M:%S") for h in range(24)]
time_labels = [datetime.time(h, 0).strftime("%H:%M") for h in range(24)]
time_mapping = dict(zip(time_labels, time_slots))
reverse_time_mapping = dict(zip(time_slots, time_labels))

def get_bookings():
    try:
        response = supabase.table("bookings").select("*").eq("status", "Approved").order("booking_date").execute()
        return response.data if response else []
    except:
        return []

if "admin_action_msg" in st.session_state:
    st.toast(st.session_state.admin_action_msg, icon="⚙️")
    del st.session_state.admin_action_msg

# ==========================================
# 4. SIDEBAR: OPERATOR GATEWAY
# ==========================================
with st.sidebar:
    st.markdown("### 🔒 Staff Gateway")
    show_admin = False
    
    passcode_input = st.text_input("Portal Key", type="password", placeholder="Enter authorization key...")
    if passcode_input == ADMIN_PASSCODE:
        st.success("Operator Access Granted", icon="🔑")
        show_admin = True
    elif passcode_input != "":
        st.error("Access Denied", icon="🛑")
        
    if st.button("🚪 Log Out of App"):
        st.session_state.authenticated = False
        st.rerun()

# ==========================================
# MAIN INTERFACE LAYOUT
# ==========================================
if show_admin:
    tab1, tab2 = st.tabs(["📅 Schedule & Requests", "⚙️ Manager Controls"])
else:
    tab1 = st.container()
    tab2 = None

with tab1:
    raw_bookings = get_bookings()
    
    view_type = st.radio(
        "Select Calendar Layout Style:",
        ["📱 Mobile Weekly List (Full Week)", "🖥️ Full Calendar Grid (Best for Desktop)"],
        horizontal=True
    )
    
    st.markdown("---")

    # 📱 NEW OPTIMIZED PHONE VIEW: THE FULL WEEK FEED + DATE JUMPER
    if view_type == "📱 Mobile Weekly List (Full Week)":
        
        # 🗓️ THE DATE JUMPER BOX
        st.markdown("#### 🔍 Jump to a Custom Week")
        start_date_selection = st.date_input(
            "Show 7 days starting from:", 
            datetime.date.today(), 
            format="DD/MM/YYYY",
            key="mobile_date_picker"
        )
        
        st.markdown("---")
        st.subheader("📋 Scheduled Allocations")
        
        # Calculate 7 consecutive days starting from whatever date you picked above
        upcoming_days = [start_date_selection + datetime.timedelta(days=i) for i in range(7)]
        
        has_any_bookings = False
        
        # Loop through each of the selected 7 days and pull data
        for target_date in upcoming_days:
            target_date_str = str(target_date)
            day_events = [b for b in raw_bookings if b['booking_date'] == target_date_str]
            
            # Format the header for each day nicely
            day_header = target_date.strftime("%A (%b %d, %Y)")
            if target_date == datetime.date.today():
                day_header = "⭐️ TODAY — " + day_header
            elif target_date == datetime.date.today() + datetime.timedelta(days=1):
                day_header = "➡️ TOMORROW — " + day_header
                
            # Only display the day header if there are actually events scheduled
            if day_events:
                has_any_bookings = True
                st.markdown(f"### {day_header}")
                
                # Sort listings chronologically by start time
                day_events = sorted(day_events, key=lambda x: x['start_time'])
                for b in day_events:
                    display_title = b['user_name'].split(" (")[0] if " (" in b['user_name'] else b['user_name']
                    try:
                        st_time = datetime.datetime.strptime(b['start_time'], "%H:%M:%S").strftime("%I:%M %p")
                        en_time = datetime.datetime.strptime(b['end_time'], "%H:%M:%S").strftime("%I:%M %p")
                        time_display = f"{st_time} - {en_time}"
                    except:
                        time_display = f"{b['start_time'][:5]} - {b['end_time'][:5]}"
                    
                    st.markdown(f"""
                        <div style="background-color: #f8fafc; border-left: 6px solid #82a6d7; padding: 15px; border-radius: 8px; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                            <div style="font-size: 1.15rem; font-weight: 700; color: #1e293b; margin-bottom: 4px;">👤 Event: {display_title}</div>
                            <div style="font-size: 1.05rem; font-weight: 600; color: #475569;">⏰ Time: {time_display}</div>
                            <div style="font-size: 0.95rem; font-weight: 500; color: #64748b; margin-top: 2px;">📍 Room: {b['room_name']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True) # Clean visual gap
                
        if not has_any_bookings:
            st.info(f"🟢 No room allocations booked for the 7-day window starting {start_date_selection.strftime('%d/%m/%Y')}.")

    # 🖥️ FULL LARGE CANVAS GRID INTERFACE (Stays completely untouched)
    else:
        calendar_events = []
        for b in raw_bookings:
            display_title = b['user_name'].split(" (")[0] if " (" in b['user_name'] else b['user_name']
            try:
                st_time_obj = datetime.datetime.strptime(b['start_time'], "%H:%M:%S")
                end_time_obj = datetime.datetime.strptime(b['end_time'], "%H:%M:%S")
                time_display = f"{st_time_obj.strftime('%I:%M %p')} - {end_time_obj.strftime('%I:%M %p')}"
            except:
                time_display = f"{b['start_time'][:5]} - {b['end_time'][:5]}"
                
            full_event_label = f"{display_title}\n⏰ Time: {time_display}\n📍 Room: {b['room_name']}"
            
            calendar_events.append({
                "title": full_event_label,
                "start": f"{b['booking_date']}T{b['start_time']}",
                "end": f"{b['booking_date']}T{b['end_time']}",
                "resourceId": b['room_name'],
                "backgroundColor": "#bacfe6",  
                "borderColor": "#82a6d7",
                "textColor": "#1e293b"
            })
            
        calendar_options = {
            "initialView": "timeGridWeek",
            "headerToolbar": {"left": "prev,next today", "center": "title", "right": "timeGridWeek,timeGridDay"},
            "firstDay": 1,              
            "locale": "en-gb",          
            "slotMinTime": "00:00:00",   
            "slotMaxTime": "24:00:00",   
            "allDaySlot": False,
            "height": "auto",
            "slotDuration": "00:30:00",    
            "snapDuration": "00:30:00",
            "slotLabelFormat": {"hour": "numeric", "minute": "2-digit", "omitZeroMinute": False, "meridiem": "short", "hour12": True}
        }
        
        calendar_styles = """
            .fc-theme-standard .fc-col-header-cell { background-color: #82a6d7 !important; }
            .fc-col-header-cell-cushion { color: white !important; font-weight: 600 !important; padding: 6px 0 !important; font-size: 1rem; }
            .fc-theme-standard td, .fc-theme-standard th { border: 1px solid #e2e8f0 !important; }
            .fc-timegrid-slot-label-cushion { font-weight: 600 !important; font-size: 0.85rem !important; text-transform: uppercase; }
            .fc-timegrid-event-holder, .fc-timegrid-event, .fc-event { background-color: #bacfe6 !important; border-radius: 4px !important; padding: 1px !important; overflow: visible !important; }
            .fc-event-main, .fc-event-title, .fc-event-title-container { font-size: 11px !important; font-weight: 700 !important; line-height: 1.1 !important; white-space: pre-wrap !important; word-break: break-word !important; padding: 1px 2px !important; }
            .fc-event-time { display: none !important; }
        """
        
        calendar(events=calendar_events, options=calendar_options, custom_css=calendar_styles, key="booking_calendar")
        
    st.markdown("---")
    st.subheader("Submit a New Booking Request")
    
    with st.form("request_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            booking_name = st.text_input("Event / Group Name")
            contact_name = st.text_input("Your Name")
            contact_phone = st.text_input("Your Phone Number")
            room_selection = st.selectbox("Select Room", ROOMS)
        with col2:
            booking_date = st.date_input("Date (DD/MM/YYYY)", datetime.date.today(), format="DD/MM/YYYY")
            start_label = st.selectbox("Start Time (24h)", time_labels, index=9) 
            end_label = st.selectbox("End Time (24h)", time_labels, index=10) 
            
        submit_btn = st.form_submit_button("Submit Request")
        
        if submit_btn:
            if booking_name and contact_name and contact_phone:
                data = {
                    "room_name": room_selection,
                    "booking_date": str(booking_date),
                    "start_time": time_mapping[start_label],
                    "end_time": time_mapping[end_label],
                    "user_name": f"{booking_name} ({contact_name})", 
                    "user_email": contact_phone,  
                    "status": "Pending"
                }
                supabase.table("bookings").insert(data).execute()
                st.success(f"🎉 SUCCESS! Your request for '{booking_name}' has been safely submitted.")
            else:
                st.error("Submission Failed: Please fill out all boxes.", icon="❌")

# ------------------------------------------
# MANAGER CONTROLS (TAB 2)
# ------------------------------------------
if show_admin and tab2 is not None:
    with tab2:
        st.subheader("Manager Portal")
        
        st.markdown("### 📝 Edit & Tweak Live Events")
        with st.expander("Click to open Live Tweak Engine"):
            all_live = supabase.table("bookings").select("*").eq("status", "Approved").order("booking_date").execute()
            live_list = all_live.data if all_live else []
            
            if not live_list:
                st.info("No active events currently published to modify.")
            else:
                event_options = {f"{ev['booking_date']} | {ev['room_name']} — {ev['user_name']}": ev for ev in live_list}
                selected_event_key = st.selectbox("Choose an Event to Edit", list(event_options.keys()))
                
                if selected_event_key:
                    target_event = event_options[selected_event_key]
                    
                    with st.form(f"edit_form_{target_event['id']}"):
                        edit_name = st.text_input("Event Name / Contact String", value=target_event['user_name'])
                        edit_room = st.selectbox("Assigned Room", ROOMS, index=ROOMS.index(target_event['room_name']))
                        edit_date = st.date_input("Scheduled Date", datetime.datetime.strptime(target_event['booking_date'], "%Y-%m-%d"), format="DD/MM/YYYY")
                        
                        curr_start_lbl = reverse_time_mapping.get(target_event['start_time'][:8], time_labels[9])
                        curr_end_lbl = reverse_time_mapping.get(target_event['end_time'][:8], time_labels[10])
                        
                        col_e1, col_e2 = st.columns(2)
                        with col_e1:
                            edit_start = st.selectbox("New Start Time (24h)", time_labels, index=time_labels.index(curr_start_lbl))
                        with col_e2:
                            edit_end = st.selectbox("New End Time (24h)", time_labels, index=time_labels.index(curr_end_lbl))
                            
                        save_edits = st.form_submit_button("Save Layout Tweaks")
                        if save_edits:
                            update_payload = {
                                "user_name": edit_name,
                                "room_name": edit_room,
                                "booking_date": str(edit_date),
                                "start_time": time_mapping[edit_start],
                                "end_time": time_mapping[edit_end]
                            }
                            supabase.table("bookings").update(update_payload).eq("id", target_event['id']).execute()
                            st.session_state.admin_action_msg = f"📝 Modified parameters for '{edit_name}'."
                            st.rerun()

        st.markdown("---")
        
        st.markdown("### 🔁 Add Recurring Schedule Block")
        with st.expander("Click to open Recurring Event Creator"):
            with st.form("recurring_form"):
                rec_title = st.text_input("Recurring Event Title")
                rec_room = st.selectbox("Select Target Room", ROOMS, key="recurring_target_room")
                
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    start_date = st.date_input("First Occurrence Date", datetime.date.today(), format="DD/MM/YYYY")
                    rec_start_lbl = st.selectbox("Start Time (24h)", time_labels, index=9, key="rec_start_time")
                with col_r2:
                    weeks_count = st.number_input("Repeat weekly for how many weeks?", min_value=2, max_value=52, value=4)
                    rec_end_lbl = st.selectbox("End Time (24h)", time_labels, index=10, key="rec_end_time")
                
                submit_recurring = st.form_submit_button("Generate All Recurring Blocks")
                if submit_recurring and rec_title:
                    batch_data = []
                    current_date = start_date
                    for _ in range(weeks_count):
                        batch_data.append({
                            "room_name": rec_room,
                            "booking_date": str(current_date),
                            "start_time": time_mapping[rec_start_lbl],
                            "end_time": time_mapping[rec_end_lbl],
                            "user_name": f"🔄 {rec_title}",
                            "user_email": "Admin Blockout",
                            "status": "Approved"
                        })
                        current_date += datetime.timedelta(weeks=1)
                    
                    supabase.table("bookings").insert(batch_data).execute()
                    st.session_state.admin_action_msg = f"🔁 Published {weeks_count} weekly blocks for '{rec_title}'."
                    st.rerun()

        st.markdown("---")
        
        st.markdown("### 📋 Pending Approval Requests")
        pending_res = supabase.table("bookings").select("*").eq("status", "Pending").execute()
        pending_bookings = pending_res.data if pending_res else []
        
        if not pending_bookings:
            st.info("No pending booking requests.")
        else:
            for pb in pending_bookings:
                with st.container():
                    st.markdown(f"#### {pb['user_name']} ({pb['room_name']})")
                    try:
                        parsed_date = datetime.datetime.strptime(pb['booking_date'], "%Y-%m-%d").strftime("%d/%m/%Y")
                    except:
                        parsed_date = pb['booking_date']
                    st.text(f"📅 Date & Time: {parsed_date} | {pb['start_time'][:5]} - {pb['end_time'][:5]}")
                    
                    col_app, col_rej, _ = st.columns([1, 1, 4])
                    if col_app.button("Approve", key=f"app_{pb['id']}"):
                        supabase.table("bookings").update({"status": "Approved"}).eq("id", pb['id']).execute()
                        st.session_state.admin_action_msg = f"✅ Approved request from '{pb['user_name']}'."
                        st.rerun()
                    if col_rej.button("Reject", key=f"rej_{pb['id']}"):
                        supabase.table("bookings").update({"status": "Rejected"}).eq("id", pb['id']).execute()
                        st.session_state.admin_action_msg = f"❌ Rejected request from '{pb['user_name']}'."
                        st.rerun()

        st.markdown("---")
        
        st.markdown("### 🗑️ Delete or Cancel Live Events")
        with st.expander("Click to view full calendar cleanup deck"):
            all_approved = supabase.table("bookings").select("*").eq("status", "Approved").order("booking_date").execute()
            approved_list = all_approved.data if all_approved else []
            
            if not approved_list:
                st.info("No active events currently published to delete.")
            else:
                for ab in approved_list:
                    col_info, col_del = st.columns([5, 1])
                    try:
                        m_date = datetime.datetime.strptime(ab['booking_date'], "%Y-%m-%d").strftime("%d/%m/%Y")
                    except:
                        m_date = ab['booking_date']
                        
                    with col_info:
                        st.write(f"🔹 **{m_date}** | {ab['room_name']} — {ab['user_name']} ({ab['start_time'][:5]}-{ab['end_time'][:5]})")
                    with col_del:
                        if st.button("Delete ❌", key=f"del_{ab['id']}"):
                            supabase.table("bookings").delete().eq("id", ab['id']).execute()
                            st.session_state.admin_action_msg = f"🗑️ Deleted live allocation for '{ab['user_name']}'."
                            st.rerun()
