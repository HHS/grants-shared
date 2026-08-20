import pytest
from marshmallow import ValidationError

from grants_shared.api.schemas.extension import fields
from grants_shared.api.schemas.extension.schema import Schema
from grants_shared.api.schemas.extension.schema_validation_error import SchemaValidationError
from grants_shared.api.schemas.extension.schema_validators import (
    RelationalValidationOperator,
    relational_validation,
)


class RelationalSchema(Schema):
    left = fields.Integer(allow_none=True)
    right = fields.Integer(allow_none=True)

    @relational_validation(
        left_field="left",
        operator=RelationalValidationOperator.LESS_THAN_OR_EQUAL,
        right_field="right",
    )
    def validate_relationship(self, data: dict, **kwargs: dict) -> None:
        pass


@pytest.mark.parametrize(
    "operator,left,right,is_valid",
    [
        (RelationalValidationOperator.LESS_THAN, 1, 2, True),
        (RelationalValidationOperator.LESS_THAN, 2, 1, False),
        (RelationalValidationOperator.LESS_THAN_OR_EQUAL, 1, 1, True),
        (RelationalValidationOperator.LESS_THAN_OR_EQUAL, 2, 1, False),
        (RelationalValidationOperator.GREATER_THAN, 2, 1, True),
        (RelationalValidationOperator.GREATER_THAN, 1, 2, False),
        (RelationalValidationOperator.GREATER_THAN_OR_EQUAL, 1, 1, True),
        (RelationalValidationOperator.GREATER_THAN_OR_EQUAL, 1, 2, False),
        (RelationalValidationOperator.EQUAL, 1, 1, True),
        (RelationalValidationOperator.EQUAL, 1, 2, False),
        (RelationalValidationOperator.NOT_EQUAL, 1, 2, True),
        (RelationalValidationOperator.NOT_EQUAL, 1, 1, False),
    ],
)
def test_relational_validation_operator(
    operator: RelationalValidationOperator,
    left: int,
    right: int,
    is_valid: bool,
):
    class TestableSchema(Schema):
        left = fields.Integer()
        right = fields.Integer()

        @relational_validation(
            left_field="left",
            operator=operator,
            right_field="right",
        )
        def validate_relationship(self, data: dict, **kwargs: dict) -> None:
            pass

    schema = TestableSchema()

    if is_valid:
        result = schema.load({"left": left, "right": right})

        assert result == {
            "left": left,
            "right": right,
        }
    else:
        expected_message = (
            f"Relational validation failed: left "
            f"must be {operator.value.replace('_', ' ')} right"
        )

        with pytest.raises(
            ValidationError,
            match=expected_message,
        ):
            schema.load({"left": left, "right": right})


def test_relational_validation_uses_invalid_comparison_error():
    schema = RelationalSchema()

    with pytest.raises(ValidationError) as exc_info:
        schema.load(
            {
                "left": 10,
                "right": 5,
            }
        )

    errors = exc_info.value.messages
    error = errors["_schema"][0]

    assert error.key == SchemaValidationError.INVALID_COMPARISON
    assert error.message == "Relational validation failed: left must be less than or equal right"


def test_relational_validation_skips_when_left_is_none():
    schema = RelationalSchema()

    result = schema.load(
        {
            "left": None,
            "right": 10,
        }
    )

    assert result == {
        "left": None,
        "right": 10,
    }


def test_relational_validation_skips_when_right_is_none():
    schema = RelationalSchema()

    result = schema.load(
        {
            "left": 10,
            "right": None,
        }
    )

    assert result == {
        "left": 10,
        "right": None,
    }


def test_relational_validation_attaches_metadata():
    validate_method = RelationalSchema.validate_relationship

    assert validate_method.__relational_validation__ == {
        "left_field": "left",
        "operator": "less_than_or_equal",
        "right_field": "right",
    }


def test_relational_validation_calls_wrapped_function():
    calls = []

    class TestableSchema(Schema):
        left = fields.Integer()
        right = fields.Integer()

        @relational_validation(
            left_field="left",
            operator=RelationalValidationOperator.LESS_THAN_OR_EQUAL,
            right_field="right",
        )
        def validate_relationship(self, data: dict, **kwargs: dict) -> None:
            calls.append(data)

    schema = TestableSchema()

    schema.load(
        {
            "left": 1,
            "right": 2,
        }
    )

    assert calls == [
        {
            "left": 1,
            "right": 2,
        }
    ]


def test_field_rejects_non_callable_openapi_metadata():
    class BadValidator:
        get_openapi_metadata = "not-callable"

        def __call__(self, value):
            return value

    with pytest.raises(
        TypeError,
        match="get_openapi_metadata must be callable",
    ):
        fields.String(validate=BadValidator())


def test_field_rejects_non_dict_openapi_metadata():
    class BadValidator:
        def get_openapi_metadata(self):
            return "not-a-dict"

        def __call__(self, value):
            return value

    with pytest.raises(
        TypeError,
        match="get_openapi_metadata must return a dict",
    ):
        fields.String(validate=BadValidator())
