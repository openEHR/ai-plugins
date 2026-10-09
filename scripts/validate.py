#!/usr/bin/env python3
"""Validate marketplace and plugin manifests, skill/agent frontmatter, and bundled template sets.

Checks both Claude Code (``.claude-plugin/``) and Cursor (``.cursor-plugin/``) layouts.

Usage: python3 scripts/validate.py   (from the repo root)
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors = []

BMM_SKILLS = ("bmm-authoring", "class-generation", "regen-classes", "scaffold")
PLUGIN_NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")
MARKETPLACE_NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
MANIFEST_FIELDS = ("logo", "rules", "skills", "agents", "commands", "hooks", "mcpServers")


def err(msg):
    errors.append(msg)


def load_json(path: Path, label: str) -> dict | None:
    try:
        return json.loads(path.read_text())
    except Exception as e:
        err(f"{path.relative_to(ROOT)}: cannot parse JSON ({label}): {e}")
        return None


def validate_skills(plugin_dir: Path):
    skills_dir = plugin_dir / "skills"
    # Plugins may ship agents only; skip when no skills directory.
    if not skills_dir.is_dir():
        return
    for skill_dir in sorted(d for d in skills_dir.iterdir() if d.is_dir()):
        skill_md = skill_dir / "SKILL.md"
        rel = skill_md.relative_to(ROOT)
        if not skill_md.is_file():
            err(f"{rel}: missing SKILL.md")
            continue
        text = skill_md.read_text()
        m = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
        if not m:
            err(f"{rel}: missing YAML frontmatter")
            continue
        front = m.group(1)
        for field in ("name", "description"):
            if not re.search(rf"^{field}:", front, re.MULTILINE):
                err(f"{rel}: frontmatter missing '{field}'")
        fm_name = re.search(r"^name:\s*(\S+)", front, re.MULTILINE)
        if fm_name and fm_name.group(1) != skill_dir.name:
            err(f"{rel}: frontmatter name '{fm_name.group(1)}' != directory '{skill_dir.name}'")


def validate_template_sets(plugin_dir: Path):
    """A skill that ships assets/template-set.json carries its own checker (scripts/scaffold.py)."""
    for tset in sorted(plugin_dir.glob("skills/*/assets/template-set.json")):
        skill_dir = tset.parent.parent
        rel = skill_dir.relative_to(ROOT)
        script = skill_dir / "scripts" / "scaffold.py"
        if not script.is_file():
            err(f"{rel}: template-set.json without scripts/scaffold.py")
            continue
        try:
            spec = importlib.util.spec_from_file_location("scaffold_check", script)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            problems = module.check_template_set(skill_dir)
        except Exception as exc:  # a broken script must fail validation, not crash it
            err(f"{rel}: cannot run scripts/scaffold.py check: {exc!r}")
            continue
        for problem in problems:
            err(f"{rel}: template set: {problem}")


def validate_bmm_exclusions(plugin_dir: Path):
    """Every skill that writes or renders a BMM schema names each repo the scaffold excludes from that
    work (the excluded_components of its bmm-seed file), so the rule cannot drift between them."""
    tset_path = plugin_dir / "skills" / "scaffold" / "assets" / "template-set.json"
    if not tset_path.is_file():
        return
    tset = load_json(tset_path, "template set")
    if tset is None:
        return
    excluded = next((f.get("excluded_components", []) for f in tset.get("files", [])
                     if f.get("strategy") == "bmm-seed"), [])
    for skill in BMM_SKILLS:
        skill_md = plugin_dir / "skills" / skill / "SKILL.md"
        if not skill_md.is_file():
            continue
        missing = [c for c in excluded if c not in skill_md.read_text()]
        if missing:
            err(f"{skill_md.relative_to(ROOT)}: does not name {', '.join(missing)}, which the scaffold "
                "template set excludes from BMM work (files[bmm].excluded_components)")


def validate_md_components(plugin_dir: Path, subdir: str):
    """Validate flat .md components (agents/): frontmatter present with the required
    fields, and any `name` matches the filename stem."""
    comp_dir = plugin_dir / subdir
    if not comp_dir.is_dir():
        return
    for md in sorted(comp_dir.glob("*.md")):
        rel = md.relative_to(ROOT)
        m = re.match(r"\A---\n(.*?)\n---\n", md.read_text(), re.DOTALL)
        if not m:
            err(f"{rel}: missing YAML frontmatter")
            continue
        front = m.group(1)
        for field in ("name", "description"):
            if not re.search(rf"^{field}:", front, re.MULTILINE):
                err(f"{rel}: frontmatter missing '{field}'")
        fm_name = re.search(r"^name:\s*(\S+)", front, re.MULTILINE)
        if fm_name and fm_name.group(1) != md.stem:
            err(f"{rel}: frontmatter name '{fm_name.group(1)}' != filename '{md.stem}'")


def validate_manifest_paths(plugin_dir: Path, plugin_name: str, plugin: dict):
    for field in MANIFEST_FIELDS:
        value = plugin.get(field)
        if value is None:
            continue
        paths = [value] if isinstance(value, str) else value if isinstance(value, list) else []
        for path_value in paths:
            if isinstance(path_value, str) and path_value.startswith(("http://", "https://")):
                continue
            if not isinstance(path_value, str):
                continue
            resolved = (plugin_dir / path_value).resolve()
            try:
                resolved.relative_to(plugin_dir.resolve())
            except ValueError:
                err(f"{plugin_name}: {field} path '{path_value}' escapes plugin directory")
                continue
            if not resolved.exists():
                err(f"{plugin_name}: {field} references missing path '{path_value}'")


def validate_plugin_entry(name: str, version: str, plugin_dir: Path, manifest_subdir: str):
    if not PLUGIN_NAME_RE.match(name):
        err(f"{name}: plugin name must be lowercase alphanumerics, hyphens, and periods")
    if plugin_dir.name != name:
        err(f"{name}: directory '{plugin_dir.name}' != plugin name")
    if not plugin_dir.is_dir():
        err(f"{name}: plugin directory missing: {plugin_dir.relative_to(ROOT)}")
        return

    manifest = plugin_dir / manifest_subdir / "plugin.json"
    if not manifest.is_file():
        err(f"{name}: missing {manifest.relative_to(ROOT)}")
        return

    plugin = load_json(manifest, name)
    if plugin is None:
        return

    if plugin.get("name") != name:
        err(f"{name}: plugin.json name '{plugin.get('name')}' != marketplace entry")
    if plugin.get("version") != version:
        err(f"{name}: plugin.json version '{plugin.get('version')}' != marketplace '{version}'")

    validate_manifest_paths(plugin_dir, name, plugin)
    validate_skills(plugin_dir)
    validate_md_components(plugin_dir, "agents")


def validate_marketplace(mp_path: Path, manifest_subdir: str, label: str):
    marketplace = load_json(mp_path, label)
    if marketplace is None:
        return

    mp_name = marketplace.get("name")
    if not mp_name or not MARKETPLACE_NAME_RE.match(mp_name):
        err(f"{mp_path.relative_to(ROOT)}: marketplace 'name' must be lowercase kebab-case")

    owner = marketplace.get("owner") or {}
    if not owner.get("name"):
        err(f"{mp_path.relative_to(ROOT)}: marketplace 'owner.name' is required")

    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        err(f"{mp_path.relative_to(ROOT)}: 'plugins' must be a non-empty array")
        return

    seen = set()
    for entry in plugins:
        name, version, source = entry.get("name"), entry.get("version"), entry.get("source")
        if not all([name, version, source]):
            err(f"{label}: entry missing name/version/source: {entry}")
            continue
        if not name.startswith("openehr-"):
            err(f"{name}: plugin name must start with 'openehr-'")
        if name in seen:
            err(f"{label}: duplicate plugin name '{name}'")
        seen.add(name)

        plugin_dir = ROOT / source
        validate_plugin_entry(name, version, plugin_dir, manifest_subdir)


def validate_cross_manifest_versions():
    """The Claude and Cursor manifests of each plugin must agree on the version."""
    for plugin_dir in sorted(d for d in (ROOT / "plugins").iterdir() if d.is_dir()):
        versions = {}
        for subdir in (".claude-plugin", ".cursor-plugin"):
            manifest = plugin_dir / subdir / "plugin.json"
            if manifest.is_file():
                data = load_json(manifest, "cross-check")
                if data:
                    versions[subdir] = data.get("version")
        if len(set(versions.values())) > 1:
            err(f"{plugin_dir.name}: version mismatch between manifests: {versions}")


def main():
    for subdir, label in (
        (".claude-plugin", "Claude marketplace"),
        (".cursor-plugin", "Cursor marketplace"),
    ):
        mp_path = ROOT / subdir / "marketplace.json"
        if not mp_path.is_file():
            err(f"missing {mp_path.relative_to(ROOT)}")
            continue
        validate_marketplace(mp_path, subdir, label)

    validate_cross_manifest_versions()
    for plugin_dir in sorted(d for d in (ROOT / "plugins").iterdir() if d.is_dir()):
        validate_template_sets(plugin_dir)  # once per plugin, not once per marketplace
        validate_bmm_exclusions(plugin_dir)


if __name__ == "__main__":
    main()
    if errors:
        print(f"FAIL: {len(errors)} problem(s)")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("OK: Claude and Cursor manifests, plugin metadata, skills, template sets, and agents are valid")
