# init_db.py
from app import app, db, criar_admin

with app.app_context():
    db.create_all()
    criar_admin()