import sqlite3


# 1. Connect to the database file (It will be created if it doesn't exist yet)
connection = sqlite3.connect('edumax.db')

# 2. Create a cursor object (This is what actually executes SQL commands)
cursor = connection.cursor()

# 3. Drop the table if it already exists (Great for resetting during testing)
cursor.execute("DROP TABLE IF EXISTS users")

# 4. Create your exact table layout using SQL syntax
cursor.execute("""
     CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0
    )
""")

# 2. SEED DATA: Insert our initial test accounts using SQL
# The order matches our columns: username, password, is_admin
# Admin Account (is_admin = 1)
cursor.execute("INSERT OR IGNORE INTO users (username, password, is_admin) VALUES (?, ?, ?)", 
               ('admin@edumax.ac.uk', 'admin123', 1))

# Student Account (is_admin = 0)
cursor.execute("INSERT OR IGNORE INTO users (username, password, is_admin) VALUES (?, ?, ?)", 
               ('student@edumax.ac.uk', 'student123', 0))



#drop table announcements if it exists
cursor.execute("DROP TABLE IF EXISTS announcements")

# 4. Create your exact table layout using SQL syntax
cursor.execute("""
     CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_ID TEXT,
        title TEXT NOT NULL,
        publish_date TEXT NOT NULL,
        priority TEXT NOT NULL,
        body TEXT NOT NULL
    )
""")

print("Database initialized! Added 'users' and 'announcements' tables cleanly.")


# 5. Save (commit) the changes and close the connection safely
connection.commit()
connection.close()