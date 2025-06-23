import os
import io
import pytest
import cloudinary.uploader

# Set environment before app loads config
os.environ["USE_SQLITE"] = "true"

from app import app, db  # Must come after USE_SQLITE
from flask import Flask

# ----- Cloudinary mock -----
def dummy_upload(file):
    return {'secure_url': 'http://dummy.url/test.jpg'}
cloudinary.uploader.upload = dummy_upload

# ----- Test Client Fixture -----
@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

# ----- Tests -----

def test_signup_and_login(client):
    client.post('/signup', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass',
        'confirm_password': 'testpass'
    }, follow_redirects=True)

    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass'
    }, follow_redirects=True)

    assert b'Logout' in response.data

def test_profile_creation(client):
    client.post('/signup', data={
        'username': 'creator',
        'email': 'creator@example.com',
        'password': 'pass123',
        'confirm_password': 'pass123'
    }, follow_redirects=True)

    client.post('/login', data={
        'username': 'creator',
        'password': 'pass123'
    }, follow_redirects=True)

    dummy_image = (io.BytesIO(b'mock image data'), 'dummy.jpg')

    response = client.post('/create_profile', data={
        'phone': '9876543210',
        'description': 'Test teacher bio.',
        'image': dummy_image
    }, content_type='multipart/form-data', follow_redirects=True)

    assert b'Profile created successfully' in response.data

def test_profile_editing(client):
    client.post('/signup', data={
        'username': 'edituser',
        'email': 'edit@example.com',
        'password': 'editpass',
        'confirm_password': 'editpass'
    }, follow_redirects=True)

    client.post('/login', data={
        'username': 'edituser',
        'password': 'editpass'
    }, follow_redirects=True)

    dummy_image = (io.BytesIO(b'mock image'), 'dummy.jpg')
    client.post('/create_profile', data={
        'phone': '1234567890',
        'description': 'Initial',
        'image': dummy_image
    }, content_type='multipart/form-data', follow_redirects=True)

    response = client.post('/edit_profile', data={
        'phone': '9999999999',
        'description': 'Updated bio'
    }, follow_redirects=True)

    assert b'Profile updated successfully' in response.data

def test_create_profile_requires_login(client):
    response = client.get('/create_profile', follow_redirects=True)
    assert b'Login' in response.data or b'Sign Up' in response.data

def test_invalid_email_signup(client):
    response = client.post('/signup', data={
        'username': 'bademail',
        'email': 'invalidemail',
        'password': 'pass123',
        'confirm_password': 'pass123'
    }, follow_redirects=True)
    assert b'Invalid email address' in response.data

def test_password_mismatch(client):
    response = client.post('/signup', data={
        'username': 'mismatch',
        'email': 'mismatch@example.com',
        'password': 'abc123',
        'confirm_password': 'abc456'
    }, follow_redirects=True)
    assert b'Passwords do not match' in response.data
