import os
from tymenu.models import Role
from tymenu.factory import create_app
from tymenu.resources import get_db

if __name__ == "__main__":
    # Helper script to remake the database.
    # WARNING: THIS WILL NUKE EVERYTHING
    ans = input("Remake DB? (y/n): ")
    if ans.lower() != "y":
        print("Exiting.")
        exit(0)
    print("Remaking database...")
    app = create_app(os.getenv("FLASK_CONFIG") or "default")
    db = get_db()

    with app.app_context():
        print("Droping tables...")
        db.drop_all()
        print("Creating tables...")
        db.create_all()
        print("Finalizing...")
        Role.insert_roles()

    print("Done!")
