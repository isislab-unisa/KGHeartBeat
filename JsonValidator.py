import json
from jsonschema import validate
import jsonschema

from InputValidator import InputValidator

class JsonValidator(InputValidator):
    
    def __init__(self, input):
        super().__init__(input)

    def validateJson(self):
        schema = {
        "$schema": "http://json-schema.org/draft-04/schema#",
        "type": ["object","null"],
      "properties": {
        "name": {
          "type": "array",
          "items": [
            {
              "type": ["string","null"]
            }
          ]
        },
        "id": {
          "type": "array",
          "items": [
            {
              "type": ["string","null"]
            }
          ]
        }
      },
      "required": [
        "name",
        "id"
      ]
        }
        try:
            validate(instance=self.input, schema=schema)
        except jsonschema.exceptions.ValidationError as err:
          return False
        return True