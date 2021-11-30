from flask import redirect, url_for, render_template, flash
from flask_login import current_user
from sqlalchemy.exc import IntegrityError
from tymenu.models import Recipe
from tymenu.resources import get_db
from .blueprint import menu_blueprint as menu
from .forms import PostRecipe, SearchRecipes


@menu.route("/new_recipe", methods=["GET", "POST"])
def new_recipe():
    form = PostRecipe()

    if form.validate_on_submit():
        recipe = Recipe(
            title=form.title.data,
            ingredients=form.ingredients.data,
            keywords=form.keywords.data,
            author=current_user._get_current_object(),
        )
        db = get_db()
        try:
            db.session.add(recipe)
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            flash(f"An error occurred while creating the recipe: {exc}")
        else:
            flash(f"New recipe '{recipe.title}' has been added.")
        return redirect(url_for(".new_recipe"))
    return render_template("menu/new_recipe.html", form=form)


def _parse_search_form(form):
    keywords = None
    if form.keywords.data:
        keywords = [k.strip() for k in form.keywords.data.split(",") if k.strip()]
    title = form.title.data or None
    ingredients = None
    if form.ingredients.data:
        ingredients = [k.strip() for k in form.ingredients.data.split() if k.strip()]
    return Recipe.build_query(title=title, ingredients=ingredients, keywords=keywords)


@menu.route("/search", methods=["GET", "POST"])
def search():
    form = SearchRecipes()
    if form.validate_on_submit():
        query = _parse_search_form(form)
        results = query.all()
        if len(results) == 0:
            flash("No results found.")
        return render_template("menu/search.html", form=form, recipes=results)
    return render_template("menu/search.html", form=form)
