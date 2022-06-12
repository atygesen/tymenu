from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

# from flask_login import current_user
from .blueprint import auth_blueprint as auth
from tymenu.resources import get_db
from tymenu.models import User
from tymenu.email import send_email
from tymenu.log import log_info
from . import forms

#
# forms import LoginForm, RegistrationForm, ChangePasswordForm, PasswordResetRequestForm


# @auth.before_app_request
# def before_request():
#     if (
#         current_user.is_authenticated
#         and not current_user.confirmed
#         and request.endpoint
#         and request.blueprint != "auth"
#         and request.endpoint != "static"
#     ):
#         return redirect(url_for("auth.unconfirmed"))


# @auth.route("/unconfirmed")
# def unconfirmed():
#     if current_user.is_anonymous or current_user.confirmed:
#         return redirect(url_for("main.index"))
#     return render_template("auth/unconfirmed.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if not current_user.is_anonymous:
        # No login page for logged in users
        return redirect(url_for("main.index"))
    form = forms.LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            log_info("Logged in user %s", user.username)
            next = request.args.get("next")
            if next is None or not next.startswith("/"):
                next = url_for("main.index")
            return redirect(next)
        flash("Invalid email or password.")
    return render_template("auth/login.html", form=form)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("main.index"))


@auth.route("/register", methods=["GET", "POST"])
def register():
    form = forms.RegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data.lower(), username=form.username.data, password=form.password.data
        )
        db = get_db()
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


# @auth.route("/confirm/<token>")
# @login_required
# def confirm(token):
#     if current_user.confirmed:
#         return redirect(url_for("main.index"))
#     if current_user.confirm(token):
#         db.session.commit()
#         flash("You have confirmed your account. Thanks!")
#     else:
#         flash("The confirmation link is invalid or has expired.")
#     return redirect(url_for("main.index"))


@auth.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = forms.ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            db = get_db()
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()
            flash("Your password has been updated.")
            return redirect(url_for("main.index"))
        else:
            flash("The old password is incorrect.")
    return render_template("auth/change_password.html", form=form)


@auth.route("/reset", methods=["GET", "POST"])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for("main.index"))
    form = forms.PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            token = user.generate_reset_token()
            send_email(
                user.email,
                "Reset Your TyMenu Password",
                "auth/email/reset_password",
                user=user,
                token=token,
            )
        flash("An email with instructions to reset your password has been sent to you.")
        return redirect(url_for("auth.login"))
    return render_template("auth/reset_password.html", form=form)


@auth.route("/reset/<token>", methods=["GET", "POST"])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for("main.index"))
    form = forms.PasswordResetForm()
    if form.validate_on_submit():
        if User.reset_password(token, form.password.data):
            db = get_db()
            db.session.commit()
            flash("Your password has been updated.")
            return redirect(url_for("auth.login"))
        else:
            return redirect(url_for("main.index"))
    return render_template("auth/reset_password.html", form=form)


# @auth.route("/change_email", methods=["GET", "POST"])
# @login_required
# def change_email_request():
#     form = ChangeEmailForm()
#     if form.validate_on_submit():
#         if current_user.verify_password(form.password.data):
#             new_email = form.email.data.lower()
#             token = current_user.generate_email_change_token(new_email)
#             send_email(
#                 new_email,
#                 "Confirm your email address",
#                 "auth/email/change_email",
#                 user=current_user,
#                 token=token,
#             )
#             flash(
#                 "An email with instructions to confirm your new email "
#                 "address has been sent to you."
#             )
#             return redirect(url_for("main.index"))
#         else:
#             flash("Invalid email or password.")
#     return render_template("auth/change_email.html", form=form)


# @auth.route("/change_email/<token>")
# @login_required
# def change_email(token):
#     if current_user.change_email(token):
#         db.session.commit()
#         flash("Your email address has been updated.")
#     else:
#         flash("Invalid request.")
#     return redirect(url_for("main.index"))
