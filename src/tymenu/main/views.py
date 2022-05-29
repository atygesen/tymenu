from flask import render_template, request, current_app
from tymenu.models import Recipe, User
from . import main_blueprint as main


@main.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    pagination = Recipe.query.order_by(Recipe.timestamp.desc()).paginate(
        page,
        per_page=current_app.config["TYMENU_RECIPES_PER_PAGE"],
        error_out=False,
    )
    recipes = pagination.items
    return render_template("index.html", recipes=recipes, recipes_list_max=5, pagination=pagination)


@main.route("/profile/<int:id>")
def profile(id):
    user = User.query.get_or_404(id)
    page = request.args.get("page", 1, type=int)
    pagination = user.recipes.order_by(Recipe.timestamp.desc()).paginate(
        page,
        per_page=5,
        error_out=False,
    )
    recipes = pagination.items
    return render_template(
        "profile.html", user=user, recipes=recipes, recipes_list_max=5, pagination=pagination
    )
