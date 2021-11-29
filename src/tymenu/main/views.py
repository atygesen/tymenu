from flask import render_template
from tymenu.models import Recipe
from . import main_blueprint as main


@main.route("/")
def index():
    recipes = Recipe.query.order_by(Recipe.timestamp.desc()).all()
    return render_template("index.html", recipes=recipes, recipes_list_max=5)
