import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mysqldb import MySQL
from dotenv import load_dotenv
import cloudinary

# Load environment variables from .env file
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
mysql = MySQL()

def create_app():
    app = Flask(__name__, template_folder='frontend/templates', static_folder='frontend/static')

    # Secret key
    app.secret_key = os.getenv('APP_SECRET_KEY', 'default-secret-key')

    # SQLite fallback
    USE_SQLITE = os.getenv('USE_SQLITE', 'false').lower() == 'true'
    if USE_SQLITE:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    else:
        db_url = os.getenv('DATABASE_URL')
        if db_url:
            if db_url.startswith("mysql://"):
                db_url = db_url.replace("mysql://", "mysql+pymysql://")
            app.config['SQLALCHEMY_DATABASE_URI'] = db_url
        else:
            app.config['SQLALCHEMY_DATABASE_URI'] = (
                f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}"
                f"@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT', '3306')}/{os.getenv('MYSQL_DB')}"
            )

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize SQLAlchemy
    db.init_app(app)

    # MySQL
    app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
    app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
    app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
    app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
    mysql.init_app(app)

    # Cloudinary configuration
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
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

