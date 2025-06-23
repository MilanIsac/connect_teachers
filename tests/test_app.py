import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import app as flask_app
import io
import cloudinary.uploader


USE_SQLITE = os.getenv('USE_SQLITE', 'false').lower() == 'true'

if USE_SQLITE:
    import sqlite3
    # You can add SQLite test config here if needed
else:
    from flask_mysqldb import MySQL
    flask_app.config['MYSQL_HOST'] = '127.0.0.1'
    flask_app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
    flask_app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
    flask_app.config['MYSQL_DB'] = 'teachers_connect'
    mysql = MySQL(flask_app)



# Mock Cloudinary upload during tests
def dummy_upload(file):
    return {'secure_url': 'http://dummy.url/test.jpg'}

cloudinary.uploader.upload = dummy_upload

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    with flask_app.test_client() as client:
        with flask_app.app_context():
            yield client

def test_signup_and_login(client):
    username = 'testuser1'
    password = 'testpass'

    # Signup
    client.post('/signup', data={
        'username': username,
        'email': 'test1@example.com',
        'password': password,
        'confirm_password': password
    }, follow_redirects=True)

    # Login
    response = client.post('/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)
    assert b'Logout' in response.data

def test_profile_creation(client):
    # Login
    client.post('/login', data={
        'username': 'testuser1',
        'password': 'testpass'
    }, follow_redirects=True)

    dummy_image = (io.BytesIO(b'my file contents'), 'dummy.jpg')

    # Create Profile
    response = client.post('/create_profile', data={
        'phone': '9876543210',
        'description': 'Test teacher bio.',
        'image': dummy_image
    }, content_type='multipart/form-data', follow_redirects=True)

    assert b'Profile created successfully' in response.data

def test_profile_editing(client):
    client.post('/login', data={
        'username': 'testuser1',
        'password': 'testpass'
    }, follow_redirects=True)

    response = client.post('/edit_profile', data={
        'phone': '9999999999',
        'description': 'Updated profile info'
    }, follow_redirects=True)

    assert b'Profile updated successfully' in response.data

def test_create_profile_requires_login(client):
    response = client.get('/create_profile', follow_redirects=True)
    assert b'Login' in response.data or b'Sign Up' in response.data

def test_error_invalid_signup_email(client):
    response = client.post('/signup', data={
        'username': 'bademailuser',
        'email': 'not-an-email',
        'password': 'pass1234',
        'confirm_password': 'pass1234'
    }, follow_redirects=True)
    assert b'Invalid email address' in response.data

def test_error_password_mismatch(client):
    response = client.post('/signup', data={
        'username': 'nomatchuser',
        'email': 'nomatch@example.com',
        'password': 'abc123',
        'confirm_password': 'abc999'
    }, follow_redirects=True)
    assert b'Passwords do not match' in response.data
