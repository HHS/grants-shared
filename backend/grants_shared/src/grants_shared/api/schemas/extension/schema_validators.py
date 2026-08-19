import enum
import operator
import typing
from functools import wraps

from marshmallow import ValidationError, validates_schema

from grants_shared.api.schemas.extension.schema_common import MarshmallowErrorContainer
from grants_shared.api.schemas.extension.schema_validation_error import SchemaValidationError


class RelationalValidationOperator(enum.StrEnum):
    """Supported comparisons between two fields in a schema-level validation."""

    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    EQUAL = "equal"
    NOT_EQUAL = "not_equal"


# Keep the public operator values separate from the Python implementation.
# This lets the decorator store stable, serializable operator names as metadata
# while using Python's operator module to perform the actual comparison.
_COMPARISON_OPERATORS: dict[
    RelationalValidationOperator,
    typing.Callable[[typing.Any, typing.Any], bool],
] = {
    RelationalValidationOperator.LESS_THAN: operator.lt,
    RelationalValidationOperator.LESS_THAN_OR_EQUAL: operator.le,
    RelationalValidationOperator.GREATER_THAN: operator.gt,
    RelationalValidationOperator.GREATER_THAN_OR_EQUAL: operator.ge,
    RelationalValidationOperator.EQUAL: operator.eq,
    RelationalValidationOperator.NOT_EQUAL: operator.ne,
}


class RelationalValidationMetadata(typing.TypedDict):
    """Serializable description of a relational validation rule."""

    left_field: str
    operator: str
    right_field: str


class RelationalValidationCallable(typing.Protocol):
    """Callable decorated with relational-validation metadata."""

    __relational_validation__: RelationalValidationMetadata

    def __call__(
        self,
        self_: typing.Any,
        data: dict[str, typing.Any],
        **kwargs: typing.Any,
    ) -> None: ...


def relational_validation(
    *,
    left_field: str,
    operator: RelationalValidationOperator,
    right_field: str,
    message: str,
) -> typing.Callable:
    """Create a Marshmallow schema-level validator comparing two fields.

    Use this when validation depends on the relationship between two values
    rather than on either field independently.

    For example:

        @relational_validation(
            left_field="award_floor",
            operator=RelationalValidationOperator.LESS_THAN_OR_EQUAL,
            right_field="award_ceiling",
            message="Award floor must be less than or equal to award ceiling",
        )
        def validate_award_values(
            self,
            data: dict,
            **kwargs: dict,
        ) -> None:
            pass

    During schema validation, the decorator reads the named values from
    ``data`` and applies the configured comparison. If both values are present
    and the comparison fails, a structured Marshmallow validation error is
    raised.

    If either value is ``None`` or missing, this validator does not perform the
    comparison. Required/null validation remains the responsibility of the
    individual field schemas.

    The decorator also attaches a machine-readable description of the
    relationship to the wrapped function. ``Schema`` collects this metadata
    and it can be exposed through the OpenAPI relational-validation plugin for
    downstream consumers such as generated frontend validation schemas.

    Args:
        left_field: Name of the field on the left side of the comparison.
        operator: Comparison to apply between the two field values.
        right_field: Name of the field on the right side of the comparison.
        message: Backend validation message returned when the relationship is
            invalid.
    """

    def decorator(
        func: typing.Callable[..., None],
    ) -> typing.Callable[..., None]:
        comparison = _COMPARISON_OPERATORS[operator]

        @wraps(func)
        def wrapper(
            self: typing.Any,
            data: dict[str, typing.Any],
            **kwargs: typing.Any,
        ) -> None:
            left_value = data.get(left_field)
            right_value = data.get(right_field)

            # Only compare values when both sides are present. Field-level
            # required/null/type validators should report those failures
            # instead of producing a secondary relational error.
            if (
                left_value is not None
                and right_value is not None
                and not comparison(left_value, right_value)
            ):
                raise ValidationError(
                    [
                        MarshmallowErrorContainer(
                            SchemaValidationError.INVALID,
                            message,
                        )
                    ]
                )

            # Preserve any additional behavior defined in the decorated
            # schema-validation method.
            func(self, data, **kwargs)

        # Store only the information needed to describe the relationship.
        # Types and presentation-specific validation details can be inferred
        # by downstream consumers from the fields' OpenAPI definitions.
        metadata: RelationalValidationMetadata = {
            "left_field": left_field,
            "operator": operator.value,
            "right_field": right_field,
        }

        # functools.wraps preserves the function's callable type, but MyPy
        # does not know about the metadata attribute we intentionally attach.
        typed_wrapper = typing.cast(RelationalValidationCallable, wrapper)
        typed_wrapper.__relational_validation__ = metadata

        # Register the wrapped function as a normal Marshmallow schema-level
        # validator after adding the relational behavior and metadata.
        return validates_schema(typed_wrapper)

    return decorator
