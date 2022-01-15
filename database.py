from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Set up database
db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.String, primary_key=True)
    username = db.Column(db.String(64), nullable=False, unique=True)
    email = db.Column(db.String(64), nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    xp = db.Column(db.Integer, default=0, nullable=False)

    events = db.relationship("Participant", back_populates="user")

class Organization(db.Model):
    __tablename__ = "organizations"
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    description = db.Column(db.String(512), nullable=False)
    password = db.Column(db.String, nullable=False)

    events = db.relationship("Event", back_populates="organizer")

class Event(db.Model):
    __tablename__ = "events"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(512), nullable=False)
    hours = db.Column(db.SmallInteger, nullable=False)
    start_date = db.Column(db.Date, default=datetime.utcnow(), nullable=False)
    xp = db.Column(db.SmallInteger, nullable=False)
    ended = db.Column(db.Boolean, default=False, nullable=False)
    organization_id = db.Column(db.String, db.ForeignKey("organizations.id"), nullable=False)

    organizer = db.relationship("Organization", back_populates="events")
    participants = db.relationship("Participant", back_populates="event")

class Participant(db.Model):
    __tablename__ = "participants"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    xp_given = db.Column(db.Boolean, default=False, nullable=False)

    event = db.relationship("Event", back_populates="participants")
    user = db.relationship("User", back_populates="events")
