from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import MySQLdb
import re, hashlib
from app import mysql

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
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
                return redirect(url_for('main.index'))
            else:
                flash('Incorrect username or password!', 'danger')
        except Exception as e:
            flash("Login failed : " + str(e), "danger")
    return render_template('login.html')


@auth_bp.route('/signup', methods=['GET', 'POST'])
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
            session['has_profile'] = False

            flash('Account created successfully!', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            flash("Signup failed: " + str(e), "danger")
    return render_template('signup.html', msg=msg)


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))