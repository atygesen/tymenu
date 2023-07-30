from __future__ import annotations

from threading import Thread

from flask import current_app, render_template
from flask_mail import Message

from tymenu.resources import get_mail


def send_async_email(app, msg):
    with app.app_context():
        mail = get_mail()
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    config = app.config
    msg = Message(
        f"{config['TYMENU_MAIL_SUBJECT_PREFIX']} {subject}",
        sender=config["TYMENU_MAIL_SENDER"],
        recipients=[to],
    )
    msg.body = render_template(f"{template}.txt", **kwargs)
    msg.html = render_template(f"{template}.html", **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr
