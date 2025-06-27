import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mysqldb import MySQL
from dotenv import load_dotenv
import cloudinary

# Load environment variables
load_dotenv()

db = SQLAlchemy()
mysql = MySQL()

def create_app():
    app = Flask(__name__, template_folder='frontend/templates', static_folder='frontend/static')

    # Secret key for sessions
    app.secret_key = os.getenv('APP_SECRET_KEY')

    # Determine database
    USE_SQLITE = os.environ.get('USE_SQLITE', 'false').lower() == 'true'
    if USE_SQLITE:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}/{os.getenv('MYSQL_DB')}"

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize DB
    db.init_app(app)

    # MySQL Configuration (used by raw SQL queries)
    app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
    app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
    app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
    app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

    mysql.init_app(app)

    # Cloudinary config
    cloudinary.config(
        cloud_name=os.getenv('CLOUD_NAME'),
        api_key=os.getenv('API_KEY'),
        api_secret=os.getenv('API_SECRET')
    )

    # Register blueprints
    from controllers.auth_controller import auth_bp
    from controllers.profile_controller import profile_bp
    from views.errors import errors_bp
    from controllers.main_controller import main_bp
    
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(errors_bp)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
