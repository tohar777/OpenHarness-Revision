import json
import requests

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

    # Tool execution loop
    max_iterations = 8

    for _ in range(max_iterations):
        payload = {
            "model": MODEL,
            "messages": messages,
            "tools": registry.get_schemas(),
            "tool_choice": "auto"
        }

        try:
            response = requests.post(
                API_URL,
                headers=headers,
                json=payload,
                timeout=120
            )

            response.raise_for_status()
            result = response.json()

            message = result["choices"][0]["message"]

            # No tool calls: return final response
            tool_calls = message.get("tool_calls")

            if not tool_calls:
                return message.get("content", "")

            # Add assistant tool-call message
            messages.append(message)

            # Execute each requested tool
            for tool_call in tool_calls:
                function = tool_call["function"]

                tool_name = function["name"]
                arguments = json.loads(function["arguments"])

                try:
                    tool_result = await registry.execute(
                        tool_name,
                        arguments
                    )

                    if not isinstance(tool_result, str):
                        tool_result = json.dumps(
                            tool_result,
                            ensure_ascii=False,
                            default=str
                        )

                except Exception as error:
                    tool_result = json.dumps({
                        "error": str(error)
                    })

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": tool_result
                })

        except requests.exceptions.RequestException as error:
            return f"API request failed: {error}"

        except (KeyError, IndexError, ValueError) as error:
            return f"Invalid API response: {error}"

    return "Maximum tool execution iterations reached."