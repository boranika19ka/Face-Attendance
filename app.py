import streamlit as st
import cv2
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os
from PIL import Image

import database as db
import face_utils as fu
import styles as stl
from streamlit_option_menu import option_menu
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
import queue
import av

RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

# Page config
st.set_page_config(
    page_title="Face Recognition System",
    page_icon="None",
    layout="wide",
    initial_sidebar_state="auto"
)

# Initialize session state
if 'admin_logged_in' not in st.session_state:
    st.session_state['admin_logged_in'] = False

# Initialize database
db.init_db()

# Apply styles
current_theme = db.get_setting("theme")
if not current_theme:
    current_theme = "dark"
stl.apply_styles(current_theme)

# Navigation
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #58a6ff;'>Face Recognition System</h2>", unsafe_allow_html=True)
    
    menu = option_menu(
        menu_title=None,
        options=["Dashboard", "Scan Attendance", "Register Student", "Attendance Records", "Admin", "Settings"],
        icons=["grid", "camera", "person-plus", "table", "shield-lock", "gear"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#161b22"},
            "icon": {"color": "#8b949e", "font-size": "18px"}, 
            "nav-link": {
                "font-size": "16px", 
                "text-align": "left", 
                "margin": "0px", 
                "color": "#f0f6fc",
                "--hover-color": "#30363d"
            },
            "nav-link-selected": {"background-color": "#007bff"},
        }
    )
    st.markdown("---")

# Helper for Time Status
def get_status(current_time, start_time_str):
    try:
        current_time_obj = datetime.strptime(current_time, "%H:%M:%S").time()
        start_time_obj = datetime.strptime(start_time_str, "%H:%M").time()
        
        if current_time_obj <= start_time_obj:
            return "On Time"
        else:
            return "Late"
    except Exception as e:
        return "On Time"

# --- PAGES ---

if menu == "Dashboard":
    st.markdown("<div class='title-container'><h1>System Dashboard</h1></div>", unsafe_allow_html=True)
    
    stats = db.get_dashboard_stats()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        stl.metric_card("Total Students", stats['total_students'], "")
    with col2:
        stl.metric_card("Today Attendance", stats['today_attendance'], "")
    with col3:
        stl.metric_card("Late Students", stats['late_today'], "")
        
    st.markdown("### Quick Summary")
    recent_attendance = db.get_attendance_records().head(5)
    if not recent_attendance.empty:
        col_table, col_chart = st.columns([1, 1])
        with col_table:
            st.table(recent_attendance)
        with col_chart:
            # Prepare data for chart
            trend_df = db.get_attendance_trends()
            if not trend_df.empty:
                chart_data = trend_df.pivot(index='date', columns='status', values='count').fillna(0)
                st.bar_chart(chart_data)
            else:
                st.info("No trend data available.")
    else:
        st.info("No attendance records for today yet.")

elif menu == "Register Student":
    st.markdown("<div class='title-container'><h1>Register New Student</h1></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Student Details")
        student_id = st.text_input("Student ID (e.g., S101)")
        full_name = st.text_input("Full Name")
        department = st.selectbox("Department", ["Computer Science", "Engineering", "Business", "Arts", "Science"])
        
        if st.button("Submit & Capture Face"):
            if student_id and full_name:
                # Store details temporarily
                st.session_state['temp_student'] = {
                    "id": student_id,
                    "name": full_name,
                    "dept": department
                }
                st.success("Details saved! Now capture the face.")
            else:
                st.error("Please fill all details.")

    with col2:
        st.markdown("### Face Capture")
        if 'temp_student' in st.session_state:
            method = st.radio("Choose Method", ["Live Camera", "Upload Photo"], horizontal=True)
            
            img_file = None
            if method == "Live Camera":
                img_file = st.camera_input("Capture Student Photo")
            else:
                img_file = st.file_uploader("Upload Student Photo", type=['jpg', 'jpeg', 'png'])
            
            if img_file:
                # Save image
                student_data = st.session_state['temp_student']
                img_path = f"faces/{student_data['id']}.jpg"
                
                # Ensure faces directory exists
                os.makedirs(os.path.dirname(img_path), exist_ok=True)
                
                with open(img_path, "wb") as f:
                    f.write(img_file.getbuffer())
                
                # Register face
                with st.spinner("Processing face encoding..."):
                    success = fu.register_face(student_data['id'], img_path)
                    if success:
                        db_success = db.add_student(student_data['id'], student_data['name'], student_data['dept'])
                        if db_success:
                            st.success(f"Student {student_data['name']} registered successfully!")
                            del st.session_state['temp_student']
                        else:
                            st.error("Student ID already exists in database.")
                    else:
                        st.error("No face detected in the photo. Please try again.")
        else:
            st.info("Please fill the details on the left first.")

elif menu == "Scan Attendance":
    st.markdown("<div class='title-container'><h1>Live Face Attendance</h1></div>", unsafe_allow_html=True)
    
    start_time_cfg = db.get_setting("start_time")
    known_encodings = fu.load_encodings()
    
    if not known_encodings:
        st.warning("No students registered yet. Please register students first.")
    else:
        col_cam, col_info = st.columns([2, 1])
        
        with col_cam:
            st.markdown("### Live Scanner")
            
            class FaceProcessor:
                def __init__(self):
                    self.known_encodings = known_encodings
                    self.start_time_cfg = start_time_cfg
                    self.recognized_ids = queue.Queue()

                def recv(self, frame):
                    img = frame.to_ndarray(format="bgr24")
                    
                    # Recognize faces
                    results = fu.recognize_face(img, self.known_encodings)
                    
                    for res in results:
                        top, right, bottom, left = res['location']
                        student_id = res['id']
                        
                        # Draw box
                        color = (88, 166, 255) if student_id != "Unknown" else (255, 123, 114)
                        cv2.rectangle(img, (left, top), (right, bottom), color, 2)
                        
                        if student_id != "Unknown":
                            cv2.putText(img, "Recognized", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (88, 166, 255), 2)
                            self.recognized_ids.put(student_id)
                        else:
                            cv2.putText(img, "Unknown", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 123, 114), 2)
                            
                    return av.VideoFrame.from_ndarray(img, format="bgr24")

            webrtc_ctx = webrtc_streamer(
                key="face-recognition",
                mode=WebRtcMode.SENDRECV,
                rtc_configuration=RTC_CONFIGURATION,
                video_processor_factory=FaceProcessor,
                async_processing=True,
            )

        with col_info:
            st.markdown("### Last Recognized")
            info_placeholder = st.empty()
            info_placeholder.info("System Ready. Waiting for face...")
            
            st.markdown("### Live Activity Log")
            log_placeholder = st.empty()
            
            # Show initial records
            initial_records = db.get_attendance_records().head(10)
            if not initial_records.empty:
                log_placeholder.dataframe(initial_records[['name', 'time', 'status']], use_container_width=True, hide_index=True)
            else:
                log_placeholder.info("No scans yet today.")

        # Process results from the processor's queue
        if webrtc_ctx.video_processor:
            try:
                while True:
                    recognized_id = webrtc_ctx.video_processor.recognized_ids.get_nowait()
                    
                    # Fetch student info
                    all_students = db.get_all_students()
                    student_row = all_students[all_students['student_id'] == recognized_id]
                    
                    if not student_row.empty:
                        name = student_row['name'].values[0]
                        dept = student_row['department'].values[0]
                        
                        now_time = datetime.now().strftime("%H:%M:%S")
                        status = get_status(now_time, start_time_cfg)
                        
                        if db.log_attendance(recognized_id, status):
                            st.toast(f"Attendance Logged: {name}")
                            
                            # Update logs
                            updated_records = db.get_attendance_records().head(10)
                            log_placeholder.dataframe(updated_records[['name', 'time', 'status']], use_container_width=True, hide_index=True)
                            
                            with col_info:
                                info_placeholder.markdown(f"""
                                    <div class='metric-card' style='border-left: 5px solid #238636;'>
                                        <h4 style='color: #58a6ff; margin:0;'>{name}</h4>
                                        <p style='color: #8b949e; margin:0;'>ID: {recognized_id}</p>
                                        <p style='color: #8b949e; margin:0;'>Dept: {dept}</p>
                                        <hr style='margin: 10px 0; border-color: #30363d;'>
                                        <div style='display: flex; justify-content: space-between;'>
                                            <span style='color: #f0f6fc;'>Time: {now_time}</span>
                                            <span style='color: {"#238636" if status == "On Time" else "#da3633"}; font-weight: bold;'>{status}</span>
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)
            except queue.Empty:
                pass
            
            # Automatically refresh to check the queue again
            from streamlit_autorefresh import st_autorefresh
            st_autorefresh(interval=2000, key="attendance_refresh")

elif menu == "Attendance Records":
    st.markdown("<div class='title-container'><h1>Attendance Records</h1></div>", unsafe_allow_html=True)
    
    records = db.get_attendance_records()
    
    if not records.empty:
        # Advanced Filters
        with st.expander("🔍 Filter Controls", expanded=True):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                search = st.text_input("Search Student (Name or ID)")
            with col2:
                # Default to last 7 days
                default_start = datetime.now() - timedelta(days=7)
                default_end = datetime.now()
                date_range = st.date_input("Date Range", value=(default_start, default_end))
            with col3:
                status_filter = st.multiselect("Status", ["On Time", "Late"], default=["On Time", "Late"])
        
        # Apply Filters
        filtered_df = records.copy()
        
        if search:
            filtered_df = filtered_df[filtered_df['name'].str.contains(search, case=False) | 
                                    filtered_df['student_id'].str.contains(search, case=False)]
        
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df = filtered_df[(filtered_df['date'] >= str(start_date)) & (filtered_df['date'] <= str(end_date))]
        elif isinstance(date_range, datetime): # fallback for single date
            filtered_df = filtered_df[filtered_df['date'] == str(date_range)]
            
        if status_filter:
            filtered_df = filtered_df[filtered_df['status'].isin(status_filter)]
            
        # Summary Metrics
        st.markdown("### Selection Summary")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            stl.metric_card("Total Scans", len(filtered_df), "")
        with m2:
            stl.metric_card("Students", filtered_df['student_id'].nunique(), "")
        with m3:
            stl.metric_card("On Time", len(filtered_df[filtered_df['status'] == 'On Time']), "✅")
        with m4:
            stl.metric_card("Late", len(filtered_df[filtered_df['status'] == 'Late']), "❌")
            
        # Visual Breakdown
        if not filtered_df.empty:
            col_table, col_chart = st.columns([2, 1])
            with col_table:
                st.dataframe(filtered_df, use_container_width=True, hide_index=True)
            with col_chart:
                st.markdown("#### Status Distribution")
                status_counts = filtered_df['status'].value_counts()
                st.bar_chart(status_counts)
        
        # Export
        if not filtered_df.empty:
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Filtered Data to CSV",
                data=csv,
                file_name=f"attendance_filtered_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv',
                use_container_width=True
            )
    else:
        st.info("No attendance records found.")

elif menu == "Settings":
    st.markdown("<div class='title-container'><h1>System Settings</h1></div>", unsafe_allow_html=True)
    
    if st.session_state['admin_logged_in']:
        current_start_time = db.get_setting("start_time")
        new_start_time = st.time_input("School Start Time (for Late checking)", value=datetime.strptime(current_start_time, "%H:%M").time())
        
        current_theme_cfg = db.get_setting("theme")
        new_theme = st.selectbox("Application Theme", ["dark", "light"], index=0 if current_theme_cfg == "dark" else 1)
        
        if st.button("Save Settings"):
            db.update_setting("start_time", new_start_time.strftime("%H:%M"))
            db.update_setting("theme", new_theme)
            st.success("Settings updated successfully!")
            st.rerun()
    else:
        st.warning("🔐 Admin Access Only")
        st.info("Please log in through the **Admin** menu to change system settings.")

elif menu == "Admin":
    st.markdown("<div class='title-container'><h1>Admin Management</h1></div>", unsafe_allow_html=True)
    
    if not st.session_state['admin_logged_in']:
        # Login Form
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
                <div style='background-color: #161b22; padding: 30px; border-radius: 15px; border: 1px solid #30363d;'>
                    <h3 style='text-align: center; color: #58a6ff;'>Secure Login</h3>
                </div>
            """, unsafe_allow_html=True)
            
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            
            if st.button("Login"):
                if user == "admin" and pwd == "admin123": # Simple secure default
                    st.session_state['admin_logged_in'] = True
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
    else:
        # Admin Dashboard
        st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"admin_logged_in": False}))
        
        tab1, tab2, tab3 = st.tabs(["Student Management", "Attendance Logs", "⚠️ Warning List"])
        
        with tab1:
            st.markdown("### Manage Students")
            students_df = db.get_students_summary()
            
            if not students_df.empty:
                # Use data_editor for editing
                edited_df = st.data_editor(
                    students_df,
                    column_config={
                        "student_id": st.column_config.TextColumn("ID", disabled=True),
                        "on_time_count": st.column_config.NumberColumn("On Time ✅", disabled=True),
                        "late_count": st.column_config.NumberColumn("Late ❌", disabled=True),
                        "registration_date": st.column_config.TextColumn("Registered", disabled=True),
                    },
                    num_rows="fixed",
                    use_container_width=True,
                    key="student_editor"
                )
                
                # Update button
                if st.button("Save Changes"):
                    # Compare and update
                    for index, row in edited_df.iterrows():
                        orig_row = students_df.iloc[index]
                        if row['name'] != orig_row['name'] or row['department'] != orig_row['department']:
                            db.update_student(row['student_id'], row['name'], row['department'])
                    st.success("Student records updated!")
                
                st.markdown("---")
                st.markdown("### Delete Student")
                delete_id = st.selectbox("Select Student to Remove", students_df['student_id'].tolist())
                if st.button("Delete Student", type="primary"):
                    if db.delete_student(delete_id):
                        fu.delete_student_face(delete_id)
                        st.success(f"Student {delete_id} removed.")
                        st.rerun()
            else:
                st.info("No students registered.")
        
        with tab2:
            st.markdown("### Attendance Records")
            records = db.get_all_attendance_with_id()
            
            if not records.empty:
                # Filter records
                search_id = st.text_input("Search Student ID", key="admin_search")
                if search_id:
                    records = records[records['student_id'].str.contains(search_id, case=False)]
                
                # Show with delete option
                st.markdown("""
                    <div style='display: flex; background-color: #0d1117; padding: 10px; border-radius: 5px; margin-bottom: 10px; border: 1px solid #30363d; font-weight: bold;'>
                        <div style='flex: 1;'>Name</div>
                        <div style='flex: 1;'>ID</div>
                        <div style='flex: 1;'>Time</div>
                        <div style='flex: 1;'>Status</div>
                        <div style='width: 80px;'>Action</div>
                    </div>
                """, unsafe_allow_html=True)
                
                for index, row in records.head(20).iterrows():
                    status_color = "#238636" if row['status'] == "On Time" else "#da3633"
                    
                    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                    with col1:
                        st.write(row['name'])
                    with col2:
                        st.write(row['student_id'])
                    with col3:
                        st.write(row['time'])
                    with col4:
                        st.markdown(f"<span style='color: {status_color}; font-weight: bold;'>{row['status']}</span>", unsafe_allow_html=True)
                    with col5:
                        if st.button("Delete", key=f"del_{row['id']}", use_container_width=True):
                            if db.delete_attendance_record(row['id']):
                                st.success("Record deleted")
                                st.rerun()
            else:
                st.info("No attendance records.")
        
        with tab3:
            st.markdown("### Late Attendance Warning")
            st.info("Students listed here have been late 3 or more times.")
            
            warnings = db.get_warning_list(threshold=3)
            if not warnings.empty:
                st.dataframe(warnings, use_container_width=True)
            else:
                st.success("Great! No students are currently on the warning list.")
