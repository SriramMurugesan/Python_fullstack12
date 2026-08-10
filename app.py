# pyrefly: ignore [missing-import]
import sqlite3
# pyrefly: ignore [missing-import]
from flask import Flask, render_template, jsonify, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "super_secret_key"  # Needed for session management

# --- Database Setup (SQLite) ---
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # Returns rows as dictionaries
    return conn

def init_db():
    conn = get_db_connection()
    # Create users table if it doesn't exist
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            dob TEXT,
            gender TEXT,
            course TEXT
        )
    ''')
    
    # Create tasks table for the new CRUD operations
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            task_name TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Initialize DB when the app starts
init_db()


@app.route('/')
def home():
    return render_template("index.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/courses')
def courses():
    return render_template("courses.html")

@app.route('/trainers')
def trainers():
    return render_template("trainers.html")

@app.route('/register', methods=["POST", "GET"])
def register():
    return render_template("register.html")

@app.route('/login', methods=["POST", "GET"])
def login():
    return render_template("login.html")


# --- Authentication & Session Management (CREATE & READ) ---

@app.route('/api/register', methods=["POST"])
def api_register():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    dob = data.get("dob")
    gender = data.get("gender")
    course = data.get("course")
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    
    if user:
        conn.close()
        return jsonify({"status": "error", "message": "User already exists with this email!"}), 400
        
    # CREATE: Insert new user into database
    conn.execute('INSERT INTO users (name, email, password, dob, gender, course) VALUES (?, ?, ?, ?, ?, ?)',
                 (name, email, password, dob, gender, course))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "message": "Registration successful!"})

@app.route('/api/login', methods=["POST"])
def api_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    
    conn = get_db_connection()
    # READ: Fetch user from database
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    
    if user and user["password"] == password:
        # Session Management: Store user email in session
        session['user_email'] = user["email"]
        session['user_name'] = user["name"]
        return jsonify({"status": "success", "message": "Login successful! Welcome back."})
    else:
        return jsonify({"status": "error", "message": "Invalid email or password!"}), 401


# --- CRUD Operations (READ, UPDATE, DELETE) ---

@app.route('/profile')
def profile():
    if 'user_email' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    # READ: Get current user details
    user = conn.execute('SELECT * FROM users WHERE email = ?', (session['user_email'],)).fetchone()
    
    # READ: Get tasks for the current user
    tasks = conn.execute('SELECT * FROM tasks WHERE user_email = ?', (session['user_email'],)).fetchall()
    
    conn.close()
    
    return render_template('profile.html', user=user, tasks=tasks)

@app.route('/profile/update', methods=['POST'])
def update_profile():
    if 'user_email' not in session:
        return redirect(url_for('login'))
        
    new_name = request.form['name']
    new_course = request.form['course']
    
    conn = get_db_connection()
    # UPDATE: Change user details
    conn.execute('UPDATE users SET name = ?, course = ? WHERE email = ?', 
                 (new_name, new_course, session['user_email']))
    conn.commit()
    conn.close()
    
    # Update session name
    session['user_name'] = new_name
    return redirect(url_for('profile'))

@app.route('/task/add', methods=['POST'])
def add_task():
    if 'user_email' not in session:
        return redirect(url_for('login'))
        
    task_name = request.form['task_name']
    
    conn = get_db_connection()
    # CREATE: Add a new task for the current user
    conn.execute('INSERT INTO tasks (user_email, task_name) VALUES (?, ?)', 
                 (session['user_email'], task_name))
    conn.commit()
    conn.close()
    
    return redirect(url_for('profile'))

@app.route('/task/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    if 'user_email' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    # DELETE: Remove a task (only if it belongs to the current user)
    conn.execute('DELETE FROM tasks WHERE id = ? AND user_email = ?', 
                 (task_id, session['user_email']))
    conn.commit()
    conn.close()
    
    return redirect(url_for('profile'))

@app.route('/logout')
def logout():
    # Clear session
    session.pop('user_email', None)
    session.pop('user_name', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)