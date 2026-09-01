"""Entry point for production servers (gunicorn, Render, etc).

Local dev:   python wsgi.py
Production:  gunicorn wsgi:app
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
