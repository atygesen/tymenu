import os
from flask_migrate import Migrate
from tymenu.factory import create_app
from tymenu.plugins import get_db

db = get_db()

app = create_app(os.getenv("FLASK_CONFIG") or "default")
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return dict(db=db)
