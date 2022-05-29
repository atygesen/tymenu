from typing import Dict, Any
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField
from wtforms.validators import DataRequired, ValidationError
from flask_pagedown.fields import PageDownField
from flask_login import current_user
from tymenu.models import Recipe


class RecipeForm(FlaskForm):
    title = StringField("Title:", validators=[DataRequired()])
    ingredients = PageDownField("Ingredients:", validators=[DataRequired()])
    instructions = PageDownField("Instructions:", validators=[DataRequired()])
    keywords = StringField("Keywords:", validators=[DataRequired()])
    source = StringField("Source:")
    submit = SubmitField("Submit")

    def __init__(self, edit_id=None, **kwargs):
        super().__init__(**kwargs)
        self.edit_id = edit_id  # ID of the

    @property
    def is_edit(self) -> bool:
        """Are we currently editing a recipe?"""
        return self.edit_id is None

    def validate_title(form, field) -> None:
        """Ensure the title does not already exist in the database."""
        existing_recipe = Recipe.query.filter_by(title=field.data).first()
        if existing_recipe:
            if not form.is_edit and form.edit_id != existing_recipe.id:
                # Either we're not editing, or we tried to change the name into
                # something which already exists.
                raise ValidationError("Title exists already.")

    def construct_recipe_kwargs(self, author=True) -> Dict[str, Any]:
        kwargs = dict(
            title=self.title.data,
            ingredients=self.ingredients.data,
            instructions=self.instructions.data,
            keywords=self.keywords.data,
            source=self.source.data,
        )
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
        recipe.last_updated = datetime.utcnow()

    def fill_from_existing_recipe(self, recipe: Recipe):
        """Fill fields from an existing recipe"""
        for field in ("title", "ingredients", "instructions", "keywords", "source"):
            value = getattr(recipe, field)
            getattr(self, field).data = value


class SimpleSearch(FlaskForm):
    search_string = StringField("Search:")
    submit = SubmitField("Submit")
