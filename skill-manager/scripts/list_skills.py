import os
import sys
import yaml
import io


ENV_SKILLS_DIR_KEYS = ("CLAUDE_SKILLS_DIR", "AGENTSKILLS_DIR", "SKILLS_DIR")


def default_skills_root():
    # Default to this repo's AgentSkillsManager directory.
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def resolve_skills_root(cli_arg=None):
    # Precedence: CLI arg > env var > repo default.
    if cli_arg:
        return cli_arg
    for k in ENV_SKILLS_DIR_KEYS:
        v = os.environ.get(k)
        if v:
            return v
    return default_skills_root()


def iter_skill_dirs(skills_root):
    """Yield skill directories that contain SKILL.md.

    Skills may exist directly under skills_root OR one directory deeper.
    """
    if not os.path.exists(skills_root):
        return

    for item in os.listdir(skills_root):
        level1 = os.path.join(skills_root, item)
        if not os.path.isdir(level1):
            continue

        if os.path.exists(os.path.join(level1, "SKILL.md")):
            yield level1
            continue

        try:
            for sub in os.listdir(level1):
                level2 = os.path.join(level1, sub)
                if os.path.isdir(level2) and os.path.exists(os.path.join(level2, "SKILL.md")):
                    yield level2
        except OSError:
            continue

# Force UTF-8 encoding for stdout to handle Chinese characters on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
else:
    # Fallback for older Python versions
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def list_skills(skills_root):
    if not os.path.exists(skills_root):
        print(f"Error: {skills_root} not found")
        return

    # Header with Description column
    header = f"{'Skill Name':<20} | {'Type':<12} | {'Description':<40} | {'Ver':<8}"
    print(header)
    print("-" * len(header))

    for skill_dir in iter_skill_dirs(skills_root):
        item = os.path.basename(skill_dir)
        skill_md = os.path.join(skill_dir, "SKILL.md")
        skill_type = "Standard"
        version = "0.1.0"
        description = "No description"
        
        if os.path.exists(skill_md):
            try:
                with open(skill_md, "r", encoding="utf-8") as f:
                    content = f.read()
                parts = content.split("---")
                if len(parts) >= 3:
                    meta = yaml.safe_load(parts[1])
                    if "github_url" in meta:
                        skill_type = "GitHub"
                    version = str(meta.get("version", "0.1.0"))
                    description = meta.get("description", "No description").replace('\n', ' ')
            except:
                pass
        
        # Simple truncation for display
        if len(description) > 37:
            display_desc = description[:37] + "..."
        else:
            display_desc = description
            
        # Using a fixed width but acknowledging that Chinese chars take 2 cells
        # This is a basic fix, for perfect alignment one would need wcwidth
        print(f"{item:<20} | {skill_type:<12} | {display_desc:<40} | {version:<8}")

if __name__ == "__main__":
    skills_path = resolve_skills_root(sys.argv[1] if len(sys.argv) > 1 else None)
    list_skills(skills_path)
