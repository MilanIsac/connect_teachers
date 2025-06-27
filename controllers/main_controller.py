from flask import Blueprint, render_template, flash
import MySQLdb
from app import mysql

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
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