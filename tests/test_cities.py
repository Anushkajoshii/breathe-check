import pytest

from breathe_check.cities import CITIES, DEFAULT_CITY, cities_with_role, get_city


def test_default_city_is_indore():
    assert get_city(DEFAULT_CITY).name == "Indore"


def test_lookup_is_case_insensitive():
    assert get_city("DELHI").slug == "delhi"


def test_unknown_city_gives_helpful_error():
    with pytest.raises(KeyError, match="Known cities"):
        get_city("atlantis")


def test_slugs_are_unique():
    slugs = [c.slug for c in CITIES]
    assert len(slugs) == len(set(slugs))


def test_every_city_is_inside_india():
    for c in CITIES:
        assert 6 < c.lat < 37 and 68 < c.lon < 98, c.slug


def test_we_have_both_treated_and_control_cities():
    assert len(cities_with_role("grap")) >= 3
    assert len(cities_with_role("control")) >= 3
