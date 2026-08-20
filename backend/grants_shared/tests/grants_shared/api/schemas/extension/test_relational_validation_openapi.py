from grants_shared.api.schemas.extension import fields
from grants_shared.api.schemas.extension.relational_validation_openapi import (
    RelationalValidationOpenAPIPlugin,
)
from grants_shared.api.schemas.extension.schema import Schema
from grants_shared.api.schemas.extension.schema_validators import (
    RelationalValidationOperator,
    relational_validation,
)


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


def test_relational_validation_openapi_plugin():
    result = RelationalValidationOpenAPIPlugin().schema_helper(
        "RelationalSchema",
        {},
        schema=RelationalSchema(),
    )

    assert result == {
        "x-relational-validations": [
            {
                "left_field": "minimum",
                "operator": "less_than_or_equal",
                "right_field": "maximum",
            }
        ]
    }


def test_relational_validation_openapi_plugin_ignores_non_shared_schema():
    result = RelationalValidationOpenAPIPlugin().schema_helper(
        "SomethingElse",
        {},
        schema=object(),
    )

    assert result is None


def test_relational_validation_openapi_plugin_ignores_schema_without_validations():
    class TestSchemaWithoutValidations(Schema):
        value = fields.String()

    result = RelationalValidationOpenAPIPlugin().schema_helper(
        "TestSchemaWithoutValidations",
        {},
        schema=TestSchemaWithoutValidations(),
    )

    assert result is None


def test_relational_validation_openapi_plugin_accepts_schema_class():
    result = RelationalValidationOpenAPIPlugin().schema_helper(
        "RelationalSchema",
        {},
        schema=RelationalSchema,
    )

    assert result == {
        "x-relational-validations": [
            {
                "left_field": "minimum",
                "operator": "less_than_or_equal",
                "right_field": "maximum",
            }
        ]
    }
