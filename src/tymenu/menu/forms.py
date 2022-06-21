from typing import Dict, Any
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, IntegerField, FloatField, SelectField
from wtforms.validators import DataRequired, ValidationError, Optional
from flask_pagedown.fields import PageDownField
from flask_login import current_user
from tymenu.models import Recipe, KcalType
from markupsafe import Markup
import emoji


def _make_label(text, is_required=True):
    # Add a star emoji if this field is required.
    star = emoji.emojize("<sup>:star2:</sup>", language="alias", variant="emoji_type")
    if is_required:
        text = f"{text} {star}"
    return Markup(text)


class RecipeForm(FlaskForm):
    title = StringField(_make_label("Title:"), validators=[DataRequired()])
    background = PageDownField("Background:", validators=[Optional(strip_whitespace=True)])
    servings = IntegerField(_make_label("Number of servings:"), validators=[DataRequired()])
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
    ingredients = PageDownField(_make_label("Ingredients:"), validators=[DataRequired()])
    instructions = PageDownField(_make_label("Instructions:"), validators=[DataRequired()])
    keywords = StringField(_make_label("Keywords:"), validators=[DataRequired()])
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
        ]

    def validate_title(self, field) -> None:
        """Ensure the title does not already exist in the database."""
        existing_recipe = Recipe.query.filter_by(title=field.data).all()
        for recipe in existing_recipe:
            if self._recipe_matches_title(recipe, field.data):
                raise ValidationError("Title exists already.")

    def _recipe_matches_title(self, recipe: Recipe, title: str) -> bool:
        return recipe.title == title

    def construct_recipe_kwargs(self, author=True) -> Dict[str, Any]:
        kwargs = {}
        for field in self.all_data_field_names():
            kwargs[field] = getattr(self, field).data
        if author:
            kwargs.update(author=current_user._get_current_object())
        print("FORM", kwargs)
        return kwargs

    def construct_new_recipe(self) -> Recipe:
        return Recipe(**self.construct_recipe_kwargs(author=True))

    def update_recipe(self, recipe: Recipe) -> None:
        """Update an existing recipe. Does not update the author"""
        kwargs = self.construct_recipe_kwargs(author=False)
        for key, value in kwargs.items():
            setattr(recipe, key, value)
        recipe.last_updated = datetime.utcnow()

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
