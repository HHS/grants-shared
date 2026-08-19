from typing import Any

from apispec import BasePlugin

from grants_shared.api.schemas.extension.schema import Schema


class RelationalValidationOpenAPIPlugin(BasePlugin):
    """APISpec plugin that adds relational validation metadata to OpenAPI schemas.

    Schemas using ``@relational_validation`` expose their relational validation
    rules through the ``x-relational-validations`` OpenAPI extension.

    Register the plugin when creating an APIFlask application:

        app = APIFlask(
            __name__,
            title="My API",
            version="v1",
            spec_plugins=[RelationalValidationOpenAPIPlugin()],
        )

    The generated OpenAPI schema will then include, for example:

        x-relational-validations:
          - left_field: award_floor
            operator: less_than_or_equal
            right_field: award_ceiling
    """

    def schema_helper(
        self,
        name: str,
        definition: dict[str, Any],
        **kwargs: Any,
    ) -> dict[str, Any] | None:
        schema = kwargs.get("schema")

        if schema is None:
            return None

        if isinstance(schema, type):
            schema = schema()

        if not isinstance(schema, Schema):
            return None

        if not schema.relational_validations:
            return None

        return {
            "x-relational-validations": schema.relational_validations,
        }
