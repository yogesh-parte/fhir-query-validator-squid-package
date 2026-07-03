from src.agentic_layer.utils.query_parser import parse_query_url


def test_parse_simple_query():
    parsed = parse_query_url("Patient?gender=male")
    assert parsed.resource_type == "Patient"
    assert parsed.params[0].name == "gender"
    assert parsed.params[0].value == "male"


def test_parse_modifier_and_comparator():
    parsed = parse_query_url("Observation?date:missing=true&value=gt5")
    assert parsed.params[0].modifier == "missing"
    assert parsed.params[1].name == "value"
    assert parsed.params[1].comparator == "gt"
    assert parsed.params[1].value == "5"


def test_parse_absolute_fhir_url():
    parsed = parse_query_url("https://hapi.fhir.org/baseR4/Patient?gender=male")
    assert parsed.resource_type == "Patient"
    assert parsed.params[0].name == "gender"


def test_parse_resource_without_query_string():
    parsed = parse_query_url("Patient")
    assert parsed.resource_type == "Patient"
    assert parsed.params == []


def test_parse_chained_parameter():
    parsed = parse_query_url("Patient?subject.name=Smith")
    assert parsed.params[0].name == "subject.name"
    assert parsed.params[0].chained is True
    assert parsed.params[0].value == "Smith"