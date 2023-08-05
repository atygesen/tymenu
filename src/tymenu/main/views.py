from __future__ import annotations

import logging

from flask import abort, current_app, flash, redirect, render_template, request, url_for
from sqlalchemy import exc

from tymenu.decorators import login_required
from tymenu.models import Recipe, User
from tymenu.resources import get_db

from . import main_blueprint as main
from .forms import ChangeUsernameForm

logger = logging.getLogger(__name__)


@main.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    pagination = Recipe.query.order_by(Recipe.timestamp.desc()).paginate(
        page=page,
        per_page=current_app.config["TYMENU_RECIPES_PER_PAGE"],
        error_out=False,
    )
    recipes = pagination.items
    return render_template("index.html", recipes=recipes, recipes_list_max=5, pagination=pagination)


@main.route("/users")
def users():
    page = request.args.get("page", 1, type=int)
    pagination = User.query.order_by(User.id.asc()).paginate(
        page=page,
        per_page=current_app.config["TYMENU_USERS_PER_PAGE"],
        error_out=False,
    )
    users = pagination.items
    return render_template("main/users.html", users=users, pagination=pagination)


@main.route("/profile/<int:id>")
def profile(id):
    user: User = User.query.get_or_404(id)
    page = request.args.get("page", 1, type=int)
    pagination = user.recipes.order_by(Recipe.timestamp.desc()).paginate(
        page=page,
        per_page=5,
        error_out=False,
    )
    recipes = pagination.items
    return render_template(
        "main/profile.html",
        user=user,
        recipes=recipes,
        recipes_list_max=5,
        pagination=pagination,
    )


@main.route("/profile/change_username/<int:id>", methods=["GET", "POST"])
@login_required
def change_username(id):
    user: User = User.query.get_or_404(id)
    if not user.is_current_user:
        # Only the user itself is allowed to change this.
        abort(403)

    form = ChangeUsernameForm()
    if form.cancel.data:
        return redirect(url_for(".profile", id=id))

    if form.validate_on_submit():
        user.username = form.username.data
        db = get_db()
        try:
            db.session.add(user)
            db.session.commit()
        except exc.IntegrityError as e:
            db.session.rollback()
            flash("Username already exists.")
            logger.error("Failed to change username for user %d. Error: %s", user.id, e)
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to change username: {e}")
            logger.error("Failed to change username for user %d. Error: %s", user.id, e)
        else:
            flash(f"Successfully changed username to {user.username}")
        return redirect(url_for(".profile", id=id))

    return render_template("main/change_username.html", form=form)


@main.route("/links")
def links():
    return render_template("links.html")
