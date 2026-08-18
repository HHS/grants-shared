import enum
import operator
import typing
from functools import wraps

from marshmallow import ValidationError, validates_schema

from grants_shared.api.schemas.extension.schema_common import MarshmallowErrorContainer
from grants_shared.api.schemas.extension.schema_validation_error import SchemaValidationError


class RelationalValidationOperator(enum.StrEnum):
    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    EQUAL = "equal"
    NOT_EQUAL = "not_equal"


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
    left_field: str
    operator: str
    right_field: str


class RelationalValidationCallable(typing.Protocol):
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

            func(self, data, **kwargs)

        metadata: RelationalValidationMetadata = {
            "left_field": left_field,
            "operator": operator.value,
            "right_field": right_field,
        }

        typed_wrapper = typing.cast(RelationalValidationCallable, wrapper)
        typed_wrapper.__relational_validation__ = metadata

        return validates_schema(typed_wrapper)

    return decorator
