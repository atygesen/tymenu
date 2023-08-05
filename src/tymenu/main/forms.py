from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length


class ChangeUsernameForm(FlaskForm):
    username = StringField("New Username", validators=[DataRequired(), Length(1, 64)])
    submit = SubmitField("Update Username")
    cancel = SubmitField(label="Cancel", render_kw={"formnovalidate": True})
