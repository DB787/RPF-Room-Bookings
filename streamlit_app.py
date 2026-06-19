import streamlit as st
import datetime
import urllib.parse
from supabase import create_client, Client
from streamlit_calendar import calendar

# ==========================================
# 1. DATABASE & ADMIN CONFIGURATION
# ==========================================
ADMIN_PASSCODE = st.secrets["ADMIN_PASSCODE"]

@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()

# ==========================================
# 2. PAGE CONFIGURATION & VISUAL THEME
# ==========================================
st.set_page_config(page_title="RPF Room Bookings", layout="wide")
st.logo("🏢", size="large")

# Custom Responsive CSS Injection
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght=400;600;700&display=swap');
        
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
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">RPF Room Bookings</h1>', unsafe_allow_html=True)

# Public Rooms List
PUBLIC_ROOMS = [
    "Main Hall", "Youth Hall", "Common Room", 
    "Retreat Room 1", "Retreat Room 2", "Retreat Room 3", "Retreat Room 4",
    "Retreat Room 5", "Retreat Room 6", "Retreat Room 7", "Retreat Room 8"
]

# Hidden Admin Room
ADMIN_ONLY_ROOMS = ["Archway"]

# ==========================================
# 3. HELPER UTILITIES & ALGORITHMIC SORTING
# ==========================================
def get_bookings():
    try:
        response = supabase.table("bookings").select("*").eq("status", "Approved").order("booking_date").execute()
        return response.data if response else []
    except:
        return []

def clean_title(name_str):
    """Extracts raw event names for clean sorting calculations"""
    if " (" in name_str:
        return name_str.split(" (")[0].strip().lower()
    return name_str.strip().lower()

def sort_events_engine(event_list):
    """Sorts data chronologically, then alphabetically by event name"""
    return sorted(event_list, key=lambda x: (x['booking_date'], x['start_time'], clean_title(x['user_name'])))

def parse_to_ddmmyyyy(date_str):
    """Safely normalizes database YYYY-MM-DD strings to visual DD/MM/YYYY formats"""
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        return date_str

def generate_msg_link(phone_num, message_text):
    """Creates a clickable instant communication bridge link"""
    cleaned_phone = "".join(filter(str.isdigit, str(phone_num)))
    encoded_text = urllib.parse.quote(message_text)
    return f"https://wa.me/{cleaned_phone}?text={encoded_text}"

if "admin_action_msg" in st.session_state:
    st.toast(st.session_state.admin_action_msg, icon="⚙️")
    del st.session_state.admin_action_msg

# ==========================================
# 4. SIDEBAR: OPERATOR LOCKBOX
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

# Build dynamic room pool depending on operator privileges
AVAILABLE_ROOMS = PUBLIC_ROOMS + ADMIN_ONLY_ROOMS if show_admin else PUBLIC_ROOMS

# ==========================================
# 5. MAIN INTERFACE LAYOUT
# ==========================================
if show_admin:
    tab1, tab2 = st.tabs(["📅 Schedule & Requests", "⚙️ Admins Hub"])
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

    # 📱 OPTIMIZED PHONE VIEW: SCROLLING TIMELINE FEED
    if view_type == "📱 Mobile Weekly List (Full Week)":
        st.markdown("#### 🔍 Jump to a Custom Week")
        start_date_selection = st.date_input("Show 7 days starting from:", datetime.date.today(), format="DD/MM/YYYY", key="mobile_date_picker")
        st.markdown("---")
        st.subheader("📋 Scheduled Allocations")
        
        upcoming_days = [start_date_selection + datetime.timedelta(days=i) for i in range(7)]
        has_any_bookings = False
        
        for target_date in upcoming_days:
            target_date_str = str(target_date)
            day_events = [b for b in raw_bookings if b['booking_date'] == target_date_str]
            
            day_header = target_date.strftime("%A (%d/%m/%Y)")
            if target_date == datetime.date.today():
                day_header = "⭐️ TODAY — " + day_header
            elif target_date == datetime.date.today() + datetime.timedelta(days=1):
                day_header = "➡️ TOMORROW — " + day_header
                
            if day_events:
                has_any_bookings = True
                st.markdown(f"### {day_header}")
                
                day_events = sort_events_engine(day_events)
                
                for b in day_events:
                    display_title = b['user_name']
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
                st.markdown("<br>", unsafe_allow_html=True)
                
        if not has_any_bookings:
            st.info(f"🟢 No room allocations booked for the 7-day window starting {start_date_selection.strftime('%d/%m/%Y')}.")

    # 🖥️ FULL CANVAS GRID WITH INTEGRATED CLICK LOOKUP
    else:
        calendar_events = []
        sorted_grid_bookings = sort_events_engine(raw_bookings)
        event_lookup = {}
        
        for b in sorted_grid_bookings:
            try:
                st_time_obj = datetime.datetime.strptime(b['start_time'], "%H:%M:%S")
                end_time_obj = datetime.datetime.strptime(b['end_time'], "%H:%M:%S")
                time_display = f"{st_time_obj.strftime('%I:%M %p')} - {end_time_obj.strftime('%I:%M %p')}"
            except:
                time_display = f"{b['start_time'][:5]} - {b['end_time'][:5]}"
                
            pure_title = b['user_name'].split(' (')[0] if ' (' in b['user_name'] else b['user_name']
            rich_grid_label = f"📝 {pure_title}\n⏰ {time_display}\n📍 {b['room_name']}"
            event_id = str(b['id'])
            
            calendar_events.append({
                "id": event_id,
                "title": rich_grid_label,
                "start": f"{b['booking_date']}T{b['start_time']}",
                "end": f"{b['booking_date']}T{b['end_time']}",
                "backgroundColor": "#bacfe6",  
                "borderColor": "#82a6d7",
                "textColor": "#1e293b"
            })
            
            event_lookup[event_id] = {
                "title": b['user_name'],
                "room": b['room_name'],
                "date": parse_to_ddmmyyyy(b['booking_date']),
                "time": time_display,
                "phone": b.get('user_email', 'N/A')
            }
            
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
            "snapDuration": "00:15:00",
            "slotEventOverlap": True, 
            "eventOrder": "start,title",
            "slotLabelFormat": {"hour": "numeric", "minute": "2-digit", "omitZeroMinute": False, "meridiem": "short", "hour12": True}
        }
        
        calendar_styles = """
            .fc-theme-standard .fc-col-header-cell { background-color: #82a6d7 !important; }
            .fc-col-header-cell-cushion { color: white !important; font-weight: 600 !important; padding: 6px 0 !important; font-size: 1rem; }
            .fc-theme-standard td, .fc-theme-standard th { border: 1px solid #e2e8f0 !important; }
            .fc-timegrid-slot-label-cushion { font-weight: 600 !important; font-size: 0.85rem !important; text-transform: uppercase; }
            .fc-timegrid-slots td { position: relative; }
            .fc-timegrid-events-container { margin: 0 !important; }
            
            .fc-timegrid-event-holder, .fc-timegrid-event, .fc-event { 
                background-color: #bacfe6 !important; 
                border-radius: 6px !important; 
                padding: 6px !important; 
                box-shadow: 1px 1px 4px rgba(0,0,0,0.08) !important;
                box-sizing: border-box !important;
                cursor: pointer !important;
            }
            .fc-timegrid-event { opacity: 0.98 !important; }
            .fc-event-main, .fc-event-title, .fc-event-title-container { 
                font-size: 11px !important; 
                font-weight: 700 !important; 
                line-height: 1.3 !important; 
                white-space: pre-wrap !important; 
                word-break: break-word !important; 
                color: #1e293b !important;
            }
            .fc-event-time { display: none !important; }
        """
        
        calendar_callback = calendar(events=calendar_events, options=calendar_options, custom_css=calendar_styles, key="booking_calendar")
        
        if calendar_callback and "eventClick" in calendar_callback:
            clicked_id = calendar_callback["eventClick"]["event"]["id"]
            if clicked_id in event_lookup:
                info = event_lookup[clicked_id]
                st.markdown("---")
                st.info("ℹ️ **Selected Event Details:**")
                meta_col1, meta_col2 = st.columns(2)
                with meta_col1:
                    st.markdown(f"### 👤 Group: **{info['title']}**")
                    st.markdown(f"#### 📍 Assigned Location: `{info['room']}`")
                with meta_col2:
                    st.markdown(f"#### 📅 Booked Date: **{info['date']}**")
                    st.markdown(f"#### ⏰ Timeline Windows: `{info['time']}`")
                    if info['phone'] and info['phone'] != "Admin Blockout":
                        st.markdown(f"📞 **Contact Reference:** {info['phone']}")
                st.markdown("---")
        
    st.markdown("---")
    st.subheader("Submit a New Booking Request")
    
    # PUBLIC BOOKING ENTRY FORM
    with st.form("request_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            booking_name = st.text_input("Event Name")
            contact_name = st.text_input("Your Name")
            contact_phone = st.text_input("Your Phone Number")
            room_selection = st.selectbox("Select Room", AVAILABLE_ROOMS)
        with col2:
            booking_date = st.date_input("Date (DD/MM/YYYY)", datetime.date.today(), format="DD/MM/YYYY")
            start_time_selection = st.time_input("Exact Start Time", value=datetime.time(9, 0))
            end_time_selection = st.time_input("Exact End Time", value=datetime.time(10, 0))
            
        submit_btn = st.form_submit_button("Submit Request")
        
        if submit_btn:
            if start_time_selection >= end_time_selection:
                st.error("Submission Denied: Your event start time cannot happen after or at the exact same time as your end time.", icon="⏰")
            elif booking_name and contact_name and contact_phone:
                data = {
                    "room_name": room_selection,
                    "booking_date": str(booking_date),
                    "start_time": start_time_selection.strftime("%H:%M:%S"),
                    "end_time": end_time_selection.strftime("%H:%M:%S"),
                    "user_name": f"{booking_name} ({contact_name})", 
                    "user_email": contact_phone,  
                    "status": "Pending"
                }
                supabase.table("bookings").insert(data).execute()
                st.success(f"🎉 SUCCESS! Your booking request for '{booking_name}' has been safely logged.")
                
                # 💬 CUSTOMER DISPATCH LINK GENERATOR
                formatted_req_date = booking_date.strftime("%d/%m/%Y")
                req_time_str = f"{start_time_selection.strftime('%I:%M %p')} - {end_time_selection.strftime('%I:%M %p')}"
                client_msg = f"Hi {contact_name}, your room booking request for *{booking_name}* ({room_selection}) on {formatted_req_date} from {req_time_str} has been successfully submitted and is currently *Pending Approval*. We will notify you shortly!"
                
                st.markdown(f'[💬 Click here to Send Submission Confirmation WhatsApp]( {generate_msg_link(contact_phone, client_msg)} )')
            else:
                st.error("Submission Failed: Please re-enter the details again.", icon="❌")

# ==========================================
# 6. ADMIN HUB (TAB 2)
# ==========================================
if show_admin and tab2 is not None:
    with tab2:
        st.subheader("Welcome to the Admin Hub!")
        
        # ACTIVE LIVE EDIT PARAMETERS ENGINE WITH INTEGRATED SEARCH
        st.markdown("### 📝 Edit Live Events")
        with st.expander("Click to open Live Engine", expanded=True):
            all_live = supabase.table("bookings").select("*").eq("status", "Approved").execute()
            live_list = sort_events_engine(all_live.data) if all_live else []
            
            if not live_list:
                st.info("No active events currently booked to modify.")
            else:
                tweak_search = st.text_input("🔍 Search Event to Edit (Type event name, room, or date...)", key="tweak_search_box")
                
                filtered_tweak_list = []
                for ev in live_list:
                    formatted_d = parse_to_ddmmyyyy(ev['booking_date'])
                    search_string = f"{ev['user_name']} {ev['room_name']} {formatted_d}".lower()
                    if tweak_search.strip() == "" or tweak_search.lower() in search_string:
                        filtered_tweak_list.append(ev)
                
                if not filtered_tweak_list:
                    st.warning("No matching active events found matching your search term.")
                else:
                    event_options = {f"{parse_to_ddmmyyyy(ev['booking_date'])} | {ev['room_name']} — {ev['user_name']}": ev for ev in filtered_tweak_list}
                    selected_event_key = st.selectbox("Choose an Event to Edit", list(event_options.keys()))
                    
                    if selected_event_key:
                        target_event = event_options[selected_event_key]
                        
                        with st.
