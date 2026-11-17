import pytest

from parse_utils import JsonParser

DATA = {
    "name": "Yogendra",
    "address": {"country": "Nepal", "city": "Pokhara"},
    "count": 0,
    "active": False,
    "tags": [],
    "nothing": None,
    "response": [{"fName": "Yogendra"}, {"fName": "Second"}],
}


@pytest.fixture
def parser():
    return JsonParser(DATA)


@pytest.mark.parametrize(
    ("spec", "expected"),
    [
        ("name", "Yogendra"),
        (["name"], "Yogendra"),
        (["address", "city"], "Pokhara"),
        (("address", "city"), "Pokhara"),
        (["response", 0, "fName"], "Yogendra"),
        (["response", -1, "fName"], "Second"),
        ([["missing"], ["address", "country"]], "Nepal"),
        ([["nothing"], ["name"]], "Yogendra"),
    ],
)
def test_paths(parser, spec, expected):
    assert parser.extract_dict({"v": spec}) == {"v": expected}


@pytest.mark.parametrize("key", ["count", "active", "tags"])
def test_falsy_values_are_kept(parser, key):
    assert parser.extract_dict({"v": key}) == {"v": DATA[key]}


@pytest.mark.parametrize(
    "spec",
    [
        ["missing"],
        ["nothing"],
        ["response", 5, "fName"],  # index out of range
        ["name", "x"],  # walking into a scalar
        ["response", "fName"],  # string key on a list
        ["address", 0],  # int index on a dict
    ],
)
def test_unresolvable_paths_are_omitted(parser, spec):
    assert parser.extract_dict({"v": spec}) == {}


@pytest.mark.parametrize("spec", [[], 5, [["a"], "b"], [True], [["a"], []]])
def test_invalid_specs(parser, spec):
    with pytest.raises(ValueError):
        parser.extract_dict({"v": spec})


def test_seed_item_and_from_string():
    parser = JsonParser.from_string('{"a": {"b": 1}}')
    seed = {"x": 1}
    assert parser.extract_dict({"b": ["a", "b"]}, item=seed) == {"x": 1, "b": 1}
    assert seed == {"x": 1}
