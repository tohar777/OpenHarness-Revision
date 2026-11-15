import json
import requests
import uuid
import asyncio
from pathlib import Path
from backend.system_config import systemprompt
from backend.filesystem import FileSystem
from backend.toolsregistry import ToolRegistry
from backend.shellexecution import ShellExecution
from backend.skills import SkillManager
from backend.websearch import WebSearch


# Configuration
CONFIG_PATH = Path(__file__).resolve().parents[3] / "config" / "config.json"

with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    config = json.load(file)

API_URL = config["API_URL"]
API_KEY = config["API_KEY"]
MODEL = config["API-MODEL"]


# Initialize tool registry
registry = ToolRegistry()


# Initialize tool implementations
fs = FileSystem("./")
se = ShellExecution()
ws = WebSearch()
skill = SkillManager()


# Register tools
registry.register(
    "skill_catalog",
    "Get the available skills.",
    skill.get_catalog,
    {
        "type": "object",
        "properties": {},
        "required": []
    }
)

registry.register(
    "load_skill",
    "Load a skill by name.",
    skill.load_skill,
    {
        "type": "object",
        "properties": {
            "name": {"type": "string"}
        },
        "required": ["name"]
    }
)

registry.register(
    "read_file",
    "Read the contents of a file.",
    fs.read_file,
    {
        "type": "object",
        "properties": {
            "filename": {"type": "string"}
        },
        "required": ["filename"]
    }
)

registry.register(
    "shell",
    "Execute a shell command.",
    se.execute_shell,
    {
        "type": "object",
        "properties": {
            "cmd": {"type": "string"}
        },
        "required": ["cmd"]
    }
)

registry.register(
    "write_file",
    "Write content to a file.",
    fs.write_file,
    {
        "type": "object",
        "properties": {
            "filename": {"type": "string"},
            "content": {"type": "string"}
        },
        "required": ["filename", "content"]
    }
)

registry.register(
    "list_files",
    "List files in the current directory.",
    fs.list_files,
    {
        "type": "object",
        "properties": {},
        "required": []
    }
)

registry.register(
    "web_search",
    "Search the web.",
    ws.web_search,
    {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "max_results": {"type": "integer"}
        },
        "required": ["query"]
    }
)

registry.register(
    "web_fetch",
    "Fetch the contents of a webpage.",
    ws.web_fetch,
    {
        "type": "object",
        "properties": {
            "url": {"type": "string"}
        },
        "required": ["url"]
    }
)

registry.register(
    "change_directory",
    "Change the current working directory.",
    fs.change_dir,
    {
        "type": "object",
        "properties": {
            "dir": {"type": "string"}
        },
        "required": ["dir"]
    }
)




async def sendRequest(prompt: str):
    messages = [
        {
            "role": "system",
            "content": systemprompt()
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    is_openai_compatible = "/v1/" in API_URL
    max_iterations = 1000

    def extract_custom_tool_call(message):
        """
        Supports models that return:
        {
            "name": "write_file",
            "arguments": {...}
        }
        inside message.content.
        """
        content = message.get("content")

        if not isinstance(content, str):
            return None

        content = content.strip()

        # Handle Markdown JSON code blocks
        if content.startswith("```"):
            content = content.split("\n", 1)[-1]
            content = content.rsplit("```", 1)[0].strip()

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return None

        if (
            isinstance(data, dict)
            and isinstance(data.get("name"), str)
            and isinstance(data.get("arguments"), dict)
        ):
            return {
                "name": data["name"],
                "arguments": data["arguments"]
            }

        return None

    for iteration in range(max_iterations):

        payload = {
            "model": MODEL,
            "messages": messages,
            "tools": registry.get_schemas(),
            "stream": False
        }

        try:
            # Avoid blocking the async event loop
            response = await asyncio.to_thread(
                requests.post,
                API_URL,
                headers=headers,
                json=payload
            )

            response.raise_for_status()
            result = response.json()

            # Extract assistant message
            if "choices" in result:
                message = result["choices"][0]["message"]

            elif "message" in result:
                message = result["message"]

            else:
                return f"Unexpected API response: {result}"

            print(f"\n--- Iteration {iteration + 1} ---")
            print("Assistant:", json.dumps(
                message,
                indent=4,
                ensure_ascii=False
            ))

            # 1. Native tool calls
            tool_calls = message.get("tool_calls") or []

            # 2. Custom JSON tool calls inside message.content
            custom_call = None

            if not tool_calls:
                custom_call = extract_custom_tool_call(message)

            # No tool calls means the model has finished
            if not tool_calls and not custom_call:
                return message.get("content") or ""

            # Execute native tool calls
            if tool_calls:

                messages.append(message)

                for tool_call in tool_calls:

                    function = tool_call["function"]
                    tool_name = function["name"]
                    arguments = function.get("arguments", {})

                    if isinstance(arguments, str):
                        arguments = json.loads(arguments)

                    print(f"\nExecuting tool: {tool_name}")
                    print("Arguments:", arguments)

                    tool_result = await registry.execute(
                        tool_name,
                        arguments
                    )

                    print("Tool result:", tool_result)

                    if is_openai_compatible:
                        tool_call_id = tool_call.get("id")

                        if not tool_call_id:
                            return "Tool call is missing its ID."

                        tool_message = {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": str(tool_result)
                        }

                    else:
                        tool_message = {
                            "role": "tool",
                            "content": str(tool_result)
                        }

                    messages.append(tool_message)

            # Execute custom JSON tool calls
            elif custom_call:

                tool_name = custom_call["name"]
                arguments = custom_call["arguments"]

                print(f"\nExecuting custom tool: {tool_name}")
                print("Arguments:", arguments)

                tool_result = await registry.execute(
                    tool_name,
                    arguments
                )

                print("Tool result:", tool_result)

                if is_openai_compatible:
                    # Convert custom JSON into a native tool-call message
                    tool_call_id = "call_" + uuid.uuid4().hex

                    messages.append({
                        "role": "assistant",
                        "content": message.get("content", "")
                    })

                    messages.append({
                        "role": "user",
                        "content": (
                            f"Tool '{tool_name}' executed successfully.\n"
                            f"Result:\n{tool_result}\n\n"
                            "Continue working on the original request. "
                            "Do not repeat the tool call unless necessary."
                        )
                    })

                else:
                    # Native Ollama-style tool result
                    messages.append({
                        "role": "assistant",
                        "content": message.get("content", "")
                    })

                    messages.append({
                        "role": "tool",
                        "content": str(tool_result)
                    })

        except requests.exceptions.RequestException as error:
            return f"API request failed: {error}"

        except Exception as error:
            print(f"Agent error: {error}")
            return f"Agent execution failed: {error}"

    return "Maximum tool execution iterations reached."
