from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3

app = Flask(__name__)

# Crucial: Flask requires a secret key to securely sign the browser session cookies
app.secret_key = 'edumax_super_secret_system_token_key'

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
        return redirect(url_for('home_page')) # Redirect safely back to the home page

    else:
        # FAILURE! Wrong username or password
        print("Authentication failed: Invalid credentials.")
        return render_template('login.html', error="Invalid username or password.")

# --- THE BACKEND LOGOUT HANDLER ---
@app.route('/logout')
def logout_process():
    # 1. Clear out all saved session cookie keys (logged_in, username, is_admin)
    session.clear()
    
    # 2. Redirect the user back to the homepage
    print("User session cleared successfully. Redirecting home.")
    return redirect(url_for('home_page'))



if __name__ == '__main__':
    app.run(debug=True)