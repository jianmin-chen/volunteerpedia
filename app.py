from flask import Flask
from flask_session import Session
from os import environ

from database import db
from routes import events, general

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    """Add and edit headers so responses aren't cached."""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = environ.get("DATABASE_URL").replace("postgres", "postgresql")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Configure session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure custom variables
app.config["DOMAIN_URL"] = "http://127.0.0.1:5000"

# Configure routes
app.register_blueprint(events.blueprint)
app.register_blueprint(general.blueprint)
