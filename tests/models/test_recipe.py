import datetime
import pytest
from sqlalchemy import or_
from tymenu.models import Recipe


@pytest.fixture
def make_recipe(john, commit_to_db):
    def _make_recipe(author=None, **kwargs):
        author = author or john
        recipe = Recipe(author=author, **kwargs)
        commit_to_db(recipe)
        return recipe

    return _make_recipe


@pytest.fixture
def meatballs(make_recipe):
    return make_recipe(
        title="meatballs",
        ingredients="Lots of meatballs\nTomato Sauce",
    )


@pytest.fixture
def spaghetti(make_recipe):
    return make_recipe(
        title="spaghetti",
        ingredients="Pasta (spaghetti)\nminced meat\nTomato Sauce",
    )


def test_recipe(meatballs):
    assert meatballs.title == "meatballs"
    assert meatballs.author.username == "john"
    assert isinstance(meatballs.timestamp, datetime.datetime)


def test_search_ingredients(meatballs, spaghetti):
    # Case sensitive?
    result = Recipe.search_ingredients("MeatBalls").all()
    assert len(result) == 1
    assert result[0] is meatballs

    # Missing plural s
    result = Recipe.search_ingredients("meatball").all()
    assert result[0] is meatballs

    # A 3rd ingredient, which is shared
    result = Recipe.search_ingredients("tomato").all()
    assert len(result) == 2
    assert spaghetti in result
    assert meatballs in result

    # No carrots, so nothing which contains everything
    result = Recipe.search_ingredients("meatballs", "carrot").all()
    assert len(result) == 0

    # Either meatballs or carrots
    result = Recipe.search_ingredients("meatballs", "carrot", operation="or").all()
    assert len(result) == 1
    assert result[0] is meatballs

    # Find either meatballs or spaghetti
    result = Recipe.search_ingredients("meatballs", "spaghetti", operation="or").all()
    assert len(result) == 2

    # Find either meatballs or spaghetti, using explicit or_ function
    result = Recipe.search_ingredients("meatballs", "spaghetti", operation=or_).all()
    assert len(result) == 2

    # Exclude meatballs
    result = Recipe.search_ingredients("meatballs", exclude=True).all()
    assert len(result) == 1
    assert meatballs not in result
    assert result[0] == spaghetti
