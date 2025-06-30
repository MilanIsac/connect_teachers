from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
import MySQLdb
import cloudinary.uploader
from app import mysql

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/create_profile', methods=['GET', 'POST'])
def create_profile():
    if 'username' not in session:
        return redirect(url_for('auth.login'))

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
                return redirect(url_for('profile.show_profile'))

            cursor.execute("""
                INSERT INTO profiles (user_id, phone, image, description)
                VALUES (%s, %s, %s, %s)
            """, (user_id, phone, image_url, description))
            mysql.connection.commit()

            session['has_profile'] = True
            flash('Profile created successfully!', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            flash("Error creating profile: " + str(e), "danger")
    return render_template('create_profile.html')


@profile_bp.route('/show_profile')
def show_profile():
    if 'username' not in session:
        return redirect(url_for('auth.login'))

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
            return redirect(url_for('main.index'))
        return render_template('show_profile.html', user=user)
    except Exception as e:
        flash("Error fetching profile: " + str(e), "warning")
        return redirect(url_for('main.index'))


@profile_bp.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'username' not in session:
        return redirect(url_for('auth.login'))

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        user_id = session['user_id']

        cursor.execute("SELECT user_id FROM profiles WHERE user_id = %s", (user_id,))
        profile_owner = cursor.fetchone()

        if not profile_owner:
            flash("You are not authorized to edit this profile.", "danger")
            return redirect(url_for('main.index'))

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
            return redirect(url_for('main.index'))

        cursor.execute("""
            SELECT phone, description, image 
            FROM profiles 
            WHERE user_id = %s
        """, (user_id,))
        profile = cursor.fetchone()

        return render_template('edit_profile.html', profile=profile)
    except Exception as e:
        flash("Error editing profile: " + str(e), "danger")
        return redirect(url_for('main.index'))


@profile_bp.route('/profile/<username>')
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
            return redirect(url_for('main.index'))

        return render_template('show_profile.html', user=user)
    except Exception as e:
        flash("Error fetching profile: " + str(e), "danger")
        return redirect(url_for('main.index'))


@profile_bp.route('/search_teachers')
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
        return jsonify({'error': 'Search failed', 'details': str(e)}), 500
