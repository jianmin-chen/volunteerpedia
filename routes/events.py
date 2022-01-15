from datetime import date
from flask import Blueprint, current_app, flash, redirect, render_template, request, session
from sqlalchemy import select
from uuid import uuid4

from database import db, User, Organization, Event
from helpers import logged_in_as_user, logged_in_as_organization, authorize_user, authorize_organization, authorize_both

# Configure blueprint
blueprint = Blueprint("events", __name__)


@blueprint.route("/opportunity/<id>")
def opportunity(id):
    """View volunteer opportunity page."""
    opportunity = db.session.execute(
        select(Event).where(Event.id == id)
    ).fetchone()
    if not opportunity:
        # No opportunity found with ID
        flash("No opportunity found.")
        return redirect("/")

    opportunity = opportunity[0]

    return render_template("opportunity.html", opportunity=opportunity)


@blueprint.route("/create", methods=["POST"])
@authorize_organization
def create():
    """Create volunteer opportunity page."""
    title = request.form.get("title")
    description = request.form.get("description")
    hours = request.form.get("hours")
    start = request.form.get("start")
    xp = request.form.get("xp")

    if not title or not description or not hours or not start or not xp:
        # Some fields not filled out
        flash("Some fields weren't filled out! Try again.")
        return redirect("/")

    hours = int(hours)
    start = date(*[int(i) for i in start.split("-")])
    xp = int(xp)

    if xp < 1 or xp > 100:
        # Error
        flash("Invalid amount of XP! It should be between 1 and 100.")
        return redirect("/")

    # Create opportunity
    opportunity = Event(
        title=title,
        description=description,
        hours=hours,
        start_date=start,
        xp=xp,
        organization_id=session["id"]
    )
    db.session.add(opportunity)
    db.session.commit()

    return redirect("/")


@blueprint.route("/join", methods=["POST"])
@authorize_user
def join():
    pass
