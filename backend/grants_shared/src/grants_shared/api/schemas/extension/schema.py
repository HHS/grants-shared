from typing import Any, cast

import apiflask
from marshmallow import EXCLUDE

from grants_shared.api.schemas.extension.schema_common import MarshmallowErrorContainer
from grants_shared.api.schemas.extension.schema_validation_error import SchemaValidationError
from grants_shared.api.schemas.extension.schema_validators import RelationalValidationMetadata


class Schema(apiflask.Schema):  # noqa: TID251
    # There's no clean way to override the error messages at the schema-level
    # as they get stored directly into the internal error store of the Schema object
    #
    # This approach is a little hacky, but we just change the default error messages to
    # return the error container objects directly to work around that
    _default_error_messages = cast(
        dict[str, str],
        {
            "type": MarshmallowErrorContainer(
                key=SchemaValidationError.INVALID,
                message="Invalid input type.",
            ),
            "unknown": MarshmallowErrorContainer(
                key=SchemaValidationError.UNKNOWN,
                message="Unknown field.",
            ),
        },
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.relational_validations = self._get_relational_validations()

        # In order for the OpenAPI docs to display correctly
        # we need to set sub-schemas as partial=True, as the
        # apispec library doesn't handle recursively passing that down
        # like it should through nested/list objects.
        if self.partial is True:
            for field in self.declared_fields.values():
                # If the field has nested, then it's a
                # Nested field object
                if hasattr(field, "nested"):
                    field.nested.partial = True

                # If the field has inner, then it's a list
                # which has a nested schema within it
                if hasattr(field, "inner"):
                    if hasattr(field.inner, "nested"):
                        field.inner.nested.partial = True

    def _get_relational_validations(
        self,
    ) -> list[RelationalValidationMetadata]:
        validations: list[RelationalValidationMetadata] = []

        for attribute_name in dir(self):
            attribute = getattr(self, attribute_name)

            metadata = getattr(
                attribute,
                "__relational_validation__",
                None,
            )

            if metadata is not None:
                validations.append(metadata)

        return validations

    class Meta:
        # Ignore any extra fields
        unknown = EXCLUDE
