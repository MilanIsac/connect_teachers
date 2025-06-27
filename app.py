from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import hashlib
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import os
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

db = SQLAlchemy()

app = Flask(__name__, template_folder='frontend/templates', static_folder='frontend/static')

app.secret_key = os.getenv('APP_SECRET_KEY')

USE_SQLITE = os.environ.get('USE_SQLITE', 'false').lower() == 'true'

if USE_SQLITE:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}/{os.getenv('MYSQL_DB')}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

mysql = MySQL(app)

cloudinary.config(
    cloud_name=os.getenv('CLOUD_NAME'),
    api_key=os.getenv('API_KEY'),
    api_secret=os.getenv('API_SECRET')
)

@app.route('/')
def index():
    try: 
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT u.username, p.description, p.image
            FROM users u
            JOIN profiles p ON u.id = p.user_id
        """)
        teachers = cursor.fetchall()
    except Exception as e:
        flash("Error loading Teachers : " + str(e), "danger")
        teachers = []
    return render_template('index.html', teachers=teachers)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']

            if not username or not password:
                flash('Please fill out all fields!', 'error')
                return render_template('login.html')

            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, hashed_password))
            user = cursor.fetchone()

            if user:
                session['loggedin'] = True
                session['username'] = user['username']
                session['user_id'] = user['id']

                cursor.execute("SELECT * FROM profiles WHERE user_id = %s", (user['id'],))
                session['has_profile'] = cursor.fetchone() is not None

                return redirect(url_for('index'))
            else:
                flash('Incorrect username or password!', 'danger')
        except Exception as e:
            flash("Login failed : " + str(e), "danger")
    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    msg = ''
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            email = request.form['email']

            if password != confirm_password:
                msg = 'Passwords do not match!'
                return render_template('signup.html', msg=msg)

            if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                msg = 'Invalid email address!'
                return render_template('signup.html', msg=msg)

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            account = cursor.fetchone()

            if account:
                msg = 'User already exists!'
                return render_template('signup.html', msg=msg)

            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute(
                'INSERT INTO users (username, password, email) VALUES (%s, %s, %s)',
                (username, hashed_password, email)
            )
            mysql.connection.commit()

            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            user = cursor.fetchone()
            session['loggedin'] = True
            session['username'] = user['username']
            session['user_id'] = user['id']
            session['has_profile'] = False  # New users don't have a profile yet

            flash('Account created successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash("Signup failed: " +str(e), "danger")
    return render_template('signup.html', msg=msg)


@app.route('/create_profile', methods=['GET', 'POST'])
def create_profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            phone = request.form.get('phone')
            description = request.form['description']
            image = request.files['image']

            image_url = None
            if image and image.filename != '':
                upload_result = cloudinary.uploader.upload(image)
                image_url = upload_result['secure_url']

            user_id = session['user_id']

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM profiles WHERE user_id = %s", (user_id,))
            profile = cursor.fetchone()

            if profile:
                flash('Profile already exists!', 'danger')
                return redirect(url_for('show_profile'))

            cursor.execute("""
                INSERT INTO profiles (user_id, phone, image, description)
                VALUES (%s, %s, %s, %s)
            """, (user_id, phone, image_url, description))
            mysql.connection.commit()

            session['has_profile'] = True
            flash('Profile created successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash("Error creating profile: " + str(e), "danger")
    return render_template('create_profile.html')


@app.route('/show_profile')
def show_profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT u.username, u.email, p.image, p.description, p.phone
            FROM users u
            LEFT JOIN profiles p ON u.id = p.user_id
            WHERE u.username = %s
        """, (session['username'],))
        user = cursor.fetchone()
        if not user:
            flash("Profile not found", "warning")
            return redirect(url_for('index'))
        return render_template('show_profile.html', user=user)
    except Exception as e:
        flash("Error fetching profile: " + str(e), "warning")
        return redirect(url_for('index'))

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        user_id = session['user_id']

        cursor.execute("SELECT user_id FROM profiles WHERE user_id = %s", (user_id,))
        profile_owner = cursor.fetchone()

        if not profile_owner:
            flash("You are not authorized to edit this profile.", "danger")
            return redirect(url_for('index'))

        if request.method == 'POST':
            phone = request.form.get('phone')
            description = request.form.get('description')
            image = request.files.get('image')

            image_url = None
            if image and image.filename != '':
                upload_result = cloudinary.uploader.upload(image)
                image_url = upload_result['secure_url']

            if image_url:
                cursor.execute("""
                    UPDATE profiles 
                    SET phone = %s, description = %s, image = %s 
                    WHERE user_id = %s
                """, (phone, description, image_url, user_id))
            else:
                cursor.execute("""
                    UPDATE profiles 
                    SET phone = %s, description = %s 
                    WHERE user_id = %s
                """, (phone, description, user_id))

            mysql.connection.commit()
            flash("Profile updated successfully", "success")
            return redirect(url_for('index'))
    except Exception as e:
        flash("Error editing profile: " + str(e), "danger")
        return redirect(url_for('index'))

    cursor.execute("""
        SELECT phone, description, image 
        FROM profiles 
        WHERE user_id = %s
    """, (user_id,))
    profile = cursor.fetchone()

    return render_template('edit_profile.html', profile=profile)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/profile/<username>')
def view_profile(username):
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT u.username, u.email, p.image, p.description, p.phone
            FROM users u
            LEFT JOIN profiles p ON u.id = p.user_id
            WHERE u.username = %s
        """, (username,))
        user = cursor.fetchone()

        if not user:
            flash("Profile not found", "danger")
            return redirect(url_for('index'))

        return render_template('show_profile.html', user=user)
    except Exception as e:
        flash("Error fetching profile: " + str(e), "danger")
        return redirect(url_for('index'))

@app.route('/search_teachers')
def search_teachers():
    try:
        query = request.args.get('query', '')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT u.username, p.description
            FROM users AS u
            JOIN profiles AS p ON u.id = p.user_id
            WHERE u.username LIKE %s
        """, ('%' + query + '%',))

        results = cursor.fetchall()
        return jsonify(results)
    except Exception as e:
        return jsonify({'error' : 'Search failed', 'details': str(e)}), 500

# @app.route('/your_profile')
# def your_profile():
#     if 'username' not in session:
#         return redirect(url_for('login'))

#     cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
#     cursor.execute("""
#         SELECT u.username, u.email, p.image, p.description, p.phone
#         FROM users u
#         LEFT JOIN profiles p ON u.id = p.user_id
#         WHERE u.username = %s
#     """, (session['username'],))
#     user = cursor.fetchone()

#     return render_template('show_profile.html', user=user)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
