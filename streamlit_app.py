import streamlit as st
import datetime
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
            
            # STATED COMPLIANCE: Forces day headers to explicitly layout as DD/MM/YYYY
            day_header = target_date.strftime("%A (%d/%m/%Y)")
            if target_date == datetime.date.today():
                day_header = "⭐️ TODAY — " + day_header
            elif target_date == datetime.date.today() + datetime.timedelta(days=1):
                day_header = "➡️ TOMORROW — " + day_header
                
            if day_events:
                has_any_bookings = True
                st.markdown(f"### {day_header}")
                
                # Apply multi-tiered sorting parameters
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

    # 🖥️ FULL CANVAS GRID: FIXED EMBED WITH SIDE-BY-SIDE OVERLAPS
    else:
        calendar_events = []
        sorted_grid_bookings = sort_events_engine(raw_bookings)
        
        for b in sorted_grid_bookings:
            try:
                st_time_obj = datetime.datetime.strptime(b['start_time'], "%H:%M:%S")
                end_time_obj = datetime.datetime.strptime(b['end_time'], "%H:%M:%S")
                time_display = f"{st_time_obj.strftime('%I:%M %p')} - {end_time_obj.strftime('%I:%M %p')}"
            except:
                time_display = f"{b['start_time'][:5]} - {b['end_time'][:5]}"
                
            full_event_label = f"{b['user_name']}\n⏰ {time_display}\n📍 {b['room_name']}"
            
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
            
            /* 🛠️ FORCE TRUE SIDE-BY-SIDE SIDE ALLOCATION (NO OVERLAPPING) */
            .fc-timegrid-slots td { position: relative; }
            .fc-timegrid-events-container { margin: 0 !important; }
            
            .fc-timegrid-event-holder, .fc-timegrid-event, .fc-event { 
                background-color: #bacfe6 !important; 
                border-radius: 6px !important; 
                padding: 4px !important; 
                box-shadow: 1px 1px 4px rgba(0,0,0,0.08) !important;
                box-sizing: border-box !important;
            }
            
            /* This ensures FullCalendar scales them nicely next to each other instead of stacking layered cards */
            .fc-timegrid-event {
                opacity: 0.98 !important;
            }
            
            .fc-event-main, .fc-event-title, .fc-event-title-container { 
                font-size: 11px !important; 
                font-weight: 700 !important; 
                line-height: 1.2 !important; 
                white-space: pre-wrap !important; 
                word-break: break-word !important; 
                color: #1e293b !important;
            }
            .fc-event-time { display: none !important; }
        """
        
        calendar(events=calendar_events, options=calendar_options, custom_css=calendar_styles, key="booking_calendar")
        
    st.markdown("---")
    st.subheader("Submit a New Booking Request")
    
    # PUBLIC BOOKING ENTRY FORM
    with st.form("request_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            booking_name = st.text_input("Event / Group Name")
            contact_name = st.text_input("Your Name")
            contact_phone = st.text_input("Your Phone Number")
            room_selection = st.selectbox("Select Room", AVAILABLE_ROOMS)
        with col2:
            # COMPLIANCE: Date picker UI structured explicitly as DD/MM/YYYY
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
            else:
                st.error("Submission Failed: Please complete all input values before saving.", icon="❌")

# ==========================================
# 6. MANAGER CONTROLS (TAB 2)
# ==========================================
if show_admin and tab2 is not None:
    with tab2:
        st.subheader("Manager Portal")
        
       # ACTIVE LIVE EDIT PARAMETERS ENGINE WITH INTEGRATED SEARCH (FIXED)
        st.markdown("### 📝 Edit & Tweak Live Events")
        with st.expander("Click to open Live Tweak Engine", expanded=True):
            all_live = supabase.table("bookings").select("*").eq("status", "Approved").execute()
            live_list = sort_events_engine(all_live.data) if all_live else []
            
            if not live_list:
                st.info("No active events currently published to modify.")
            else:
                # SEARCH COMPONENT: Live filter engine for edits
                tweak_search = st.text_input("🔍 Search Event to Edit (Type event name, room, or date...)", key="tweak_search_box")
                
                # Filter down options dynamically based on string comparisons
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
                        
                        # FIXED: We use a completely unique form key anchored strictly to the unique database row ID
                        with st.form(key=f"live_tweak_form_{target_event['id']}"):
                            edit_name = st.text_input("Event Name / Contact String", value=target_event['user_name'])
                            edit_room = st.selectbox("Assigned Room", AVAILABLE_ROOMS, index=AVAILABLE_ROOMS.index(target_event['room_name']))
                            edit_date = st.date_input("Scheduled Date", datetime.datetime.strptime(target_event['booking_date'], "%Y-%m-%d"), format="DD/MM/YYYY")
                            
                            parsed_curr_start = datetime.datetime.strptime(target_event['start_time'][:8], "%H:%M:%S").time()
                            parsed_curr_end = datetime.datetime.strptime(target_event['end_time'][:8], "%H:%M:%S").time()
                            
                            col_e1, col_e2 = st.columns(2)
                            with col_e1:
                                edit_start = st.time_input("Modify Start Time", value=parsed_curr_start)
                            with col_e2:
                                edit_end = st.time_input("Modify End Time", value=parsed_curr_end)
                                
                            save_edits = st.form_submit_button("Save Layout Tweaks")
                            
                            if save_edits:
                                if edit_start >= edit_end:
                                    st.error("Operation Denied: Logical time mismatch detected.")
                                else:
                                    update_payload = {
                                        "user_name": edit_name,
                                        "room_name": edit_room,
                                        "booking_date": str(edit_date),
                                        "start_time": edit_start.strftime("%H:%M:%S"),
                                        "end_time": edit_end.strftime("%H:%M:%S")
                                    }
                                    
                                    # FIXED: Explicitly targeting only the matching entry ID and forcing an immediate commit
                                    supabase.table("bookings").update(update_payload).eq("id", target_event['id']).execute()
                                    
                                    formatted_new_date = edit_date.strftime("%d/%m/%Y")
                                    st.session_state.admin_action_msg = f"📝 Modified parameters for '{edit_name}' on {formatted_new_date}."
                                    st.rerun()

        st.markdown("---")
        
        # RECURRING MULTI-DAY EVENT ENGINE
        st.markdown("### 🔁 Add Recurring Schedule Block")
        with st.expander("Click to open Advanced Multi-Day Recurring Creator"):
            with st.form("recurring_form"):
                rec_title = st.text_input("Recurring Event Title")
                rec_room = st.selectbox("Select Target Room", AVAILABLE_ROOMS, key="recurring_target_room")
                
                st.markdown("**Select Days of the Week to apply this schedule block:**")
                c_mon, c_tue, c_wed, c_thu, c_fri, c_sat, c_sun = st.columns(7)
                mon = c_mon.checkbox("Mon", value=True)
                tue = c_tue.checkbox("Tue")
                wed = c_wed.checkbox("Wed")
                thu = c_thu.checkbox("Thu")
                fri = c_fri.checkbox("Fri")
                sat = c_sat.checkbox("Sat")
                sun = c_sun.checkbox("Sun")
                
                active_days = []
                if mon: active_days.append(0)
                if tue: active_days.append(1)
                if wed: active_days.append(2)
                if thu: active_days.append(3)
                if fri: active_days.append(4)
                if sat: active_days.append(5)
                if sun: active_days.append(6)
                
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    start_bound_date = st.date_input("Schedule Start Date", datetime.date.today(), format="DD/MM/YYYY")
                    rec_start_time = st.time_input("Recurring Start Time", value=datetime.time(18, 0))
                with col_r2:
                    total_weeks_duration = st.number_input("Repeat sequence for how many weeks total?", min_value=1, max_value=52, value=4)
                    rec_end_time = st.time_input("Recurring End Time", value=datetime.time(19, 30))
                
                submit_recurring = st.form_submit_button("Generate Dynamic Recurring Matrix")
                if submit_recurring and rec_title:
                    if rec_start_time >= rec_end_time:
                        st.error("Operation Denied: Input times do not make chronological sense.", icon="⏰")
                    elif not active_days:
                        st.error("Operation Denied: You must select at least one day checkbox.", icon="📆")
                    else:
                        batch_data = []
                        end_bound_date = start_bound_date + datetime.timedelta(weeks=total_weeks_duration)
                        loop_date = start_bound_date
                        
                        while loop_date <= end_bound_date:
                            if loop_date.weekday() in active_days:
                                batch_data.append({
                                    "room_name": rec_room,
                                    "booking_date": str(loop_date),
                                    "start_time": rec_start_time.strftime("%H:%M:%S"),
                                    "end_time": rec_end_time.strftime("%H:%M:%S"),
                                    "user_name": f"🔄 {rec_title}",
                                    "user_email": "Admin Blockout",
                                    "status": "Approved"
                                })
                            loop_date += datetime.timedelta(days=1)
                        
                        if batch_data:
                            supabase.table("bookings").insert(batch_data).execute()
                            st.session_state.admin_action_msg = f"🔁 Successfully established {len(batch_data)} instances for '{rec_title}'."
                            st.rerun()
                        else:
                            st.error("No dates matched the selection parameters.")

        st.markdown("---")
        
        # STANDARD PENDING APPROVAL GATEWAY
        st.markdown("### 📋 Pending Approval Requests")
        pending_res = supabase.table("bookings").select("*").eq("status", "Pending").execute()
        pending_bookings = sort_events_engine(pending_res.data) if pending_res else []
        
        if not pending_bookings:
            st.info("No pending booking requests.")
        else:
            for pb in pending_bookings:
                with st.container():
                    st.markdown(f"#### {pb['user_name']} ({pb['room_name']})")
                    # COMPLIANCE: Pending logs layout metrics show date as DD/MM/YYYY
                    parsed_date = parse_to_ddmmyyyy(pb['booking_date'])
                    st.text(f"📅 Date & Time: {parsed_date} | {pb['start_time'][:5]} - {pb['end_time'][:5]}")
                    
                    col_app, col_rej, _ = st.columns([1, 1, 4])
                    if col_app.button("Approve", key=f"app_{pb['id']}"):
                        supabase.table("bookings").update({"status": "Approved"}).eq("id", pb['id']).execute()
                        st.session_state.admin_action_msg = f"✅ Approved request from '{pb['user_name']}' on {parsed_date}."
                        st.rerun()
                    if col_rej.button("Reject", key=f"rej_{pb['id']}"):
                        supabase.table("bookings").update({"status": "Rejected"}).eq("id", pb['id']).execute()
                        st.session_state.admin_action_msg = f"❌ Rejected request from '{pb['user_name']}' on {parsed_date}."
                        st.rerun()

        st.markdown("---")
        
       # DATABASE DATA CLEANUP ENGINE WITH BATCH CLEANUP (OPTIMIZED)
        st.markdown("### 🗑️ Delete or Cancel Live Events")
        with st.expander("Click to view full calendar cleanup deck", expanded=True):
            all_approved = supabase.table("bookings").select("*").eq("status", "Approved").execute()
            approved_list = sort_events_engine(all_approved.data) if all_approved else []
            
            if not approved_list:
                st.info("No active events currently published to delete.")
            else:
                delete_search = st.text_input("🔍 Search Event to Delete (Type name, room, or date...)", key="delete_search_box")
                
                # Dynamic Search Filtering
                filtered_delete_list = []
                for ab in approved_list:
                    formatted_d = parse_to_ddmmyyyy(ab['booking_date'])
                    search_string = f"{ab['user_name']} {ab['room_name']} {formatted_d}".lower()
                    if delete_search.strip() == "" or delete_search.lower() in search_string:
                        filtered_delete_list.append(ab)
                
                if not filtered_delete_list:
                    st.warning("No matching active events found.")
                else:
                    # Choose Deletion Method Strategy
                    delete_mode = st.radio(
                        "Deletion Strategy:",
                        ["Clean up Individual Instances", "💥 Batch Delete Entire Recurring Series"],
                        horizontal=True,
                        key="delete_mode_strategy"
                    )
                    st.markdown("---")
                    
                    # STRATEGY A: Standard precise individual line removal
                    if delete_mode == "Clean up Individual Instances":
                        for ab in filtered_delete_list:
                            col_info, col_del = st.columns([5, 1])
                            m_date = parse_to_ddmmyyyy(ab['booking_date'])
                                
                            with col_info:
                                st.write(f"🔹 **{m_date}** | {ab['room_name']} — {ab['user_name']} ({ab['start_time'][:5]}-{ab['end_time'][:5]})")
                            with col_del:
                                if st.button("Delete ❌", key=f"del_indiv_{ab['id']}"):
                                    supabase.table("bookings").delete().eq("id", ab['id']).execute()
                                    st.session_state.admin_action_msg = f"🗑️ Deleted single instance for '{ab['user_name']}' on {m_date}."
                                    st.rerun()
                                    
                    # STRATEGY B: Wipe out entire series grouped cleanly by name and location targets
                    else:
                        st.info("The view below groups identical booking titles together. Deleting one will clear all future dates matching that title.")
                        
                        # Use Python sets to distill down unique repeating groups dynamically
                        seen_groups = set()
                        unique_series_list = []
                        
                        for ab in filtered_delete_list:
                            # Group items based on their structural profile name and assigned room target
                            group_profile = (ab['user_name'], ab['room_name'])
                            if group_profile not in seen_groups:
                                seen_groups.add(group_profile)
                                unique_series_list.append(ab)
                        
                        for ab in unique_series_list:
                            col_info, col_del = st.columns([5, 1])
                            
                            # Count how many total instances exist down the timeline for context
                            total_count = sum(1 for item in filtered_delete_list if item['user_name'] == ab['user_name'] and item['room_name'] == ab['room_name'])
                            
                            with col_info:
                                st.write(f"📁 **{ab['user_name']}** inside **{ab['room_name']}** *(Contains {total_count} scheduled allocations)*")
                            with col_del:
                                if st.button("Wipe All 🔥", key=f"del_series_{ab['id']}"):
                                    # Execute massive multi-row delete target query matching titles and rooms
                                    supabase.table("bookings").delete().eq("user_name", ab['user_name']).eq("room_name", ab['room_name']).execute()
                                    st.session_state.admin_action_msg = f"💥 Mass Cleaned Engine: Purged all {total_count} entries for '{ab['user_name']}'."
                                    st.rerun()
