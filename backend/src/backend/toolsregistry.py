import inspect


import inspect
import json


class ToolRegistry:

    def __init__(self):
        self.tools = {}

    def register(self, name, description, function, parameters):
        if not callable(function):
            raise TypeError(f"Tool '{name}' must be callable")

        self.tools[name] = {
            "description": description,
            "function": function,
            "parameters": parameters
        }

    def get_schemas(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                    "strict": False
                }
            }
            for name, tool in self.tools.items()
        ]

    async def execute(self, name, arguments):
        if name not in self.tools:
            raise ValueError(f"Unknown tool: {name}")

        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Invalid JSON arguments for '{name}': {e}"
                ) from e

        if not isinstance(arguments, dict):
            raise TypeError("Tool arguments must be a dictionary")

        function = self.tools[name]["function"]

        try:
            result = function(**arguments)

            if inspect.isawaitable(result):
                result = await result

            if isinstance(result, (dict, list)):
                return json.dumps(result, ensure_ascii=False)

            if result is None:
                return "Tool executed successfully (no output)."

            return str(result)

        except Exception as e:
            return json.dumps({
                "error": str(e),
                "tool": name
            }, ensure_ascii=False)
