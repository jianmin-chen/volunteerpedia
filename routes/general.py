from flask import Blueprint, current_app, flash, redirect, render_template, request, session
from sqlalchemy import func, select
from uuid import uuid4
from werkzeug.security import check_password_hash, generate_password_hash

from database import db, User, Organization, Event, Participant
from helpers import logged_in_as_user, logged_in_as_organization, authorize_user, authorize_organization, authorize_both

# Configure blueprint
blueprint = Blueprint("general", __name__)


@blueprint.route("/")
def index():
    """Return sign in page or dashboard depending on whether logged in or not."""
    if logged_in_as_user():
        # Email, username, description, XP, XP to next level, leaderboard, recent opportunities, joined opportunities
        user = db.session.execute(
            select(User).where(User.id == session["id"])
        ).fetchone()[0]
        opportunities = db.session.execute(
            select(Event).order_by(Event.start_date.desc())
        ).fetchall()

        leaderboard = db.session.execute(
            select(User).where(User.hours > user.hours).order_by(User.hours.desc())
        ).fetchall()
        if len(leaderboard) <= 15:
            # User is in top 15
            leaderboard = db.session.execute(
                select(User).order_by(User.hours.desc()).limit(15)
            ).fetchall()
            leaderboard_position = None
        else:
            leaderboard_position = len(leaderboard) + 1

        return render_template(
            "user-dashboard.html",
            name=user.username,
            email=user.email,
            xp=user.xp,
            hours=user.hours,
            joined_opportunities=user.events,
            opportunities=opportunities,
            leaderboard=leaderboard[:15],
            leaderboard_position=leaderboard_position
        )
    elif logged_in_as_organization():
        # Name, description, events created sorted by start date, create opportunity
        organization = db.session.execute(
            select(Organization).where(Organization.id == session["id"])
        ).fetchone()[0]
        events = db.session.execute(
            select(Event).where(Event.organization_id == session["id"]).order_by(Event.start_date.desc())
        ).fetchall()

        return render_template("organization-dashboard.html", name=organization.name, description=organization.description, events=events)

    # Not logged in at all
    return redirect("/signin")


@blueprint.route("/signup", methods=["GET", "POST"])
def signup():
    """Sign up page."""
    if request.method == "GET":
        return render_template("signup.html")

    type = request.form.get("type")
    if not type or type not in ("user", "organization"):
        flash("Make sure you're signing up either as a user or organization.")
        return redirect("/signup")

    if type == "user":
        # Sign up as user
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        if not email or not username or not password:
            # Some fields not filled out
            flash("Some fields weren't filled out! Try again.")
            return redirect("/signup")
        elif db.session.execute(select(User).where(User.email == email)).fetchone():
            # User already exists
            flash("User already exists. Try signing in!")
            return redirect("/signup")
        elif db.session.execute(select(User).where(User.username == username)).fetchone():
            # Username already taken
            flash("That username is already taken. Try adding a couple of numbers to the end of your name!")
            return redirect("/signup")

        # Create user
        new = User(
            id=str(uuid4()),
            email=email,
            username=username,
            password=generate_password_hash(password)
        )
    else:
        # Sign up as organization
        name = request.form.get("name")
        description = request.form.get("description")
        password = request.form.get("password")
        if not name or not description or not password:
            flash("Some fields weren't filled out! Try again.")
            return redirect("/signup")
        elif db.session.execute(select(Organization).where(Organization.name == name)).fetchone():
            # Organization alreay exists
            flash("Organization already exists. Try signing in!")
            return redirect("/signup")

        # Create organization
        new = Organization(
            id=str(uuid4()),
            name=name,
            description=description,
            password=generate_password_hash(password)
        )

    # Update database
    db.session.add(new)
    db.session.commit()

    flash("Your account has successfully been created!")
    return redirect("/signin")


@blueprint.route("/signin", methods=["GET", "POST"])
def signin():
    """Sign in page."""
    if request.method == "GET":
        return render_template("signin.html")

    type = request.form.get("type")
    if not type or type not in ("user", "organization"):
        flash("Make sure you're signing in either as a user or organization.")
        return redirect("/signin")

    if type == "user":
        # Sign in as user
        email = request.form.get("email")
        password = request.form.get("password")
        if not email or not password:
            # Some fields not filled out
            flash("Some fields weren't filled out! Try again.")
            return redirect("/signup")

        user = db.session.execute(
            select(User).where(User.email == email)
        ).fetchone()
        if not user:
            # Invalid email
            flash("Looks like you're not a user yet! Perhaps try signing up.")
            return redirect("/signin")
        elif not check_password_hash(user[0].password, password):
            # Email and password don't match
            flash("Looks like your email or password is incorrect! Try again.")
            return redirect("/signin")

        id = user[0].id
    else:
        # Sign in as organization
        name = request.form.get("name")
        password = request.form.get("password")
        if not name or not password:
            flash("Some fields weren't filled out! Try again.")
            return redirect("/signin")

        organization = db.session.execute(
            select(Organization).where(Organization.name == name)
        ).fetchone()
        if not organization:
            # Invalid organization name
            flash("Looks like that organization hasn't joined VolunteerPedia yet! Try signing up.")
            return redirect("/signin")
        elif not check_password_hash(organization[0].password, password):
            # Name and password don't match
            flash("Looks like your name or password is incorrect! Try again.")
            return redirect("/signin")

        id = organization[0].id

    # Save ID and password to session so user/org can stay logged in
    session["id"] = id
    session["password"] = password

    return redirect("/")


@blueprint.route("/signout")
@authorize_both
def signout():
    """Log out page."""
    session.clear()
    return redirect("/")
