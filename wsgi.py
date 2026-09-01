"""Entry point for production servers (gunicorn, Render, etc).

Local dev:   python wsgi.py
Production:  gunicorn wsgi:app   OR   gunicorn app:app  (both work)
"""
from app import app

if __name__ == "__main__":
    app.run(debug=True)
