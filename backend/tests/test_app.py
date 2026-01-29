from fastapi import FastAPI

from main import app


def test_app_initializes():
    assert isinstance(app, FastAPI)
    assert app.title == "AlphaLens API"
