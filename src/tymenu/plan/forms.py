from datetime import datetime
from flask_wtf import FlaskForm
from flask_pagedown.fields import PageDownField
from wtforms.fields import DateField, SubmitField, SelectField, StringField, IntegerField
from wtforms.validators import DataRequired, InputRequired

from tymenu.utils import label_is_required


class PlanDate(FlaskForm):
    entrydate = DateField(
        "Date:", format="%Y-%m-%d", default=datetime.today, validators=[DataRequired()]
    )
    first_day = SelectField(
        label="First day:", choices=["Monday", "Selected"], validators=[DataRequired()]
    )
    author = SelectField(label="Added by:", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Submit")


class RecipeMenuPlanForm(FlaskForm):
    recipe_id = IntegerField("Recipe ID:", validators=[DataRequired()])
    day = IntegerField("Day:", validators=[InputRequired("Enter day number.")], default=0)
    days_leftover = IntegerField(
        "Days leftovers:", validators=[InputRequired("Enter number of leftovers!")], default=0
    )

    submit = SubmitField("Submit")
    cancel = SubmitField(label="Cancel", render_kw={"formnovalidate": True})


class NewMenuPlanForm(FlaskForm):
    title = StringField(label_is_required("Title:"), validators=[DataRequired()])
    description = PageDownField("Description:")

    submit = SubmitField("Submit")
    cancel = SubmitField(label="Cancel", render_kw={"formnovalidate": True})
