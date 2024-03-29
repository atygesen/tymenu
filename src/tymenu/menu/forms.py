from __future__ import annotations

from datetime import datetime
from typing import Any

from flask_login import current_user
from flask_pagedown.fields import PageDownField
from flask_wtf import FlaskForm
from wtforms import DateField, FloatField, IntegerField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, InputRequired, NumberRange, Optional, ValidationError

from tymenu.models import KcalType, Recipe
from tymenu.timestamp import get_now_utc
from tymenu.utils import label_is_required


class RecipeForm(FlaskForm):
    title = StringField(label_is_required("Title:"), validators=[DataRequired()])
    background = PageDownField("Background:", validators=[Optional(strip_whitespace=True)])
    servings = IntegerField(label_is_required("Number of servings:"), validators=[DataRequired()])
    kcal_type = SelectField(
        "Kcal type:",
        choices=[
            (str(KcalType.PER_PERSON.value), "Per Person"),
            (str(KcalType.TOTAL.value), "Total"),
        ],
        coerce=int,
    )
    kcal = FloatField("Calories:", validators=[Optional(strip_whitespace=True)])
    protein_gram = FloatField("Protein (g):", validators=[Optional(strip_whitespace=True)])
    carb_gram = FloatField("Carbs (g):", validators=[Optional(strip_whitespace=True)])
    fat_gram = FloatField("Fat (g):", validators=[Optional(strip_whitespace=True)])
    cooking_time_min = FloatField(
        "Cooking time (minutes):", validators=[Optional(strip_whitespace=True)]
    )

    ingredients = PageDownField(label_is_required("Ingredients:"), validators=[DataRequired()])
    instructions = PageDownField(label_is_required("Instructions:"), validators=[DataRequired()])
    keywords = StringField(label_is_required("Keywords:"), validators=[DataRequired()])
    source = StringField("Source:")
    submit = SubmitField("Submit")
    cancel = SubmitField(label="Cancel", render_kw={"formnovalidate": True})

    @staticmethod
    def all_data_field_names():
        return [
            "title",
            "background",
            "ingredients",
            "instructions",
            "keywords",
            "source",
            "servings",
            "kcal",
            "kcal_type",
            "protein_gram",
            "carb_gram",
            "fat_gram",
            "cooking_time_min",
        ]

    def validate_title(self, field) -> None:
        """Ensure the title does not already exist in the database."""
        existing_recipe = Recipe.query.filter_by(title=field.data).all()
        for recipe in existing_recipe:
            if self._recipe_matches_title(recipe, field.data):
                raise ValidationError("Title exists already.")

    def _recipe_matches_title(self, recipe: Recipe, title: str) -> bool:
        return recipe.title == title

    def construct_recipe_kwargs(self, author=True) -> dict[str, Any]:
        kwargs = {}
        for field in self.all_data_field_names():
            kwargs[field] = getattr(self, field).data
        if author:
            kwargs.update(author=current_user._get_current_object())
        return kwargs

    def construct_new_recipe(self) -> Recipe:
        return Recipe(**self.construct_recipe_kwargs(author=True))

    def update_recipe(self, recipe: Recipe) -> None:
        """Update an existing recipe. Does not update the author"""
        kwargs = self.construct_recipe_kwargs(author=False)
        for key, value in kwargs.items():
            setattr(recipe, key, value)
        recipe.last_updated = get_now_utc()

    def fill_from_existing_recipe(self, recipe: Recipe):
        """Fill fields from an existing recipe"""
        for field in self.all_data_field_names():
            value = getattr(recipe, field)
            if value is not None:
                getattr(self, field).data = value


class EditRecipeForm(RecipeForm):
    def __init__(self, edit_id: int, **kwargs):
        super().__init__(**kwargs)
        self.edit_id = edit_id  # ID of the recipe which is being edited.

    def _recipe_matches_title(self, recipe: Recipe, title: str) -> bool:
        if recipe.id == self.edit_id:
            # This is our own recipe we're editing.
            return False
        return super()._recipe_matches_title(recipe, title)


class SimpleSearch(FlaskForm):
    search_string = StringField("Search:")
    submit = SubmitField("Submit")


class PlannerAdder(FlaskForm):
    entrydate = DateField(
        "Date:", format="%Y-%m-%d", default=datetime.today, validators=[DataRequired()]
    )
    leftovers = IntegerField(
        "Leftovers:", default=0, validators=[InputRequired(), NumberRange(min=0)]
    )
    note = PageDownField("Note:")
    submit = SubmitField("Submit")
    cancel = SubmitField(label="Cancel", render_kw={"formnovalidate": True})
