from pydantic import BaseModel, ConfigDict
from pydantic.json_schema import JsonSchemaValue


class RequiredFieldsModel(BaseModel):
    model_config = ConfigDict()

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler) -> JsonSchemaValue:
        schema = handler(core_schema)

        # object schema에서 모든 property를 required로 강제
        if schema.get("type") == "object":
            props = schema.get("properties", {})
            if props:
                schema["required"] = list(props.keys())

        return schema
