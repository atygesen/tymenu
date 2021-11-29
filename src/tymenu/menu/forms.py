from flask_wtf import FlaskForm
from tymenu.models import Recipe
from wtforms import TextAreaField, SubmitField, StringField
from wtforms.validators import DataRequired, ValidationError


class PostRecipe(FlaskForm):
    title = StringField("Title:", validators=[DataRequired()])
    ingredients = TextAreaField("Ingredients:", validators=[DataRequired()])
    keywords = StringField("Keywords:", validators=[DataRequired()])
    submit = SubmitField("Submit")

    def validate_title(form, field):
        """Ensure the title does not already exist in the database"""
        if Recipe.query.filter_by(title=field.data).first():
            raise ValidationError("Title exists already.")


class SearchRecipes(FlaskForm):
    title = StringField("Title:")
    ingredients = TextAreaField("Ingredients:")
    keywords = StringField("Keywords:")
    submit = SubmitField("Submit")
