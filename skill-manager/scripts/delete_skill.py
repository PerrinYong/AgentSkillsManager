import os
import sys
import shutil


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


def resolve_skill_dir(skills_root, skill_name):
    """Resolve a skill directory by name.

    Supports skills directly under skills_root or nested one level deep.
    """
    direct = os.path.join(skills_root, skill_name)
    if os.path.isdir(direct) and os.path.exists(os.path.join(direct, "SKILL.md")):
        return direct

    matches = []
    try:
        for item in os.listdir(skills_root):
            level1 = os.path.join(skills_root, item)
            if not os.path.isdir(level1):
                continue
            candidate = os.path.join(level1, skill_name)
            if os.path.isdir(candidate) and os.path.exists(os.path.join(candidate, "SKILL.md")):
                matches.append(candidate)
    except OSError:
        return None

    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        print(f"Error: Skill name '{skill_name}' is ambiguous under {skills_root}")
        for m in matches:
            print(f"- {m}")
        return None
    return None

def delete_skill(skills_root, skill_name):
    skill_dir = resolve_skill_dir(skills_root, skill_name)
    if not skill_dir:
        print(f"Error: Skill '{skill_name}' not found under {skills_root}")
        return False
    
    try:
        # Physical deletion
        shutil.rmtree(skill_dir)
        print(f"Successfully deleted skill: {skill_name}")
        return True
    except Exception as e:
        print(f"Error deleting skill '{skill_name}': {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python delete_skill.py <skill_name> [skills_root]\n"
            "Env vars (optional): " + ", ".join(ENV_SKILLS_DIR_KEYS) + "\n"
            f"Default: {default_skills_root()}"
        )
        sys.exit(1)
        
    name = sys.argv[1]
    root = resolve_skills_root(sys.argv[2] if len(sys.argv) > 2 else None)
        
    delete_skill(root, name)
