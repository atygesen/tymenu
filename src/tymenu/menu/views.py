from typing import NamedTuple, Optional
import base64
import requests
import tempfile
import logging
from flask import redirect, url_for, render_template, flash, request, current_app
from flask_login import current_user
from sqlalchemy.exc import IntegrityError
from werkzeug.datastructures import FileStorage
from tymenu.models import Recipe
from tymenu.resources import get_db
from tymenu.decorators import mod_required, login_required
from .blueprint import menu_blueprint as menu
from .forms import RecipeForm, SimpleSearch, EditRecipeForm

from . import forms

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


class ImageUrlData(NamedTuple):
    display_url: str
    delete_url: str
    thumb_url: str
    url_viewer: str


def redirect_recipe(recipe_id: int):
    return redirect(url_for("menu.view_recipe", recipe_id=recipe_id))


def _do_upload_file(file: FileStorage) -> Optional[ImageUrlData]:
    """Upload the image file to img BB"""
    config = current_app._get_current_object().config
    api_key = config["IMGBB_API_KEY"]
    if not api_key:
        flash("imgbb API key is not configured.")
        logger.warning("No API key for imgbb.")
        return None

    logger.info("Uploading file: %s", file.filename)
    with tempfile.TemporaryFile() as dst:
        file.save(dst)
        dst.seek(0)
        encoded = base64.b64encode(dst.read())

    url = "https://api.imgbb.com/1/upload"
    payload = {
        "key": api_key,
        "image": encoded,
    }
    res = requests.post(url, payload, allow_redirects=False)

    if res.status_code != 200:
        logger.error("Status code '%s', will not upload. Content: %s", res.status_code, res.content)
        # Something happened
        # Try to fetch the error message
        json_response: dict = res.json()
        error = json_response.get("error", None)
        if isinstance(error, dict):
            # Recover the error message
            msg = error.get("message", "")
            flash(f"An error occured during upload: {msg}")
        else:
            # Something else happened... ?
            flash("An error occured during upload.")
        return None
    else:
        logger.info("Retrieved payload: %s. As JSON: %s", res, res.json())

    flash("Image was uploaded.")

    # Retrieve the display URL
    data = res.json().get("data", None)
    if data is None:
        flash("No data was received?")
        logger.info("No data.")
        return None
    delete_url = data["delete_url"]
    display_url = data["display_url"]
    thumb_url = data["thumb"]["url"]
    url_viewer = data["url_viewer"]
    return ImageUrlData(display_url, delete_url, thumb_url, url_viewer)


@menu.route("/upload/<int:recipe_id>", methods=["GET", "POST"])
@login_required
@mod_required
def upload_file(recipe_id: int):
    recipe = Recipe.query.get_or_404(recipe_id)
    if request.method == "POST":
        # check if the post request has the file part
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["file"]
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == "":
            flash("No file was selected.")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            url_data = _do_upload_file(file)
            if url_data is None:
                # Something went wrong
                return redirect_recipe(recipe_id)
            recipe.img_display_url = url_data.display_url
            recipe.img_delete_url = url_data.delete_url
            recipe.img_thumbnail_url = url_data.thumb_url
            recipe.img_url_viewer = url_data.url_viewer

            db = get_db()
            try:
                db.session.commit()
            except Exception as exc:
                logger.error("An error occurred during commit: %s", exc)
                db.session.rollback()
                flash(f"An error occurred while creating the recipe: {exc}")
            else:
                logger.info("Comitted image URL's to recipe with ID %s", recipe.id)
            return redirect_recipe(recipe_id)
    return render_template("menu/upload_image.html", recipe_id=recipe_id)


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
        except Exception as exc:
            logger.error("An error happened while comitting recipe: %s", exc)
            db.session.rollback()
            flash(f"An error occurred while creating the recipe: {exc}")
            return redirect(url_for("main.index"))
        else:
            logger.info(
                "Added a new recipe to DB with ID '%s' and title '%s'", recipe.id, recipe.title
            )
            flash(f"New recipe '{recipe.title}' has been added.")
        return redirect_recipe(recipe.id)
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
            page=page,
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
            logger.error("An error occurred during update: %s", exc)
            db.session.rollback()
            flash(f"An error occurred while updating recipe: {exc}")
        else:
            logger.info("Comitted edit to recipe with ID: %s", recipe.id)
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
    logger.info("Deleting recipe with ID: %d", recipe.id)
    try:
        db.session.delete(recipe)
        db.session.commit()
    except IntegrityError as exc:
        logger.error("An error occurred during delete: %s", exc)
        db.session.rollback()
        flash(f"An error occurred while deleting recipe: {exc}")
    else:
        logger.info("Recipe %s was deleted.", recipe.title)
        flash(f"Recipe '{recipe.title}' was deleted.")

    return redirect(url_for("main.index"))


# @menu.route("/planner_add/<int:recipe_id>", methods=["GET", "POST"])
# @login_required
# @mod_required
# def add_to_plan(recipe_id):
#     recipe: Recipe = Recipe.query.get_or_404(recipe_id)

#     form = forms.PlannerAdder()

#     if form.cancel.data:
#         return redirect(url_for("main.index"))

#     if form.validate_on_submit():
#         db = get_db()

#         plan_item = MenuPlanItem(
#             added_by=current_user.id,
#             recipe_id=recipe.id,
#             date=form.entrydate.data,
#             leftovers=form.leftovers.data,
#             note=form.note.data,
#         )

#         try:
#             db.session.add(plan_item)
#             db.session.commit()
#         except IntegrityError as exc:
#             logger.error("An error occurred while adding menu plan item: %s", exc)
#             db.session.rollback()
#             flash(f"An error occurred while adding menu plan item: {exc}")
#         else:
#             logger.info("Created menu plan with id: %s", plan_item.id)
#             flash("Added item to menu plan")
#         return redirect(url_for("main.index"))
#     return render_template("menu/add_to_plan.html", form=form, recipe=recipe)
