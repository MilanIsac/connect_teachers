import os
import io
import pytest
import cloudinary.uploader
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app as flask_app

# ----- Cloudinary mock -----
def dummy_upload(file):
    return {'secure_url': 'http://dummy.url/test.jpg'}
cloudinary.uploader.upload = dummy_upload

# ----- Test Client Fixture -----
@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    with flask_app.test_client() as client:
        with flask_app.app_context():
            yield client

# ----- Tests -----

@patch('app.mysql')
def test_signup_and_login(mock_mysql, client):
    cursor = MagicMock()
    mock_mysql.connection.cursor.return_value = cursor
    cursor.fetchone.side_effect = [None,  # user not exists on signup check
                                   {'id': 1, 'username': 'testuser', 'password': 'hashed'}]  # after insert

    client.post('/signup', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass',
        'confirm_password': 'testpass'
    }, follow_redirects=True)

    cursor.fetchone.return_value = {'id': 1, 'username': 'testuser', 'password': 'hashed'}

    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass'
    }, follow_redirects=True)

    assert b'Logout' in response.data or b'Profile' in response.data

@patch('app.mysql')
def test_profile_creation(mock_mysql, client):
    cursor = MagicMock()
    mock_mysql.connection.cursor.return_value = cursor
    cursor.fetchone.return_value = None  # profile does not exist

    with client.session_transaction() as sess:
        sess['username'] = 'creator'
        sess['user_id'] = 1

    dummy_image = (io.BytesIO(b'mock image data'), 'dummy.jpg')

    response = client.post('/create_profile', data={
        'phone': '9876543210',
        'description': 'Test bio.',
        'image': dummy_image
    }, content_type='multipart/form-data', follow_redirects=True)

    assert b'Profile created successfully' in response.data

@patch('app.mysql')
def test_profile_editing(mock_mysql, client):
    cursor = MagicMock()
    mock_mysql.connection.cursor.return_value = cursor
    cursor.fetchone.side_effect = [{'user_id': 1}, {'phone': '000', 'description': 'desc', 'image': 'img.jpg'}]

    with client.session_transaction() as sess:
        sess['username'] = 'edituser'
        sess['user_id'] = 1

    response = client.post('/edit_profile', data={
        'phone': '9999999999',
        'description': 'Updated bio'
    }, follow_redirects=True)

    assert b'Profile updated successfully' in response.data

@patch('app.mysql')
def test_create_profile_requires_login(mock_mysql, client):
    response = client.get('/create_profile', follow_redirects=True)
    assert b'Login' in response.data or b'Sign Up' in response.data

@patch('app.mysql')
def test_invalid_email_signup(mock_mysql, client):
    response = client.post('/signup', data={
        'username': 'bademail',
        'email': 'invalidemail',
        'password': 'pass123',
        'confirm_password': 'pass123'
    }, follow_redirects=True)
    assert b'Invalid email address' in response.data

@patch('app.mysql')
def test_password_mismatch(mock_mysql, client):
    response = client.post('/signup', data={
        'username': 'mismatch',
        'email': 'mismatch@example.com',
        'password': 'abc123',
        'confirm_password': 'abc456'
    }, follow_redirects=True)
    assert b'Passwords do not match' in response.data
