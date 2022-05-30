from flask import redirect, url_for, render_template, flash, request, current_app
from flask_login.utils import login_required
from sqlalchemy.exc import IntegrityError
from tymenu.models import Recipe
from tymenu.resources import get_db
from tymenu.decorators import mod_required
from .blueprint import menu_blueprint as menu
from .forms import RecipeForm, SimpleSearch, EditRecipeForm


@menu.route("/new_recipe", methods=["GET", "POST"])
@login_required
def new_recipe():
    form = RecipeForm()

    if form.cancel.data:
        return redirect(url_for("main.index"))

    if form.validate_on_submit():
        recipe = form.construct_new_recipe()
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
    form = SimpleSearch()
    if form.validate_on_submit():
        q = form.search_string.data
        return redirect(url_for(".search_results", q=q))
    return render_template("menu/search.html", form=form)


@menu.route("/search_results")
def search_results():
    """Return the results of the seach query"""
    page = request.args.get("page", 1, type=int)
    search_string = request.args.get("q", None)

    recipes = []
    pagination = None
    results_total = 0
    if search_string is not None:
        query = Recipe.search_string(search_string).order_by(Recipe.timestamp.desc())
        pagination = query.paginate(
            page,
            per_page=current_app.config["TYMENU_RECIPES_PER_PAGE"],
            error_out=False,
        )
        recipes = pagination.items
        results_total = query.count()
    return render_template(
        "menu/search_results.html",
        q=search_string,
        recipes=recipes,
        pagination=pagination,
        results_total=results_total,
    )


@menu.route("/recipe/<int:recipe_id>", methods=["GET"])
def view_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    return render_template("menu/recipe.html", recipe=recipe)


@menu.route("/edit/<int:recipe_id>", methods=["GET", "POST"])
@login_required
@mod_required
def edit_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    # Allow any user to edit?
    form = EditRecipeForm(recipe_id)
    if request.method == "POST":
        if form.cancel.data:
            return redirect(url_for("menu.view_recipe", recipe_id=recipe_id))
    if form.validate_on_submit():
        form.update_recipe(recipe)
        db = get_db()
        try:
            db.session.add(recipe)
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            flash(f"An error occurred while updating recipe: {exc}")
        else:
            flash(f"Recipe '{recipe.title}' has been updated.")
        return redirect(url_for(".view_recipe", recipe_id=recipe_id))
    form.fill_from_existing_recipe(recipe)
    return render_template("menu/edit_recipe.html", form=form, recipe=recipe)


@menu.route("/delete/<int:recipe_id>")
@login_required
@mod_required
def delete_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    db = get_db()
    try:
        db.session.delete(recipe)
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        flash(f"An error occurred while updating recipe: {exc}")
    else:
        flash(f"Recipe '{recipe.title}' was deleted.")

    return redirect(url_for("main.index"))
