import os
import logging
from sqlalchemy import text
from flask_migrate import Migrate
from tymenu.factory import create_app
from tymenu.resources import get_db
from tymenu.models import Role

logger = logging.getLogger(__name__)

db = get_db()

app = create_app(os.getenv("FLASK_CONFIG") or "default")
migrate = Migrate(app, db)


def init_db():
    db.create_all()
    Role.insert_roles()


def check_tables():
    db.session.execute(text(f"SELECT * from {Role.__tablename__}")).fetchall()


with app.app_context():
    print("Testing if tables exist...")
    try:
        # In case the tables havn't been created yet.
        # Else, assume the tables are OK.
        check_tables()
    except Exception as e:
        print("Exception:", e)
        print("Initializing DB...")
        init_db()
        print("DB initialized.")


@app.shell_context_processor
def make_shell_context():
    return dict(db=db)
