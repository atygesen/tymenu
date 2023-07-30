import logging

from flask import render_template, url_for, redirect, flash
from flask_login import current_user

from tymenu.models import MenuPlan, Recipe, MenuPlanItem
from tymenu.resources import get_db
from tymenu.decorators import admin_required, mod_required

from .blueprint import plan_blueprint as planner
from .forms import NewMenuPlanForm, RecipeMenuPlanForm

TIME_FMT = "%Y-%m-%d"
DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

logger = logging.getLogger(__name__)


@planner.route("/plans", methods=["GET", "POST"])
def plan():
    all_plans = MenuPlan.query.all()
    return render_template("menu_plan/plan.html", plans=all_plans)


@planner.route("/plan/new_plan", methods=["GET", "POST"])
@mod_required
def new_plan():
    form = NewMenuPlanForm()

    if form.cancel.data:
        return redirect(url_for(".plan"))

    if form.validate_on_submit():
        db = get_db()

        new_plan = MenuPlan(
            added_by_id=current_user.id,
            title=form.title.data,
            description=form.description.data,
        )
        try:
            db.session.add(new_plan)
            db.session.commit()
        except Exception as exc:
            logger.error("An error happened while creating new plan: %s", exc)
            db.session.rollback()
            flash(f"An error occurred while creating the recipe: {exc}")
            return redirect(url_for("main.index"))
        return redirect(url_for("plan.view_plan", plan_id=new_plan.id))
    return render_template("menu_plan/new_plan.html", form=form)


@planner.route("/plan/view_plan/<int:plan_id>", methods=["GET"])
def view_plan(plan_id):
    plan = MenuPlan.query.get_or_404(plan_id)
    return render_template("menu_plan/view_plan.html", plan=plan)


@planner.route("/plan/add_recipe/<int:plan_id>", methods=["GET", "POST"])
@mod_required
def add_recipe_to_template(plan_id):
    plan = MenuPlan.query.get_or_404(plan_id)

    form = RecipeMenuPlanForm()

    if form.cancel.data:
        return redirect(url_for(".view_plan", plan_id=plan.id))

    if form.validate_on_submit():
        recipe_id = form.recipe_id.data
        Recipe.query.get_or_404(recipe_id)

        menu_plan_recipe = MenuPlanItem(
            menu_plan_id=plan.id,
            recipe_id=recipe_id,
            day=form.day.data,
            days_leftover=form.days_leftover.data,
        )
        db = get_db()
        try:
            db.session.add(menu_plan_recipe)
            db.session.commit()
        except Exception as exc:
            logger.error("An error happened while creating new recipe for plan: %s", exc)
            db.session.rollback()
            flash(f"An error occurred while creating the recipe for plan: {exc}")
            return redirect(url_for("main.index"))
        return redirect(url_for(".view_plan", plan_id=plan.id))
    return render_template("menu_plan/add_recipe_plan.html", plan=plan, form=form)


@planner.route("/plan/delete_plan/<int:plan_id>", methods=["GET", "POST"])
@admin_required
def delete_plan(plan_id):
    plan = MenuPlan.query.get_or_404(plan_id)
    db = get_db()
    try:
        db.session.delete(plan)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.error("Failed to delete plan with id %d: %s", plan.id, exc)
        flash(f"Failed to delete plan: {plan.id}. Error: {exc}")
    return redirect(url_for("main.index"))


@planner.route("/plan/delete_plan_item/<int:item_id>", methods=["GET", "POST"])
@admin_required
def remove_recipe_from_template(item_id: int):
    plan_recipe = MenuPlanItem.query.get_or_404(item_id)
    plan_id = plan_recipe.menu_plan_id
    db = get_db()
    try:
        db.session.delete(plan_recipe)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.error("Failed to delete plan with id %d: %s", plan_recipe.id, exc)
        flash(f"Failed to delete plan: {plan_recipe.id}. Error: {exc}")
    return redirect(url_for(".view_plan", plan_id=plan_id))
