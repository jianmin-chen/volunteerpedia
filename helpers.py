from flask import flash, redirect, session
from functools import wraps
from sqlalchemy import select
from werkzeug.security import check_password_hash

from database import db, User, Organization


def logged_in_as_user():
    """Logged in function that determines if user is logged in."""
    if session.get("id") is None or session.get("password") is None:
        # User isn't signed in yet
        return False

    query = db.session.execute(
        select(User).where(User.id == session["id"])
    ).fetchone()
    if not query:
        return False
    elif not check_password_hash(query[0].password, session["password"]):
        # Invalid password
        return False

    # User is signed in
    return True


def logged_in_as_organization():
    """Logged in function that determines if organization is logged in."""
    if session.get("id") is None or session.get("password") is None:
        # Organization isn't signed in yet
        return False

    query = db.session.execute(
        select(Organization).where(Organization.id == session["id"])
    ).fetchone()
    if not query:
        return False
    elif not check_password_hash(query[0].password, session["password"]):
        # Invalid password
        return False

    # Organization is signed in
    return True


def authorize_user(f):
    """Authorize function that makes sure user is logged in before they can access a view."""
    @wraps(f)
    def decorate(*args, **kwargs):
        if not logged_in_as_user():
            if logged_in_as_organization():
                # Organization is logged in, not user
                flash("Oops, that page is reserved for users!")
                return redirect("/")
            # User isn't logged in yet
            flash("Oops, looks like you need to log in first!")
            return redirect("/signin")

        # Apply Flask headers, etc.
        return f(*args, **kwargs)

    return decorate


def authorize_organization(f):
    """Authorize function that makes sure organization is logged in before they can access a view."""
    @wraps(f)
    def decorate(*args, **kwargs):
        if not logged_in_as_organization():
            if logged_in_as_user():
                # User is logged in, not organization
                flash("Oops, that page is reserved for organizations!")
                return redirect("/")
            # Organization isn't logged in yet
            flash("Oops, looks like you need to log in first!")
            return redirect("/signin")

        # Apply Flask headers, etc.
        return f(*args, **kwargs)

    return decorate


def authorize_both(f):
    """Authorize function that makes sure either a user or organization is logged in before they can access a view."""
    @wraps(f)
    def decorate(*args, **kwargs):
        if not logged_in_as_user() or not logged_in_as_organization():
            flash("Oops, looks like you need to log in first!")
            return redirect("/signin")

        # Apply Flask headers, etc.
        return f(*args, **kwargs)

    return decorate
