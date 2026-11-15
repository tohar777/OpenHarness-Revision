
import yaml
from pathlib import Path


class SkillManager:

    def __init__(self, skills_dir=None):
        if skills_dir is None:
            project_root = Path(__file__).resolve().parents[3]
            skills_dir = project_root / "skills"

        self.skills_dir = Path(skills_dir).resolve()
        self.skills = {}

        print("Skills directory:", self.skills_dir)
        print("Exists:", self.skills_dir.is_dir())

    def discover(self):
        self.skills.clear()

        if not self.skills_dir.is_dir():
            print("ERROR: Skills directory does not exist")
            return []

        skill_files = list(self.skills_dir.glob("*/SKILL.md"))
        print("Skill files found:", skill_files)

        for skill_file in skill_files:
            print(f"\nChecking: {skill_file}")

            try:
                content = skill_file.read_text(encoding="utf-8-sig")

                if not content.startswith("---"):
                    print("REJECTED: Missing YAML frontmatter")
                    continue

                parts = content.split("---", 2)

                if len(parts) != 3:
                    print("REJECTED: Invalid frontmatter")
                    continue

                metadata = yaml.safe_load(parts[1]) or {}

                if not isinstance(metadata, dict):
                    continue

                name = metadata.get("name")
                description = metadata.get("description")

                if not name or not description:
                    print("REJECTED: Missing metadata")
                    continue

                if name != skill_file.parent.name:
                    print(f"REJECTED: Name mismatch: {name}")
                    continue

                self.skills[name] = {
                    "description": description,
                    "content": parts[2].strip()
                }

                print("ACCEPTED:", name)

            except Exception as e:
                print("ERROR:", repr(e))

        print("Loaded skills:", list(self.skills.keys()))

        return [
            {"name": name, "description": skill["description"]}
            for name, skill in self.skills.items()
        ]

    def get_catalog(self):
        skills = self.discover()

        if not skills:
            return "No valid skills found in the skills directory."

        return "\n".join(
            f"- {skill['name']}: {skill['description']}"
            for skill in skills
        )

    def load_skill(self, name: str):
        self.discover()

        name = name.strip().lower()

        if name not in self.skills:
            matches = [
                skill_name
                for skill_name in self.skills
                if name in skill_name.lower()
            ]

            if len(matches) == 1:
                name = matches[0]
            else:
                raise ValueError(
                    f"Unknown or ambiguous skill: {name}. "
                    f"Available skills: {list(self.skills.keys())}"
                )

        skill = self.skills[name]

        return {
            "name": name,
            "instructions": skill["content"]
        }
