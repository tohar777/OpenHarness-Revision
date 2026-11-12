
from backend.filesystem import FileSystem
from backend.toolsregistry import ToolRegistry
from backend.shellexecution import ShellExecution
from backend.skills import SkillManager
from backend.websearch import WebSearch


class Tools:

    def __init__(self):
        self.fs = FileSystem("./")
        self.se = ShellExecution()
        self.ws = WebSearch()
        self.skill = SkillManager()

    def load(self, registry: ToolRegistry) -> ToolRegistry:
        """Register all available OpenHarness tools."""

        # Skill tools
        registry.register(
            "skill_catalog",
            "List available skills in the skills directory.",
            self.skill.get_catalog,
            {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        )

        registry.register(
            "load_skill",
            "Load a skill's full instructions.",
            self.skill.load_skill,
            {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the skill to load."
                    }
                },
                "required": ["name"],
                "additionalProperties": False
            }
        )

        # Filesystem tools
        registry.register(
            "read_file",
            "Read a text file from the workspace.",
            self.fs.read_file,
            {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"}
                },
                "required": ["filename"],
                "additionalProperties": False
            }
        )

        registry.register(
            "write_file",
            "Create or modify a text file in the workspace.",
            self.fs.write_file,
            {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["filename", "content"],
                "additionalProperties": False
            }
        )

        registry.register(
            "list_files",
            "List files in the workspace.",
            self.fs.list_files,
            {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        )

        registry.register(
            "change_directory",
            "Change the workspace directory.",
            self.fs.change_dir,
            {
                "type": "object",
                "properties": {
                    "dir": {"type": "string"}
                },
                "required": ["dir"],
                "additionalProperties": False
            }
        )

        # Shell tools
        registry.register(
            "shell",
            "Execute shell commands.",
            self.se.execute_shell,
            {
                "type": "object",
                "properties": {
                    "cmd": {"type": "string"}
                },
                "required": ["cmd"],
                "additionalProperties": False
            }
        )

        # Web tools
        registry.register(
            "web_search",
            "Search the internet for information.",
            self.ws.web_search,
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer"}
                },
                "required": ["query"],
                "additionalProperties": False
            }
        )

        registry.register(
            "web_fetch",
            "Fetch information from a URL.",
            self.ws.web_fetch,
            {
                "type": "object",
                "properties": {
                    "url": {"type": "string"}
                },
                "required": ["url"],
                "additionalProperties": False
            }
        )

        return registry
