import os
import sys
import yaml
import json
import subprocess
import concurrent.futures


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

        # One more level deep
        try:
            for sub in os.listdir(level1):
                level2 = os.path.join(level1, sub)
                if os.path.isdir(level2) and os.path.exists(os.path.join(level2, "SKILL.md")):
                    yield level2
        except OSError:
            continue

def get_remote_hash(url):
    """Fetch the latest commit hash from the remote repository."""
    try:
        # Using git ls-remote to avoid downloading the whole repo
        # Asking for HEAD specifically
        result = subprocess.run(
            ['git', 'ls-remote', url, 'HEAD'], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        if result.returncode != 0:
            return None
        # Output format: <hash>\tHEAD
        parts = result.stdout.split()
        if parts:
            return parts[0]
        return None
    except Exception:
        return None

def scan_skills(skills_root):
    """Scan all subdirectories for SKILL.md and extract metadata."""
    skill_list = []
    
    if not os.path.exists(skills_root):
        print(f"Skills root not found: {skills_root}", file=sys.stderr)
        return []

    for skill_dir in iter_skill_dirs(skills_root):
        item = os.path.basename(skill_dir)
        skill_md = os.path.join(skill_dir, "SKILL.md")
             
        # Parse Frontmatter
        try:
            with open(skill_md, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract YAML between first two ---
            parts = content.split('---')
            if len(parts) < 3:
                continue # Invalid format
                
            frontmatter = yaml.safe_load(parts[1])
            
            # Check if managed by github-to-skills
            if 'github_url' in frontmatter:
                skill_list.append({
                    "name": frontmatter.get('name', item),
                    "dir": skill_dir,
                    "github_url": frontmatter['github_url'],
                    "local_hash": frontmatter.get('github_hash', 'unknown'),
                    "local_version": frontmatter.get('version', '0.0.0')
                })
        except Exception as e:
            # print(f"Skipping {item}: {e}", file=sys.stderr)
            pass
            
    return skill_list

def check_updates(skills):
    """Check for updates concurrently."""
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Create a map of future -> skill
        future_to_skill = {
            executor.submit(get_remote_hash, skill['github_url']): skill 
            for skill in skills
        }
        
        for future in concurrent.futures.as_completed(future_to_skill):
            skill = future_to_skill[future]
            try:
                remote_hash = future.result()
                skill['remote_hash'] = remote_hash
                
                if not remote_hash:
                    skill['status'] = 'error'
                    skill['message'] = 'Could not reach remote'
                elif remote_hash != skill['local_hash']:
                    skill['status'] = 'outdated'
                    skill['message'] = 'New commits available'
                else:
                    skill['status'] = 'current'
                    skill['message'] = 'Up to date'
                    
                results.append(skill)
            except Exception as e:
                skill['status'] = 'error'
                skill['message'] = str(e)
                results.append(skill)
                
    return results

if __name__ == "__main__":
    target_dir = resolve_skills_root(sys.argv[1] if len(sys.argv) > 1 else None)
    if not os.path.exists(target_dir):
        print(f"Skills root not found: {target_dir}", file=sys.stderr)
        print(
            "Usage: python scan_and_check.py [skills_dir]\n"
            "Env vars (optional): " + ", ".join(ENV_SKILLS_DIR_KEYS) + "\n"
            f"Default: {default_skills_root()}",
            file=sys.stderr,
        )
        sys.exit(1)

    skills = scan_skills(target_dir)
    updates = check_updates(skills)
    
    print(json.dumps(updates, indent=2))
