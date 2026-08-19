import pytest
from marshmallow import ValidationError

from grants_shared.api.schemas.extension import validators
from grants_shared.api.schemas.extension.schema_validation_error import SchemaValidationError


def get_error_container(error: ValidationError):
    assert isinstance(error.messages, list)
    assert len(error.messages) == 1
    return error.messages[0]


def test_regexp_accepts_matching_value():
    validator = validators.Regexp(r"^abc$")

    assert validator("abc") == "abc"


def test_regexp_rejects_non_matching_value():
    validator = validators.Regexp(
        r"^abc$",
        error_message="Must match abc.",
    )

    with pytest.raises(ValidationError) as exc_info:
        validator("def")

    error = get_error_container(exc_info.value)
    assert error.key == SchemaValidationError.FORMAT
    assert error.message == "Must match abc."


@pytest.mark.parametrize(
    "validator,value",
    [
        (validators.Length(min=2), "ab"),
        (validators.Length(max=2), "ab"),
        (validators.Length(min=2, max=4), "abc"),
        (validators.Length(equal=3), "abc"),
    ],
)
def test_length_accepts_valid_values(validator, value):
    assert validator(value) == value


@pytest.mark.parametrize(
    "validator,value,error_type",
    [
        (
            validators.Length(min=2),
            "a",
            SchemaValidationError.MIN_LENGTH,
        ),
        (
            validators.Length(max=2),
            "abc",
            SchemaValidationError.MAX_LENGTH,
        ),
        (
            validators.Length(min=2, max=4),
            "a",
            SchemaValidationError.MIN_OR_MAX_LENGTH,
        ),
        (
            validators.Length(min=2, max=4),
            "abcde",
            SchemaValidationError.MIN_OR_MAX_LENGTH,
        ),
        (
            validators.Length(equal=3),
            "ab",
            SchemaValidationError.EQUALS,
        ),
    ],
)
def test_length_rejects_invalid_values(
    validator,
    value,
    error_type,
):
    with pytest.raises(ValidationError) as exc_info:
        validator(value)

    error = get_error_container(exc_info.value)
    assert error.key == error_type


@pytest.mark.parametrize(
    "validator,value",
    [
        (validators.WordLimit(min=2), "one two"),
        (validators.WordLimit(max=2), "one two"),
        (validators.WordLimit(min=2, max=4), "one two three"),
        (validators.WordLimit(equal=3), "one two three"),
    ],
)
def test_word_limit_accepts_valid_values(validator, value):
    assert validator(value) == value


@pytest.mark.parametrize(
    "validator,value,error_type",
    [
        (
            validators.WordLimit(min=2),
            "one",
            SchemaValidationError.MIN_WORDS,
        ),
        (
            validators.WordLimit(max=2),
            "one two three",
            SchemaValidationError.MAX_WORDS,
        ),
        (
            validators.WordLimit(min=2, max=4),
            "one",
            SchemaValidationError.MIN_OR_MAX_WORDS,
        ),
        (
            validators.WordLimit(min=2, max=4),
            "one two three four five",
            SchemaValidationError.MIN_OR_MAX_WORDS,
        ),
        (
            validators.WordLimit(equal=3),
            "one two",
            SchemaValidationError.EQUALS_WORDS,
        ),
    ],
)
def test_word_limit_rejects_invalid_values(
    validator,
    value,
    error_type,
):
    with pytest.raises(ValidationError) as exc_info:
        validator(value)

    error = get_error_container(exc_info.value)
    assert error.key == error_type


def test_email_accepts_valid_email():
    validator = validators.Email()

    assert validator("test@example.com") == "test@example.com"


def test_email_rejects_invalid_email():
    validator = validators.Email()

    with pytest.raises(ValidationError) as exc_info:
        validator("not-an-email")

    error = get_error_container(exc_info.value)
    assert error.key == SchemaValidationError.FORMAT
    assert error.message == "Not a valid email address."


def test_email_exposes_openapi_metadata():
    validator = validators.Email()

    assert validator.get_openapi_metadata() == {
        "format": "email",
    }


def test_url_accepts_valid_url():
    validator = validators.URL()

    assert validator("https://example.com") == "https://example.com"


def test_url_rejects_invalid_url():
    validator = validators.URL()

    with pytest.raises(ValidationError) as exc_info:
        validator("not-a-url")

    error = get_error_container(exc_info.value)
    assert error.key == SchemaValidationError.INVALID
    assert error.message == "Not a valid URL."


def test_one_of_accepts_valid_choice():
    validator = validators.OneOf(["a", "b", "c"])

    assert validator("b") == "b"


def test_one_of_rejects_invalid_choice():
    validator = validators.OneOf(["a", "b", "c"])

    with pytest.raises(ValidationError) as exc_info:
        validator("d")

    error = get_error_container(exc_info.value)
    assert error.key == SchemaValidationError.INVALID_CHOICE
    assert "a" in error.message
    assert "b" in error.message
    assert "c" in error.message


@pytest.mark.parametrize(
    "validator,value",
    [
        (validators.Range(min=1), 1),
        (validators.Range(max=10), 10),
        (validators.Range(min=1, max=10), 5),
    ],
)
def test_range_accepts_valid_values(validator, value):
    assert validator(value) == value


@pytest.mark.parametrize(
    "validator,value,error_type",
    [
        (
            validators.Range(min=1),
            0,
            SchemaValidationError.MIN_VALUE,
        ),
        (
            validators.Range(max=10),
            11,
            SchemaValidationError.MAX_VALUE,
        ),
        (
            validators.Range(min=1, max=10),
            0,
            SchemaValidationError.MIN_OR_MAX_VALUE,
        ),
        (
            validators.Range(min=1, max=10),
            11,
            SchemaValidationError.MIN_OR_MAX_VALUE,
        ),
    ],
)
def test_range_rejects_invalid_values(
    validator,
    value,
    error_type,
):
    with pytest.raises(ValidationError) as exc_info:
        validator(value)

    error = get_error_container(exc_info.value)
    assert error.key == error_type
