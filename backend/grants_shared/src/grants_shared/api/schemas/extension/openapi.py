from typing import Any

from apispec import BasePlugin

from grants_shared.api.schemas.extension.schema import Schema


class RelationalValidationOpenAPIPlugin(BasePlugin):
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