import streamlit as st
import smtplib
import hashlib
import random
import os
import webbrowser
from pymongo import MongoClient
from bson.objectid import ObjectId
import streamlit.components.v1 as components

# Email Configuration
EMAIL_ADDRESS = "noteworthynotes24@gmail.com"
EMAIL_PASSWORD = "bnkm atmy ooup dmke"


# MongoDB Setup

CONNECTION_STRING = "mongodb+srv://NOTEWORTHY:Tilak$2004@noteworthy.fmh8b.mongodb.net/?retryWrites=true&w=majority&appName=NOTEWORTHY"

# Connect to MongoDB Atlas
client = MongoClient(CONNECTION_STRING)

db = client["record_writing_app"]
users_collection = db["users"]
records_collection = db["records"]
messages_collection = db["messages"]  # New collection for messagesessages



# Helper Functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def send_email(recipient, subject, message):
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        email_message = f"Subject: {subject}\n\n{message}"
        server.sendmail(EMAIL_ADDRESS, recipient, email_message)

def send_otp(email):
    otp = random.randint(100000, 999999)
    send_email(email, "Your OTP Code", f"Your OTP code is: {otp}")
    return otp

def login(username, password):
    hashed_pw = hash_password(password)
    return users_collection.find_one({"username": username, "password": hashed_pw})

def register_user(username, password, email):
    hashed_pw = hash_password(password)
    users_collection.insert_one({"username": username, "password": hashed_pw, "email": email})

def get_tasks():
    return list(records_collection.find().sort("priority", 1))

def update_task_status(task_id, status, username):
    task = records_collection.find_one({"_id": ObjectId(task_id)})
    if task:
        records_collection.update_one({"_id": ObjectId(task_id)}, {"$set": {"status": status}})
        user = users_collection.find_one({"username": username})
        if user:
            email = user.get("email")
            if email:
                send_email(
                    email,
                    "Task Status Update",
                    f"The status of Task ID {task_id} has been updated to '{status}'."
                )

def delete_task(task_id):
    records_collection.delete_one({"_id": ObjectId(task_id)})

def open_pdf(pdf_path):
    if os.path.isfile(pdf_path):
        webbrowser.open(f"file:///{pdf_path}")
        return True
    return False

def send_message(task_id, sender, message):
    messages_collection.insert_one({"task_id": ObjectId(task_id), "sender": sender, "message": message})

def get_messages(task_id):
    return list(messages_collection.find({"task_id": ObjectId(task_id)}).sort("timestamp", 1))

# Streamlit App Configuration
st.set_page_config(page_title="Record Writing App", layout="wide")

# Navigation Sidebar
def sidebar_navigation():
    return st.sidebar.radio(
        "Navigation",
        ["Login", "Register", "Dashboard", "Task Management"]
    )


# Login Page
def login_page():
    st.title("🔑 Login")
    username = st.text_input("👤 Username")
    password = st.text_input("🔒 Password", type="password")

    if st.button("🔓 Login"):
        user = login(username, password)
        if user:
            otp = send_otp(user["email"])
            entered_otp = st.text_input("🔢 Enter OTP sent to your email:")
            if st.button("✔️ Verify OTP"):
                if entered_otp == str(otp):
                    st.success("✅ Login successful!")
                    st.session_state["username"] = username
                    st.session_state["logged_in"] = True
                else:
                    st.error("❌ Invalid OTP.")
        else:
            st.error("❌ Invalid username or password.")

# Register Page
def register_page():
    st.title("📝 Register")
    username = st.text_input("👤 Choose a Username")
    password = st.text_input("🔒 Choose a Password", type="password")
    email = st.text_input("📧 Enter Your Email")

    if st.button("📝 Register"):
        if users_collection.find_one({"username": username}):
            st.error("❌ Username already exists.")
        else:
            otp = send_otp(email)
            entered_otp = st.text_input("🔢 Enter OTP sent to your email:")
            if st.button("✔️ Verify OTP"):
                if entered_otp == str(otp):
                    register_user(username, password, email)
                    st.success("✅ Registration successful!")
                else:
                    st.error("❌ Invalid OTP.") 
# Writer Dashboard
def writer_dashboard():
    st.title("🖋️ Writer Dashboard - Task Queue Management")

    # Fetch tasks and categorize them
    tasks = get_tasks()
    pending_tasks = [task for task in tasks if task.get("status") == "Pending"]
    in_progress_tasks = [task for task in tasks if task.get("status") == "In Progress"]
    completed_tasks = [task for task in tasks if task.get("status") == "Completed"]

    # Display Pending Tasks
    st.subheader("⏳ Pending Tasks")
    if not pending_tasks:
        st.info("No pending tasks.")
    for task in pending_tasks:
        st.markdown(f"**📌 Task ID:** {task['_id']}")
        st.text(f"👤 User: {task.get('username', 'N/A')}")
        st.text(f"🔤 Font: {task.get('font', 'N/A')}")
        st.text(f"⚡ Priority: {task.get('priority', 'N/A')}")
        st.text(f"📍Pickup Location: {task.get('pickup_location', 'N/A')}")
        st.text(f"📍Drop Location: {task.get('drop_location', 'N/A')}")

        if st.button(f"✅ Accept Task {task['_id']}", key=f"accept_{task['_id']}"):
            update_task_status(task["_id"], "In Progress", task.get("username"))
            st.success(f"Task {task['_id']} accepted and moved to 'In Progress'.")

        if st.button(f"❌ Reject Task {task['_id']}", key=f"reject_{task['_id']}"):
            delete_task(task["_id"])
            st.warning(f"Task {task['_id']} rejected and deleted.")

    # Display In-Progress Tasks
    st.subheader("🚧 In-Progress Tasks")
    if not in_progress_tasks:
        st.info("No in-progress tasks.")
    for task in in_progress_tasks:
        st.markdown(f"**📌 Task ID:** {task['_id']}")
        st.text(f"👤 User: {task.get('username', 'N/A')}")
        st.text(f"🔤 Font: {task.get('font', 'N/A')}")
        st.text(f"⚡ Priority: {task.get('priority', 'N/A')}")
        st.text(f"📅 Deadline: {task.get('deadline', 'N/A')}")
        st.text(f"📍Pickup Location: {task.get('pickup_location', 'N/A')}")
        st.text(f"📍Drop Location: {task.get('drop_location', 'N/A')}")

        # Status update options
        status = st.selectbox(
            f"🔄 Update Status for Task {task['_id']}",
            ["In Progress", "Completed"],
            key=f"status_{task['_id']}"
        )
        if st.button(f"Update Task {task['_id']}", key=f"update_{task['_id']}"):
            update_task_status(task["_id"], status, task.get("username"))
            st.success(f"Task {task['_id']} status updated to '{status}'.")

        pdf_path = task.get("pdf_path", "")
        if pdf_path and st.button(f"📂 Open PDF for Task {task['_id']}", key=f"open_pdf_{task['_id']}"):
            if open_pdf(pdf_path):
                st.success(f"PDF for Task {task['_id']} opened.")
            else:
                st.error(f"PDF for Task {task['_id']} not found.")

    # Display Completed Tasks
    st.subheader("✅ Completed Tasks")
    if not completed_tasks:
        st.info("No completed tasks.")
    for task in completed_tasks:
        st.markdown(f"**📌 Task ID:** {task['_id']}")
        st.text(f"👤 User: {task.get('username', 'N/A')}")
        st.text(f"🔤 Font: {task.get('font', 'N/A')}")
        st.text(f"⚡ Priority: {task.get('priority', 'N/A')}")
        st.text(f"📅 Deadline: {task.get('deadline', 'N/A')}")
        st.text(f"📍Pickup Location: {task.get('pickup_location', 'N/A')}")
        st.text(f"📍Drop Location: {task.get('drop_location', 'N/A')}")
        st.success("This task is marked as completed.")

        # Display Reviews
        reviews = task.get("reviews")
        if reviews:
            st.markdown("### ⭐ Review Details")
            st.write(f"- **Rating**: {reviews.get('rating', 'N/A')}")
            st.write(f"- **Review**: {reviews.get('review_text', 'N/A')}")
        else:
            st.write("No reviews available for this task.")

        pdf_path = task.get("pdf_path", "")
        if pdf_path and st.button(f"📂 Open PDF for Task {task['_id']}"):
            if open_pdf(pdf_path):
                st.success(f"PDF for Task {task['_id']} opened.")
            else:
                st.error(f"PDF for Task {task['_id']} not found.")

# Task Management And History Page
def get_tasks_by_font(font):
    return list(records_collection.find({"font": font}))

def task_management():
    st.title("📋 Task Management")
    
    # Fetch distinct fonts from the records
    fonts = records_collection.distinct("font")
    selected_font = st.selectbox("Select Font", [""] + fonts, key="task_font")

    if not selected_font:
        st.info("Please select a font to view tasks")
        return

    tasks = get_tasks_by_font(selected_font)
    
    if not tasks:
        st.warning("No tasks available for selected font")
        return

    for task in tasks:
        with st.container():
            st.markdown(f'<div class="task-card">', unsafe_allow_html=True)
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"📌 Task ID: {task['_id']}")
                st.markdown(f"""
                - 👤 **User**: {task.get('username', 'N/A')}
                - 🔤 **Font**: {task.get('font', 'N/A')}
                - 🚩 **Status**: {task.get('status', 'N/A')}
                - ⚡ **Priority**: {task.get('priority', 'N/A')}
                - 📅 **Deadline**: {task.get('deadline', 'N/A')}
                """)
   

    for task in tasks:
        st.subheader(f"📝 Task ID: {task['_id']}")
        st.text(f"👤 User: {task.get('username', 'N/A')}")
        st.text(f"🔤 Font: {task.get('font', 'N/A')}")
        st.text(f"📊 Priority: {task.get('priority', 'N/A')}")
        st.text(f"📅 Deadline: {task.get('deadline', 'N/A')}")
        st.text(f"📈 Status: {task.get('status', 'N/A')}")
        st.text(f"📍Pickup Location: {task.get('pickup_location', 'N/A')}")
        st.text(f"📍Drop Location: {task.get('drop_location', 'N/A')}")

        # Display Reviews
        reviews = task.get('reviews')
        if reviews:
            st.markdown("### ⭐ Review Details")
            st.write(f"- **Rating**: {reviews.get('rating', 'N/A')}")
            st.write(f"- **Review**: {reviews.get('review_text', 'N/A')}")
        else:
            st.write("No reviews available for this task.")

        # Messaging Section
        st.markdown("### 💬 Messaging")
        st.write("Under Development")

        # Task Actions
        if st.button(f"✅ Accept Task {task['_id']}"):
            update_task_status(task['_id'], "In Progress", task.get("username"))
            st.success(f"Task {task['_id']} status updated to 'In Progress'.")

        status = st.selectbox(
            f"🔄 Update Status for Task {task['_id']}",
            ["Pending", "In Progress", "Completed"],
            key=f"status_{task['_id']}"
        )
        if st.button(f"Update Task {task['_id']}"):
            update_task_status(task["_id"], status, task.get("username"))
            st.success(f"Task {task['_id']} status updated to '{status}'.")

        if st.button(f"🗑️ Delete Task {task['_id']}"):
            delete_task(task["_id"])
            st.success(f"Task {task['_id']} deleted.")

        pdf_path = task.get("pdf_path", "")
        if pdf_path and st.button(f"📂 Open PDF for Task {task['_id']}"):
            if open_pdf(pdf_path):
                st.success(f"PDF for Task {task['_id']} opened.")
            else:
                st.error(f"PDF for Task {task['_id']} not found.")

        # Add a horizontal line for separation
        st.markdown("---")

    # Add some custom CSS for animations
    components.html("""
    <style>
    .stButton button {
        transition: transform 0.2s;
    }
    .stButton button:hover {
        transform: scale(1.1);
    }
    </style>
    """, height=0)

# Main Function
def main():
    # Sidebar for navigation
    page = st.radio(
        "Navigation",
        ["Login", "Register", "Dashboard", "Task Management"],
        horizontal=True,
        label_visibility="hidden"
    )

    if page == "Login":
        login_page()
    elif page == "Register":
        register_page()
    elif page == "Dashboard":
        writer_dashboard()
    elif page == "Task Management":
        task_management()
    
if __name__ == "__main__":
    main()
