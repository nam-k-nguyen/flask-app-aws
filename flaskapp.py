import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)

# — Configuration —
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER  = os.path.join(BASE_DIR, 'uploads')
DATABASE       = os.path.join(BASE_DIR, 'users.db')
ALLOWED_EXTS   = {'txt'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTS

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# — Initialize database —
db = get_db()
db.execute('''CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT UNIQUE NOT NULL,
    password    TEXT NOT NULL,
    firstname   TEXT,
    lastname    TEXT,
    email       TEXT,
    address     TEXT,
    filename    TEXT,
    word_count  INTEGER
)''')
db.commit()
db.close()

# — Routes —

# 4a. Registration page (GET) & form submission (POST)
@app.route('/', methods=['GET'])
def register_form():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    username  = request.form['username']
    password  = request.form['password']
    firstname = request.form['firstname']
    lastname  = request.form['lastname']
    email     = request.form['email']
    address   = request.form['address']

    filename = None
    word_count = None
    upload = request.files.get('file')
    if upload and allowed_file(upload.filename):
        filename = secure_filename(upload.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        upload.save(path)
        # count words in the uploaded .txt
        with open(path, 'r') as f:
            word_count = len(f.read().split())

    conn = get_db()
    conn.execute(
        '''INSERT INTO users
           (username,password,firstname,lastname,email,address,filename,word_count)
         VALUES (?,?,?,?,?,?,?,?)''',
        (username, password, firstname, lastname, email, address, filename, word_count)
    )
    conn.commit()
    conn.close()

    return redirect(url_for('profile', username=username))

# 4c. Display user details
@app.route('/profile/<username>', methods=['GET','POST'])
def profile(username):
    conn = get_db()

    # if a file was POSTed, save it and update word_count
    if request.method == 'POST':
        upload = request.files.get('file')
        if upload and allowed_file(upload.filename):
            filename = secure_filename(upload.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            upload.save(path)
            wc = len(open(path).read().split())
            conn.execute(
                "UPDATE users SET filename=?, word_count=? WHERE username=?",
                (filename, wc, username)
            )
            conn.commit()

    user = conn.execute(
        "SELECT * FROM users WHERE username=?", (username,)
    ).fetchone()
    conn.close()
    return render_template('profile.html', user=user)


# 4d. Re-login page
@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()
        if user:
            return redirect(url_for('profile', username=username))
        error = "Invalid credentials"
    return render_template('login.html', error=error)

# serve uploaded files for download
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
