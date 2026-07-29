from flask import Flask, render_template, request, redirect, session, url_for, flash, Response, jsonify
import sqlite3
import requests
import json
import csv
import io
import os 
from openai import OpenAI
from dotenv import load_dotenv

app = Flask(__name__)

# Crucial: Flask requires a secret key to securely sign the browser session cookies
app.secret_key = 'edumax_super_secret_system_token_key'


# --- Locate this block near the top area of your app.py file ---
load_dotenv()

# Fallback explicit variable definitions 
GROQ_SECRET = os.environ.get("GROQ_API_KEY") 

free_ai_client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_SECRET  # Securely maps your active validated key directly
)


def google_search_tutor(query_text):
    """Fetches real-time search context string blocks from Google via Serper."""
    url = "https://serper.dev"  # <-- Update this specific URL path string!
    payload = json.dumps({"q": query_text, "num": 3})
    # ... rest of your search code remains identical ...
    headers = {
        'X-API-KEY': os.environ.get("SERPER_API_KEY"),
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=5)
        search_results = response.json()
        
        context_string = ""
        for result in search_results.get('organic', []):
            context_string += f"- {result.get('snippet')}\n"
        return context_string
    except Exception:
        return "No real-time search engine context available."

# 3. Add the route to render the Student Chat Interface page layout
@app.route('/assistant')
def assistant_page():
    if not session.get('logged_in'):
        return render_template('login.html', error="Please log in first.")
    return render_template('assistant.html')

# 4. Add the backend AJAX API processing engine route
# 4. Add the backend AJAX API processing engine route
@app.route('/api/ai/ask', methods=['POST'])
def ask_ai_assistant():
    if not session.get('logged_in'):
        return jsonify({"answer": "Authentication required."}), 401
        
    data = request.get_json() or {}
    student_question = data.get('question', '').strip()

    if not student_question:
        return jsonify({"answer": "Please type a valid question."}), 400

    # 1. Isolate the search function in its own safe check block
    live_web_facts = ""
    try:
        if os.environ.get("SERPER_API_KEY"):
            live_web_facts = google_search_tutor(student_question)
    except Exception as search_error:
        print("GOOGLE SEARCH ERROR (Skipping):", str(search_error))

    # 2. Structure your system prompt instructions
    socratic_system_prompt = (
        "You are the EduMax Socratic Academic Coach. Help the student learn by analyzing concepts, "
        "NOT by doing their work. Follow these rules strictly:\n"
        "1. NEVER output entire completed code blocks, full math solutions, or complete essays.\n"
        "2. Provide structural templates or conceptual roadmaps with blanks (e.g., Use '[your variable]').\n"
        "3. End with one direct follow-up question prompting the student's next logical step.\n"
    )
    
    if live_web_facts:
        socratic_system_prompt += f"\nUse this real-time context if relevant:\n{live_web_facts}"

    # 3. Request completion from Groq API engine matrix
      # 3. Request completion from Groq API engine matrix
        # 3. Request completion from Groq API engine matrix
    try:
        response = free_ai_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": socratic_system_prompt},
                {"role": "user", "content": student_question}
            ],
            max_tokens=300
        )
        
        # --- FIX THIS SPECIFIC LINE REGION BELOW ---
        if hasattr(response, 'choices') and isinstance(response.choices, list):
            # Access the first choice out of the array index directly
            ai_reply = response.choices[0].message.content
        else:
            # Fallback to standard OpenAI formatting layout
            ai_reply = response.choices.message.content
            
    except Exception as ai_error:
        print("GROQ API ENCOUNTERED ERROR:", str(ai_error))
        ai_reply = "The study coach framework is currently updating. Please try again shortly."


    # This line now sits cleanly outside the try/except block closures
    return jsonify({"answer": ai_reply})



# --- 1. PUBLIC ROUTE: HOME PAGE ---
@app.route('/')
def home_page():
    return render_template('index.html')

# ---  PUBLIC ROUTE: News PAGE ---

@app.route('/news')
def news_page():
    # 1. Connect to your database
    connection = sqlite3.connect('edumax.db')
    cursor = connection.cursor()
    
    # 2. Grab all saved entries from the announcements table
    # ORDER BY id DESC makes the newest announcements show up at the very top of the feed
    cursor.execute("SELECT title, publish_date, priority, body FROM announcements ORDER BY id DESC")
    announcements_list = cursor.fetchall()
    
    connection.close()
    
    # 3. Pass that data array into your HTML template using a variable named 'posts'
    return render_template('news.html', posts=announcements_list)


# ---  PUBLIC ROUTE: Modules PAGE ---
@app.route('/modules')
def modules_page():  # <--- This is what url_for checks
    return render_template('modules.html')

# ---  PUBLIC ROUTE: Membership PAGE ---
@app.route('/membership')
def membership_page():  # <--- This is what url_for checks
    return render_template('membership.html')


# --- 2. PUBLIC ROUTE: DISPLAY LOGIN FORM ---
@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

    # --- ADMIN ONLY ROUTE: DISPLAY EDIT FORM ---

# --- 1. ADMIN HUB: VIEW CONTROL DASHBOARD TABLE ---
@app.route('/form', methods=['GET'])
def edit_announcement_page():
    # Security Guard Protection Link Check
    if not session.get('logged_in') or not session.get('is_admin'):
        return render_template('login.html', error="Administrative clearance required to access this portal.")
    
    # Connect and pull ALL entries so we can draw our dashboard spreadsheet
    connection = sqlite3.connect('edumax.db')
    cursor = connection.cursor()
    cursor.execute("SELECT id, title, publish_date, priority FROM announcements ORDER BY id DESC")
    all_rows = cursor.fetchall()
    connection.close()
    
    # We load a clean layout file and pass our data rows package under the nickname 'announcements'
    return render_template('manager.html', announcements=all_rows)

# --- 2. ADMIN ACTIONS: CREATE BLANK FORM LINK ---
@app.route('/form/new', methods=['GET'])
def new_announcement_form():
    if not session.get('logged_in') or not session.get('is_admin'):
        return render_template('login.html', error="Administrative clearance required.")
    
    # Renders the input template file in "Create Mode"
    return render_template('form.html', mode="create")

@app.route('/form/delete/<int:announcement_id>')
def delete_announcement_route(announcement_id):
    # Security guard line
    if not session.get('logged_in') or not session.get('is_admin'):
        return render_template('login.html', error="Admin access required.")
    
    connection = sqlite3.connect('edumax.db')
    cursor = connection.cursor()

    cursor.execute('DELETE FROM announcements WHERE id = ?', (announcement_id,))

    connection.commit()
    connection.close()

    print(f"Purged record item matching ID: {announcement_id}")

     # Pack a temporary text warning notification box message
    flash('Announcement row was permanently deleted from the database.', 'danger')

    return redirect(url_for('edit_announcement_page'))

@app.route('/form/edit/<int:announcement_id>')
def edit_announcement_route(announcement_id):
    # Security guard line
    if not session.get('logged_in') or not session.get('is_admin'):
        return render_template('login.html', error="Admin access required.")
    
    connection = sqlite3.connect('edumax.db')
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM announcements WHERE id = ?', (announcement_id,))
    announcement = cursor.fetchone()
    return render_template('form.html', post=announcement)

@app.route('/admin/users')
@app.route('/admin/users')
def edit_users():
    if not session.get('logged_in') or not session.get('is_admin'):
        return render_template('login.html', error="Admin access required.")
    
    # Defaults to an empty string if no search parameter exists in the URL
    search_query = request.args.get('search', '').strip()
    
    connection = sqlite3.connect('edumax.db')
    cursor = connection.cursor()
    
    if search_query:
        # Runs ONLY when an admin types a query and hits 'Search'
        cursor.execute('SELECT * FROM users WHERE username LIKE ?', (f'%{search_query}%',))
    else:
        # Runs automatically on first load, populating the page with ALL users
        cursor.execute('SELECT * FROM users')
        
    user_list = cursor.fetchall()
    connection.close()
    
    return render_template('users_manager.html', accounts=user_list, search_query=search_query)


@app.route('/admin/delete/<int:user_id>')
def delete_user_route(user_id):
    # Security guard line
    if not session.get('logged_in') or not session.get('is_admin'):
        return render_template('login.html', error="Admin access required.")
    
    connection = sqlite3.connect('edumax.db')
    cursor = connection.cursor()

    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))

    connection.commit()
    connection.close()

    print(f"Purged record item matching ID: {user_id}")

     # Pack a temporary text warning notification box message
   
    record_activity(f"Permanently deleted User Account ID #{user_id}")

    return redirect(url_for('edit_users'))

@app.route('/form/edit/<int:user_id>')
def edit_user_route(user_id):
    # Security guard line
    if not session.get('logged_in') or not session.get('is_admin'):
        return render_template('login.html', error="Admin access required.")
    
    connection = sqlite3.connect('edumax.db')
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    return render_template('user_form.html', post=user)

# --- 1. ADMIN ACTION: RENDER BLANK USER ACC CREATION FORM ---
@app.route('/admin/users/new', methods=['GET'])
def new_user_form():
    if not session.get('logged_in') or not session.get('is_admin'):
        return render_template('login.html', error="Admin access required.")
    
    # Loads a clean user data entry template form canvas
    return render_template('user_form.html')


# --- 2. ADMIN ACTION: PROCESS USER ACCOUNT REGISTRATION ---
# --- ADMIN ONLY: FETCH USER DATA AND LOAD USER FORM IN EDIT MODE ---
@app.route('/admin/edit/<int:user_id>', methods=['GET'])
def edit_user_load_page(user_id):
    if not session.get('logged_in') or not session.get('is_admin'):
        return render_template('login.html', error="Admin access required.")
    
    connection = sqlite3.connect('edumax.db')
    cursor = connection.cursor()
    
    # Securely retrieve the exact user profile tuple row by its unique ID
    cursor.execute('SELECT id, username, password, is_admin FROM users WHERE id = ?', (user_id,))
    user_account = cursor.fetchone()
    connection.close()
    
    # If the user doesn't exist in the database, protect the app from crashing
    if not user_account:
        flash("System Error: Account profile not found.", "danger")
        return redirect(url_for('edit_users'))
        
    # Open your user form canvas, passing the account rows under the nickname 'account'
    return render_template('user_form.html', account=user_account)

# --- THE BACKEND USER PROCESSOR (HANDLES BOTH ADD & EDIT ACCOUNTS) ---
@app.route('/admin/users/add', methods=['POST'])
def submit_new_user():
    if not session.get('logged_in') or not session.get('is_admin'):
        return render_template('login.html', error="Admin access required.")
    
    # Pull parameters from the HTML form fields
    form_user_id = request.form.get('user_id')
    new_username = request.form.get('username')
    new_password = request.form.get('password')
    new_role = request.form.get('is_admin')
    
    connection = sqlite3.connect('edumax.db')
    cursor = connection.cursor()
    
    # If form_user_id exists, we run an UPDATE to overwrite old data
    if form_user_id:
        cursor.execute("""
            UPDATE users 
            SET username = ?, password = ?, is_admin = ?
            WHERE id = ?
        """, (new_username, new_password, int(new_role), form_user_id))
        connection.commit()
        connection.close()
        # Log the UPDATE using the existing form_user_id
        record_activity(f"Updated user account ID #{form_user_id} ({new_username})")
        flash('User account details updated successfully!', 'success')
        
    else:
        # If form_user_id is missing, it is a brand new account, run an INSERT
        cursor.execute("""
            INSERT INTO users (username, password, is_admin) 
            VALUES (?, ?, ?)
        """, (new_username, new_password, int(new_role)))

        # Grab the newly generated ID from SQLite right after inserting
        new_id = cursor.lastrowid
        
        connection.commit()
        connection.close()
        record_activity(f"Added new user ID #{new_id} ({new_username})")
        flash('New user account added successfully!', 'success')
        
    
    # Route the administrator right back onto the user spreadsheet dashboard grid!
    return redirect(url_for('edit_users'))



# --- THE BACKEND SUBMISSION PROCESSOR (HANDLES BOTH ADD & EDIT) ---
@app.route('/add_announcement', methods=['POST'])
def submit_announcement():
    # 1. Grab all text values from your form fields
    form_id = request.form.get('announcement_id') # Pulls the hidden ID field we added
    form_title = request.form.get('title')
    form_date = request.form.get('publish_date')
    form_priority = request.form.get('priority')
    form_body = request.form.get('body')
    
    connection = sqlite3.connect('edumax.db')
    cursor = connection.cursor()
    
    # 2. THE LOGIC BRANCH: If form_id exists, we are UPDATING an existing row!
    if form_id:
        cursor.execute("""
            UPDATE announcements 
            SET title = ?, publish_date = ?, priority = ?, body = ?
            WHERE id = ?
        """, (form_title, form_date, form_priority, form_body, form_id))

        print(f"Successfully UPDATED announcement ID #{form_id}")
        flash('Announcement parameters updated successfully!', 'success')
        
    else:
        # If form_id is missing/empty, the admin clicked "Add New", so we INSERT fresh
        cursor.execute("""
            INSERT INTO announcements (title, publish_date, priority, body) 
            VALUES (?, ?, ?, ?)
        """, (form_title, form_date, form_priority, form_body))

        print(f"Successfully CREATED a brand new announcement: {form_title}")
        flash('Brand new announcement published to live feeds!', 'success')
       
        
    connection.commit()
    connection.close()
    record_activity(f"Added new announcement #{form_title}")
    # 3. Dynamic loop-back straight to your master control spreadsheet
    return redirect(url_for('edit_announcement_page'))



# --- 3. THE BACKEND POST PROCESSOR: HANDLES LOGIN ---
@app.route('/login', methods=['POST'])
def login_process():
    # Grab the data typed into the form input fields
    form_username = request.form.get('username')
    form_password = request.form.get('password')

    # Connect to your local database
    connection = sqlite3.connect('edumax.db')
    cursor = connection.cursor()

    # Query the database for this specific user row
    cursor.execute("SELECT id, username, password, is_admin FROM users WHERE username = ?", (form_username,))
    user_row = cursor.fetchone()
    connection.close()

    # Check if a user row was actually found, and verify the password matches
    if user_row and user_row[2] == form_password:
        # SUCCESS! Save state inside Flask's secure session memory
        session['logged_in'] = True
        session['username'] = user_row[1]
        session['is_admin'] = (user_row[3] == 1) # Becomes True if 1, False if 0
    
        print(f"User {form_username} authenticated successfully. Admin state: {session['is_admin']}")
        record_activity(f"User successfully logged in")
        return redirect(url_for('home_page')) # Redirect safely back to the home page

    else:
        # FAILURE! Wrong username or password
        print("Authentication failed: Invalid credentials.")
        return render_template('login.html', error="Invalid username or password.")

# --- THE BACKEND LOGOUT HANDLER ---
@app.route('/logout')
def logout_process():
    if session.get('logged_in'):
        # Log the logout action while the session username still exists
        record_activity(f"User logged out safely")
    # 1. Clear out all saved session cookie keys (logged_in, username, is_admin)
    session.clear()
    
    # 2. Redirect the user back to the homepage
    print("User session cleared successfully. Redirecting home.")
    return redirect(url_for('home_page'))

def record_activity(action_description):
    """Saves administrative activities to the database log table."""
    current_user = session.get('username', 'System/Unknown')
    
    connection = sqlite3.connect('edumax.db')
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO audit_logs (username, action) VALUES (?, ?)",
        (current_user, action_description)
    )
    connection.commit()
    connection.close()

@app.route('/admin/logs')
def view_logs():
    if not session.get('logged_in') or not session.get('is_admin'):
        return render_template('login.html', error="Admin access required.")
        
    connection = sqlite3.connect('edumax.db')
    cursor = connection.cursor()
    # Pull newest actions first
    cursor.execute("SELECT username, action, timestamp FROM audit_logs ORDER BY id DESC")
    log_rows = cursor.fetchall()
    connection.close()
    
    return render_template('logs.html', logs=log_rows)

@app.route('/admin/logs/download')
def download_logs():
    # Security guard checkpoint
    if not session.get('logged_in') or not session.get('is_admin'):
        return render_template('login.html', error="Admin access required.")
        
    # 1. Fetch all audit rows from the SQLite engine
    connection = sqlite3.connect('edumax.db')
    cursor = connection.cursor()
    cursor.execute("SELECT timestamp, username, action FROM audit_logs ORDER BY id DESC")
    log_rows = cursor.fetchall()
    connection.close()
    
    # 2. Write the database results out into an in-memory CSV text stream buffer
    output_stream = io.StringIO()
    writer = csv.writer(output_stream)
    
    # Write structural headers first
    writer.writerow(['Timestamp', 'Administrator', 'Action Performed'])
    
    # Dump the fetched tracking tuple rows down into the stream block
    writer.writerows(log_rows)
    
    # Reset stream cursor pointer position back to start
    output_stream.seek(0)
    
    # 3. Stream the raw CSV output data as a direct download attachment file block
    return Response(
        output_stream.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=system_audit_logs.csv"}
    )

if __name__ == '__main__':
    app.run(debug=True)