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
        
        /* 👁️ CRISP VISIBILITY PATCH FOR INPUT FIELDS */
        div[data-testid="stForm"] input, 
        div[data-testid="stForm"] select, 
        div[data-testid="stForm"] div[role="combobox"] {
            color: #1e293b !important;
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
        }
        
        /* Ensures dropdown text and calendar picker text stays dark */
        div[data-baseweb="select"] *, div[data-baseweb="calendar"] * {
            color: #1e293b !important;
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

        /* 📱 Responsive view container rules */
        @media screen and (max-width: 768px) {
            .main-title { font-size: 1.8rem; }
        }
    </style>
""", unsafe_allow_html=True)

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

# ==========================================
# 3. SIDEBAR: OPERATOR GATEWAY
# ==========================================
with st.sidebar:
    st.markdown("### 🔒 Staff Gateway")
    show_admin = False
    
    passcode_input = st.text_input("Portal Key", type="password", placeholder="Enter authorization key...")
    if passcode_input == ADMIN_PASSCODE:
        st.success("Operator Access Granted")
        show_admin = True
    elif passcode_input != "":
        st.error("Access Denied")

# ==========================================
# MAIN INTERFACE LAYOUT
# ==========================================
if show_admin:
    tab1, tab2 = st.tabs(["📅 Schedule & Requests", "⚙️ Manager Controls"])
else:
    tab1 = st.container()
    tab2 = None

# ------------------------------------------
# VIEW 1: DUAL-DISPLAY LAYOUT (MOBILE FRIENDLY)
# ------------------------------------------
with tab1:
    raw_bookings = get_bookings()
    
    # Let users choose their viewport style or default to automated presentation
    view_type = st.radio(
        "Select Calendar Layout Style:",
        ["📱 Mobile Agenda List (Best for Phones)", "🖥️ Full Calendar Grid (Best for Desktop/Tablets)"],
        horizontal=True
    )
    
    st.markdown("---")

    # ---- MODE A: MOBILE AGENDA LIST (CLEAN, LARGE, BULLETPROOF TEXT CARDS) ----
    if view_type == "📱 Mobile Agenda List (Best for Phones)":
        st.subheader("🗓️ Scheduled Allocations")
        
        filter_date = st.date_input("Filter Agenda by Date:", datetime.date.today(), format="DD/MM/YYYY")
        selected_date_str = str(filter_date)
        
        day_events = [b for b in raw_bookings if b['booking_date'] == selected_date_str]
        
        if not day_events:
            st.info("🟢 No active room allocations scheduled for this date. Available all day!")
        else:
            # Sort events cleanly by start time
            day_events = sorted(day_events, key=lambda x: x['start_time'])
            
            for b in day_events:
                display_title = b['user_name'].split(" (")[0] if " (" in b['user_name'] else b['user_name']
                try:
                    st_time = datetime.datetime.strptime(b['start_time'], "%H:%M:%S").strftime("%I:%M %p")
                    en_time = datetime.datetime.strptime(b['end_time'], "%H:%M:%S").strftime("%I:%M %p")
                    time_display = f"{st_time} - {en_time}"
                except:
                    time_display = f"{b['start_time'][:5]} - {b['end_time'][:5]}"
                
                # Render a thick container card rearranged to Event -> Time -> Room
                st.markdown(f"""
                    <div style="
                        background-color: #f8fafc;
                        border-left: 6px solid #82a6d7;
                        padding: 15px;
                        border-radius: 8px;
                        margin-bottom: 12px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    ">
                        <div style="font-size: 1.15rem; font-weight: 700; color: #1e293b; margin-bottom: 4px;">
                            👤 Event: {display_title}
                        </div>
                        <div style="font-size: 1.05rem; font-weight: 600; color: #475569;">
                            ⏰ {time_display}
                        </div>
                        <div style="font-size: 0.95rem; font-weight: 500; color: #64748b; margin-top: 2px;">
                            📍 Room: {b['room_name']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    # ---- MODE B: STANDARD FULL CALENDAR GRID FOR LARGE DESKTOPS ----
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
                
            # Rearranged text label directly inside the FullCalendar generation line
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
            # Converts the left axis timeline labels inside the calendar grid to 12h AM/PM
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
                st.success("🎉 Request submitted successfully! It is now awaiting Admin approval.")
                st.rerun()
            else:
                st.error("Please fill out all fields before submitting.")

# ------------------------------------------
# VIEW 2: HIDDEN MANAGER CONTROLS
# ------------------------------------------
if show_admin and tab2 is not None:
    with tab2:
        st.subheader("Manager Portal")
        
        # Tool 1: Live Tweak Engine
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
                        st.markdown("**Update Values Below:**")
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
                            st.toast("✨ Live event updated successfully!", icon="✅")
                            st.rerun()

        st.markdown("---")
        
        # Tool 2: Recurring Blocks
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
                    st.toast(f"✨ Published {weeks_count} recurring weeks!", icon="🔄")
                    st.rerun()

        st.markdown("---")
        
        # Tool 3: Quick SMS Text Dispatcher
        st.markdown("### 💬 Quick SMS Text Dispatcher")
        with st.expander("Click to open Quick Text Portal"):
            all_current = supabase.table("bookings").select("*").execute()
            current_data = all_current.data if all_current else []
            
            if not current_data:
                st.info("No bookings found to contact.")
            else:
                contact_options = {
                    f"{ev['booking_date']} | {ev['user_name']} ({ev['user_email']})": ev 
                    for ev in current_data if ev['user_email'] and ev['user_email'] != "Admin Blockout"
                }
                
                if not contact_options:
                    st.info("No custom user phone entries found to text.")
                else:
                    selected_contact = st.selectbox("Who do you want to message?", list(contact_options.keys()))
                    sms_target = contact_options[selected_contact]
                    
                    default_msg = f"Hi, regarding your booking for '{sms_target['user_name'].split(' (')[0]}' on {sms_target['booking_date']}: "
                    sms_body = st.text_area("Write your text message here:", value=default_msg)
                    
                    clean_phone = "".join(filter(str.isdigit, sms_target['user_email']))
                    encoded_text = urllib.parse.quote(sms_body)
                    
                    sms_url = f"sms:{clean_phone}&body={encoded_text}"
                    st.markdown(f'<a href="{sms_url}" class="sms-btn">📱 Launch Text Message on Phone</a>', unsafe_allow_html=True)

        st.markdown("---")
        
        # Tool 4: Pending Approvals
        st.markdown("### 📋 Pending Approval Requests")
        pending_res = supabase.table("bookings").select("*").eq("status", "Pending").execute()
        pending_bookings = pending_res.data if pending_res else []
        
        if not pending_bookings:
            st.info("No pending booking requests at the moment.")
        else:
            for pb in pending_bookings:
                with st.container():
                    st.markdown(f"#### {pb['user_name']} ({pb['room_name']})")
                    st.text(f"📱 Phone Number: {pb['user_email']}") 
                    
                    try:
                        parsed_date = datetime.datetime.strptime(pb['booking_date'], "%Y-%m-%d").strftime("%d/%m/%Y")
                    except:
                        parsed_date = pb['booking_date']
                        
                    st.text(f"📅 Date & Time: {parsed_date} | {pb['start_time'][:5]} - {pb['end_time'][:5]}")
                    
                    col_app, col_rej, _ = st.columns([1, 1, 4])
                    if col_app.button("Approve", key=f"app_{pb['id']}"):
                        supabase.table("bookings").update({"status": "Approved"}).eq("id", pb['id']).execute()
                        st.rerun()
                    if col_rej.button("Reject", key=f"rej_{pb['id']}"):
                        supabase.table("bookings").update({"status": "Rejected"}).eq("id", pb['id']).execute()
                        st.rerun()
                st.markdown("---")

        # Tool 5: Deletion Panel
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
                            st.rerun()
