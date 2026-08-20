import pytest
from marshmallow import ValidationError

from grants_shared.api.schemas.extension import fields
from grants_shared.api.schemas.extension.schema import Schema
from grants_shared.api.schemas.extension.schema_common import MarshmallowErrorContainer
from grants_shared.api.schemas.extension.schema_validation_error import SchemaValidationError
from grants_shared.api.schemas.extension.schema_validators import (
    RelationalValidationOperator,
    relational_validation,
)


class ChildSchema(Schema):
    value = fields.String()


class RelationalSchema(Schema):
    minimum = fields.Integer()
    maximum = fields.Integer()

    @relational_validation(
        left_field="minimum",
        operator=RelationalValidationOperator.LESS_THAN_OR_EQUAL,
        right_field="maximum",
    )
    def validate_range(self, data: dict, **kwargs: dict) -> None:
        pass


def test_schema_collects_relational_validations():
    schema = RelationalSchema()

    assert schema.relational_validations == [
        {
            "left_field": "minimum",
            "operator": "less_than_or_equal",
            "right_field": "maximum",
        }
    ]


def test_schema_without_relational_validations_has_empty_list():
    class PlainSchema(Schema):
        value = fields.String()

    schema = PlainSchema()

    assert schema.relational_validations == []


def test_schema_excludes_unknown_fields():
    class ExampleSchema(Schema):
        known = fields.String()

    result = ExampleSchema().load(
        {
            "known": "value",
            "unknown": "ignored",
        }
    )

    assert result == {
        "known": "value",
    }


def test_schema_partial_propagates_to_nested_schema():
    class ParentSchema(Schema):
        child = fields.Nested(ChildSchema)

    schema = ParentSchema(partial=True)

    child_field = schema.declared_fields["child"]

    assert child_field.nested.partial is True


def test_schema_partial_propagates_to_nested_schema_in_list():
    class ParentSchema(Schema):
        children = fields.List(fields.Nested(ChildSchema))

    schema = ParentSchema(partial=True)

    children_field = schema.declared_fields["children"]

    assert children_field.inner.nested.partial is True


def test_schema_type_error_uses_structured_error():
    class ExampleSchema(Schema):
        value = fields.String()

    with pytest.raises(ValidationError) as exc_info:
        ExampleSchema().load("not-an-object")

    errors = exc_info.value.messages

    assert "_schema" in errors
    assert len(errors["_schema"]) == 1

    error = errors["_schema"][0]

    assert isinstance(error, MarshmallowErrorContainer)
    assert error.key == SchemaValidationError.INVALID
    assert error.message == "Invalid input type."