from flask import render_template
from . import main_blueprint as main


@main.route("/")
def index():
    return render_template("index.html")
