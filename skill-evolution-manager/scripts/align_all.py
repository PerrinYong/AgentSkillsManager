import os
import sys
import subprocess


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

def align_all(skills_root):
    if not os.path.exists(skills_root):
        print(f"Error: {skills_root} not found")
        return

    stitch_script = os.path.join(os.path.dirname(__file__), "smart_stitch.py")
    
    count = 0
    for skill_dir in iter_skill_dirs(skills_root):
        item = os.path.basename(skill_dir)
             
        evolution_json = os.path.join(skill_dir, "evolution.json")
        if os.path.exists(evolution_json):
            print(f"Aligning {item}...")
            # Run the smart_stitch script for this skill
            subprocess.run([sys.executable, stitch_script, skill_dir])
            count += 1
            
    print(f"\nFinished. Aligned {count} skills.")

if __name__ == "__main__":
    skills_path = resolve_skills_root(sys.argv[1] if len(sys.argv) > 1 else None)
    align_all(skills_path)
