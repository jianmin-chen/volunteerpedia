from datetime import date
from flask import Blueprint, current_app, flash, redirect, render_template, request, session
from sqlalchemy import select
from uuid import uuid4

from database import db, User, Organization, Event, Participant
from helpers import logged_in_as_user, logged_in_as_organization, authorize_user, authorize_organization, authorize_both

# Configure blueprint
blueprint = Blueprint("events", __name__)


@blueprint.route("/opportunity/<id>")
@authorize_both
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
    is_organizer = False
    joined = False
    if opportunity.organization_id == session["id"]:
        # Organizer gets certain priveleges
        is_organizer = True
    else:
        # Check to see if user has already joined opportunity
        query = db.session.execute(
            select(Participant).where(
                (Participant.user_id == session["id"]) &
                (Participant.event_id == opportunity.id)
            )
        ).fetchone()
        if query:
            joined = True

    return render_template("opportunity.html", opportunity=opportunity, is_organizer=is_organizer, joined=joined)


@blueprint.route("/create", methods=["POST"])
@authorize_organization
def create():
    """Create volunteer opportunity page."""
    title = request.form.get("title")
    description = request.form.get("description")
    hours = request.form.get("hours")
    start = request.form.get("start")

    if not title or not description or not hours or not start:
        # Some fields not filled out
        flash("Some fields weren't filled out! Try again.")
        return redirect("/")

    hours = float(hours)
    start = date(*[int(i) for i in start.split("-")])

    # Create opportunity
    opportunity = Event(
        title=title,
        description=description,
        hours=hours,
        start_date=start,
        xp=hours * current_app.config["XP_PER_HOUR"],
        organization_id=session["id"]
    )
    db.session.add(opportunity)
    db.session.commit()

    return redirect("/")


@blueprint.route("/join", methods=["POST"])
@authorize_user
def join():
    id = request.form.get("id")
    if not id:
        # Some fields not filled out
        flash("There was an issue! Try again.")
        return redirect(request.referrer)

    # Make sure that event exists
    if not db.session.execute(select(Event).where(Event.id == id)).fetchone():
        flash("That opportunity couldn't be found!")
        return redirect(request.referrer)

    # Make sure that user isn't already part of event
    query = db.session.execute(
        select(Participant).where(
            (Participant.user_id == session["id"]) &
            (Participant.event_id == id)
        )
    ).fetchone()
    if query:
        flash("You've already joined!")
        return redirect(request.referrer)

    # Add user as participant
    participant = Participant(
        user_id=session["id"],
        event_id=id
    )
    db.session.add(participant)
    db.session.commit()

    return redirect(request.referrer)


@blueprint.route("/end", methods=["POST"])
@authorize_organization
def end():
    """End opportunity so no more users can join."""
    id = request.form.get("id")
    if not id:
        # Some fields not filled out
        flash("There was an issue! Try again.")
        return redirect(request.referrer)

    # Make sure that event exists
    event = db.session.execute(
        select(Event).where(Event.id == id)
    ).fetchone()
    if not event:
        flash("That opportunity couldn't be found!")
        return redirect(request.referrer)
    elif event[0].organization_id != session["id"]:
        flash("Sorry, you're not allowed to end that volunteer opportunity!")
        return redirect(request.referrer)

    # End openings
    event[0].ended = True
    db.session.add(event[0])
    db.session.commit()

    return redirect(request.referrer)


@blueprint.route("/end_individual", methods=["POST"])
@authorize_organization
def end_individual():
    """End an individual's volunteering and give them their XP and hours."""
    opportunity_id = request.form.get("opportunity_id")
    user_id = request.form.get("user_id")

    if not opportunity_id or not user_id:
        flash("There was an issue! Try again.")
        return redirect(request.referrer)

    # Make sure user exists
    user = db.session.execute(
        select(User).where(User.id == user_id)
    ).fetchone()
    if not user:
        flash("There was an issue! Try again.")
        return redirect(request.referrer)

    # Make sure that event exists, that organization can access event, and that user is part of event
    query = db.session.execute(
        select(Participant).where(
            (Participant.user_id == user_id) &
            (Participant.event_id == opportunity_id)
        )
    ).fetchone()
    if not query:
        flash("There was an issue! Try again.")
        return redirect(request.referrer)
    elif query[0].event.organization_id != session["id"]:
        flash("There was an issue! Try again.")
        return redirect(request.referrer)

    query[0].user.xp += query[0].event.xp
    query[0].user.hours += query[0].event.hours
    query[0].xp_given = True

    db.session.add(query[0])
    db.session.commit()

    return redirect(request.referrer)
