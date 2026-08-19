import inspect

import pytest
from marshmallow import ValidationError

from grants_shared.api.schemas.extension import fields, validators
from tests.grants_shared.api.schemas.schema_validation_utils import (
    DummySchema,
    EnumA,
    EnumB,
    FieldTestSchema,
    get_expected_validation_errors,
    get_invalid_field_test_schema_req,
    get_valid_field_test_schema_req,
    validate_errors,
)


def test_enum_field():
    schema = DummySchema()

    both_ab_field = schema.declared_fields["both_ab"]

    # Make sure the multi enum can deserialize to both enums and reserialize to a string
    for e in EnumA:
        deserialized_value = both_ab_field._deserialize(str(e), None, None)
        assert deserialized_value == e
        assert isinstance(deserialized_value, EnumA)

        serialized_value = both_ab_field._serialize(e, None, None)
        assert isinstance(serialized_value, str)
    for e in EnumB:
        deserialized_value = both_ab_field._deserialize(str(e), None, None)
        assert deserialized_value == e
        assert isinstance(deserialized_value, EnumB)

        serialized_value = both_ab_field._serialize(e, None, None)
        assert isinstance(serialized_value, str)

    with pytest.raises(
        ValidationError, match="Must be one of: value1, value2, value3, value4, value5, value6."
    ):
        both_ab_field._deserialize("not_a_value", None, None)

    with pytest.raises(
        ValidationError, match="Must be one of: value1, value2, value3, value4, value5, value6."
    ):
        both_ab_field._deserialize({}, None, None)


def test_enum_field_converts_enum_load_default_to_openapi_value():
    field = fields.Enum(
        EnumA,
        load_default=EnumA.VALUE1,
    )

    assert field.load_default == EnumA.VALUE1
    assert field.metadata["default"] == EnumA.VALUE1.value


def test_field_converts_enum_example_to_openapi_value():
    field = fields.String(
        metadata={
            "example": EnumA.VALUE1,
        }
    )

    assert field.metadata["example"] == EnumA.VALUE1.value


def test_field_converts_enum_list_example_to_openapi_values():
    field = fields.String(
        metadata={
            "example": [
                EnumA.VALUE1,
                EnumA.VALUE2,
                "not-an-enum",
            ],
        }
    )

    assert field.metadata["example"] == [
        EnumA.VALUE1.value,
        EnumA.VALUE2.value,
        "not-an-enum",
    ]


def test_field_applies_validator_openapi_metadata():
    field = fields.String(
        validate=validators.Email(),
    )

    assert field.metadata["format"] == "email"


def test_field_without_openapi_validator_metadata_does_not_set_format():
    field = fields.String(
        validate=validators.Length(max=100),
    )

    assert "format" not in field.metadata


def test_field_applies_custom_validator_openapi_metadata():
    class TestValidator(validators.Validator):
        def __call__(self, value):
            return value

        def get_openapi_metadata(self):
            return {
                "format": "test-format",
                "x-test": True,
            }

    field = fields.String(
        validate=TestValidator(),
    )

    assert field.metadata["format"] == "test-format"
    assert field.metadata["x-test"] is True


@pytest.mark.parametrize(
    "payload,expected_errors",
    [(get_invalid_field_test_schema_req(), get_expected_validation_errors())],
)
def test_fields(payload, expected_errors):
    errors = FieldTestSchema().validate(payload)
    validate_errors(errors, expected_errors)


def test_fields_ignore_unknowns():
    unknown_key = "UNKNOWN"
    payload = {**get_valid_field_test_schema_req(), unknown_key: "EXCLUDED"}
    result = FieldTestSchema().load(payload)
    assert unknown_key not in result


def test_fields_configured_properly():
    """
    This is a sanity-test to verify we have properly
    overriden and defined all the default error codes
    that Marshmallow uses.

    If you see this test failing after updating our
    dependency on Marshmallow, likely just need to add
    a configuration to the relevant class' "error_mapping" object
    """
    relevant_classes = []
    for _, obj in inspect.getmembers(fields):
        if inspect.isclass(obj) and issubclass(obj, fields.MixinField):
            relevant_classes.append(obj)

    for relevant_class in relevant_classes:
        if relevant_class == fields.Enum:
            # We don't derive from the original and made a custom enum field
            # so the default error messages aren't relevant
            assert relevant_class.error_mapping.keys() == {"unknown"}
            continue

        # We want to make sure all keys are configured, but we also may have more
        required_error_message_keys = relevant_class.default_error_messages.keys()
        configured_error_message_keys = relevant_class.error_mapping.keys()
        assert configured_error_message_keys >= required_error_message_keys
