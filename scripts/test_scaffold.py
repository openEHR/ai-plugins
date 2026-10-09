#!/usr/bin/env python3
"""Tests for the scaffold skill's script (plugins/openehr-specs/skills/scaffold/scripts/scaffold.py).

Run from the repo root: python3 -m unittest discover -s scripts -p 'test_*.py'
Standard library only; every test works in a temporary directory.
"""
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "plugins/openehr-specs/skills/scaffold/scripts/scaffold.py"
_spec = importlib.util.spec_from_file_location("scaffold", SCRIPT)
scaffold = importlib.util.module_from_spec(_spec)
sys.modules["scaffold"] = scaffold
_spec.loader.exec_module(scaffold)

TITLE = {"component_title": "Demo Model"}


class FakeDocker:
    """Stands in for scaffold.docker: an image bundling `schemas` ({id: text}), or none at all (None)."""

    def __init__(self, schemas, problem="docker is not installed"):
        self.schemas, self.problem, self.calls = schemas, problem, []

    def __call__(self, *args):
        self.calls.append(args)
        if self.schemas is None:
            return None, self.problem
        if args[-2:] == ("ghcr.io/openehr/bmm-publisher", "/app/resources"):
            return "".join(f"{i}.bmm.json\n" for i in self.schemas), None
        name = args[-1].rsplit("/", 1)[-1][: -len(".bmm.json")]
        if name in self.schemas:
            return self.schemas[name], None
        return None, f"cat: can't open '{args[-1]}': No such file or directory"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        # no stray GIT_* variable and no repository above the temporary directory may leak in
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env["GIT_CEILING_DIRECTORIES"] = str(self.root.parent)
        patcher = mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        # the host's Docker must not leak in either: by default the bmm-publisher image is unavailable
        self.docker = FakeDocker(None)
        patcher = mock.patch.object(scaffold, "docker", self.docker)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.repo = self.root / "specifications-DEMO"
        self.repo.mkdir()
        self.set_dir = scaffold.SET_DIR

    def plan(self, repo=None, overwrite=(), pin=(), **variables):
        return scaffold.build_plan(repo or self.repo, self.set_dir, dict(TITLE, **variables), overwrite, pin)

    def actions(self, plan):
        return {a.target: a.action for a in plan.acts}

    def apply(self, repo=None, overwrite=(), pin=(), **variables):
        return scaffold.apply_plan(repo or self.repo, self.set_dir, dict(TITLE, **variables), overwrite, pin)

    def text(self, name):
        return (self.repo / name).read_text(encoding="utf-8")

    def put(self, name, text):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def base_clone(self, *schema_ids):
        """A sibling specifications-BASE clone holding the given BMM schema ids."""
        bmm = self.root / "specifications-BASE" / "computable" / "BMM"
        bmm.mkdir(parents=True, exist_ok=True)
        for schema_id in schema_ids:
            (bmm / f"{schema_id}.bmm.json").write_text("{}", encoding="utf-8")

    def copy_set(self):
        dst = self.root / f"set{len(list(self.root.glob('set*')))}"
        shutil.copytree(scaffold.SET_DIR, dst, ignore=shutil.ignore_patterns("__pycache__"))
        return dst

    def bump(self, dst, steps=None, edit=None):
        """Add the next revision (with its migration file) to a copied template set."""
        path = dst / "assets" / "template-set.json"
        tset = json.loads(path.read_text(encoding="utf-8"))
        rev = tset["revision"] + 1
        tset["revision"] = rev
        tset["revisions"].append({"revision": rev, "released": "2027-01-01", "summary": "test", "digest": ""})
        path.write_text(json.dumps(tset, indent=2), encoding="utf-8")
        (dst / "migrations").mkdir(exist_ok=True)
        (dst / "migrations" / f"{rev:04d}.json").write_text(
            json.dumps({"from": rev - 1, "to": rev, "steps": steps or []}), encoding="utf-8")
        if edit:
            edit(dst)
        scaffold.seal(dst)
        return rev


class EngineTests(unittest.TestCase):
    def test_conditionals_and_standalone_tag_lines(self):
        text = "a\n{{#if x}}\nb\n{{/if}}\nc\n{{#unless x}}\nd\n{{/unless}}\ne\n"
        self.assertEqual(scaffold.render(text, {"x": "1"}), "a\nb\nc\ne\n")
        self.assertEqual(scaffold.render(text, {"x": ""}), "a\nc\nd\ne\n")

    def test_inline_conditional_keeps_the_line(self):
        self.assertEqual(scaffold.render("v{{#if x}} + m{{/if}}.", {"x": "yes"}), "v + m.")
        self.assertEqual(scaffold.render("v{{#if x}} + m{{/if}}.", {"x": ""}), "v.")

    def test_false_like_values_are_falsy(self):
        for value in ("", "false", "0", "no"):
            self.assertEqual(scaffold.render("{{#if x}}y{{/if}}", {"x": value}), "")

    def test_filters(self):
        self.assertEqual(scaffold.render("{{a|lower}} {{a|upper}}", {"a": "Base Model"}), "base model BASE MODEL")

    def test_unknown_variable_is_an_error(self):
        with self.assertRaises(scaffold.ScaffoldError):
            scaffold.render("{{nope}}", {})
        with self.assertRaises(scaffold.ScaffoldError):
            scaffold.render("{{#if nope}}x{{/if}}", {})

    def test_nested_blocks_are_rejected(self):
        with self.assertRaises(scaffold.ScaffoldError):
            scaffold.render("{{#if a}}{{#if b}}x{{/if}}{{/if}}", {"a": "1", "b": "1"})

    def test_json_escape(self):
        out = scaffold.render('{"t": "{{t}}"}', {"t": 'Say "hi"\\'}, scaffold.json_escape)
        self.assertEqual(json.loads(out), {"t": 'Say "hi"\\'})


class InitTests(Base):
    def test_init_creates_the_standard_set_and_the_second_run_is_a_noop(self):
        result = self.apply()
        self.assertTrue(result["applied"])
        for name in (".claude/scaffold.json", "AGENTS.md", ".claude/CLAUDE.md", ".claude/settings.json",
                     "manifest.json", ".gitignore", ".asciidoctorconfig", "LICENSE", "README.md"):
            self.assertTrue((self.repo / name).is_file(), name)
        self.assertEqual(self.plan().mode, "current")
        self.assertTrue(all(a in ("unchanged", "exists", "skipped") for a in self.actions(self.plan()).values()))
        self.assertEqual(json.loads(self.text("manifest.json"))["id"], "DEMO")
        self.assertIn(":component: DEMO", self.text(".asciidoctorconfig"))
        self.assertIn("Changes for SPECDEMO-", self.text("AGENTS.md"))

    def test_descriptor_records_revision_variables_and_hashes(self):
        self.apply()
        desc = json.loads(self.text(".claude/scaffold.json"))
        self.assertEqual(list(desc)[:2], ["template_set", "revision"])
        latest = json.loads((self.set_dir / "assets/template-set.json").read_text(encoding="utf-8"))["revision"]
        self.assertEqual(desc["revision"], latest)
        self.assertEqual(desc["variables"]["component"], "DEMO")
        self.assertNotIn("license_name", desc["variables"])  # derived, not stored
        self.assertEqual(set(desc["files"]["agents"]["regions"]), {"plugin", "build", "conventions"})
        self.assertIn("sha256", desc["files"]["claude-md"])

    def test_bmm_switches_on_the_class_generation_sections(self):
        self.apply(bmm_schema_id="openehr_demo_1.0.0")
        agents = self.text("AGENTS.md")
        self.assertIn("computable/BMM/openehr_demo_1.0.0.bmm.json", agents)
        self.assertIn("openehr-specs:class-generation", agents)
        self.assertIn("## Gotchas", agents)
        self.assertIn("and BMM sources", self.text(".claude/CLAUDE.md"))

    def test_a_base_dependency_is_loaded_with_d_in_the_class_table_command(self):
        self.apply(bmm_schema_id="openehr_demo_1.0.0", base_bmm_schema_id="openehr_base_1.3.0")
        agents = self.text("AGENTS.md")
        self.assertIn('  -v "$PWD/../specifications-BASE/computable/BMM/openehr_base_1.3.0.bmm.json"'
                      ':/in/openehr_base_1.3.0.bmm.json:ro \\\n', agents)
        self.assertIn("  ghcr.io/openehr/bmm-publisher legacy-adoc \\\n"
                      "  -d /in/openehr_base_1.3.0.bmm.json \\\n"
                      "  /in/openehr_demo_1.0.0.bmm.json -o /out\n", agents)

    def test_without_a_base_dependency_the_command_has_no_d_option(self):
        self.apply(bmm_schema_id="openehr_demo_1.0.0")
        agents = self.text("AGENTS.md")
        self.assertNotIn("-d /in/", agents)
        self.assertNotIn("specifications-BASE/computable", agents)
        self.assertIn("  ghcr.io/openehr/bmm-publisher legacy-adoc \\\n"
                      "  /in/openehr_demo_1.0.0.bmm.json -o /out\n", agents)

    def test_agents_md_asks_for_the_repos_own_tooling_instead_of_denying_it(self):
        self.apply()
        agents = self.text("AGENTS.md")
        self.assertNotIn("No build tooling lives in this repo", agents)
        self.assertIn("TODO(scaffold): if this repo has its own tooling", agents)

    def test_claude_md_points_repo_guidance_to_agents_md(self):
        self.apply()
        self.assertIn("outside the `openehr-scaffold` regions", self.text(".claude/CLAUDE.md"))

    def test_without_bmm_those_sections_are_absent(self):
        self.apply()
        agents = self.text("AGENTS.md")
        for needle in ("class-generation", "## Gotchas", "bmm-publisher", "BMM"):
            self.assertNotIn(needle, agents)

    def test_missing_required_variables_stop_the_plan(self):
        plan = scaffold.build_plan(self.repo, self.set_dir, {})
        self.assertEqual([m["name"] for m in plan.missing], ["component_title"])
        self.assertEqual(plan.acts, [])
        self.assertEqual(scaffold.public(plan)["status"], "needs_input")

    def test_invalid_values_are_reported(self):
        plan = self.plan(jira_project="jira-ish")
        self.assertEqual([i["name"] for i in plan.invalid], ["jira_project"])

    def test_hyphenated_component_cannot_default_its_jira_key(self):
        repo = self.root / "specifications-ITS-REST"
        repo.mkdir()
        plan = self.plan(repo)
        self.assertEqual(plan.values["component"], "ITS-REST")
        self.assertEqual([i["name"] for i in plan.invalid], ["jira_project"])  # SPECITS-REST is wrong: ask
        self.assertEqual(self.plan(repo, jira_project="SPECITS").invalid, [])

    def test_its_components_default_to_apache(self):
        repo = self.root / "specifications-ITS-JSON"
        repo.mkdir()
        self.assertEqual(self.plan(repo, jira_project="SPECITS").values["license"], "apache-2.0")
        self.assertEqual(self.plan().values["license"], "cc-by-sa-3.0")

    def test_quotes_in_the_title_do_not_break_manifest_json(self):
        self.apply(component_title='The "Demo" Model')
        self.assertEqual(json.loads(self.text("manifest.json"))["title"], 'The "Demo" Model')

    def test_explicit_beats_descriptor_beats_inferred(self):
        self.apply(default_branch="main")
        self.assertEqual(self.plan().values["default_branch"], "main")  # recorded
        self.assertEqual(self.plan(default_branch="trunk").values["default_branch"], "trunk")  # explicit


class InferTests(Base):
    def test_variables_come_from_an_existing_manifest(self):
        self.put("manifest.json", json.dumps({
            "id": "DEMO", "title": "Demo Model", "description": "d", "keywords": "k",
            "jira": {"roadmap": "SPECDEMO", "open_issues": "11999"},
            "specifications": [{"id": "alpha"}, {"id": "beta"}]}))
        plan = scaffold.build_plan(self.repo, self.set_dir, {})
        self.assertEqual(plan.missing, [])
        self.assertEqual(plan.values["jira_open_issues"], "11999")
        self.assertEqual(plan.values["documents"], "`alpha`, `beta`")
        self.assertTrue(plan.sources["component_title"].startswith("inferred"))

    def test_bmm_schema_is_found(self):
        self.put("computable/BMM/openehr_demo_1.2.0.bmm.json", "{}")
        self.assertEqual(self.plan().values["bmm_schema_id"], "openehr_demo_1.2.0")

    def test_base_bmm_comes_from_the_sibling_base_clone_highest_version_first(self):
        self.put("computable/BMM/openehr_demo_1.0.0.bmm.json", "{}")
        self.base_clone("openehr_base_1.2.0", "openehr_base_1.10.0", "openehr_base_1.3.0")
        plan = self.plan()
        self.assertEqual(plan.values["base_bmm_schema_id"], "openehr_base_1.10.0")
        self.assertTrue(plan.sources["base_bmm_schema_id"].startswith("inferred"))

    def test_base_itself_gets_no_base_dependency(self):
        repo = self.root / "specifications-BASE"
        (repo / "computable/BMM").mkdir(parents=True)
        (repo / "computable/BMM/openehr_base_1.3.0.bmm.json").write_text("{}", encoding="utf-8")
        plan = self.plan(repo)
        self.assertEqual(plan.values["base_bmm_schema_id"], "")
        self.assertFalse(any("specifications-BASE" in w for w in plan.warnings))

    def test_a_repo_without_bmm_gets_no_base_dependency(self):
        self.base_clone("openehr_base_1.3.0")
        self.assertEqual(self.plan().values["base_bmm_schema_id"], "")

    def test_a_missing_base_clone_is_reported(self):
        self.put("computable/BMM/openehr_demo_1.0.0.bmm.json", "{}")
        plan = self.plan()
        self.assertEqual(plan.values["base_bmm_schema_id"], "")
        self.assertTrue(any("specifications-BASE" in w for w in plan.warnings), plan.warnings)

    def test_licence_family_is_recognised_from_the_text(self):
        text = (self.set_dir / "assets/templates/license-apache-2.0.txt").read_text(encoding="utf-8")
        self.put("LICENSE", text)
        self.assertEqual(self.plan().values["license"], "apache-2.0")

    def test_component_from_git_remote_when_the_directory_name_says_nothing(self):
        repo = self.root / "checkout"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "remote", "add", "origin",
                        "https://github.com/openEHR/specifications-QUERY.git"], check=True)
        plan = self.plan(repo)
        self.assertEqual(plan.values["component"], "QUERY")
        self.assertEqual(plan.values["repo_name"], "specifications-QUERY")

    def test_component_from_asciidoctorconfig(self):
        repo = self.root / "somewhere"
        repo.mkdir()
        (repo / ".asciidoctorconfig").write_text(":component: PROC\n", encoding="utf-8")
        self.assertEqual(self.plan(repo).values["component"], "PROC")


class StrategyTests(Base):
    def test_seed_files_are_never_overwritten(self):
        self.put("README.md", "mine\n")
        self.put("manifest.json", '{"id": "DEMO", "custom": true}\n')
        self.apply()
        self.assertEqual(self.text("README.md"), "mine\n")
        self.assertIn('"custom"', self.text("manifest.json"))

    def test_an_existing_readme_in_another_format_blocks_readme_md(self):
        self.put("README.adoc", "= Demo\n")
        plan = self.plan()
        self.assertEqual(self.actions(plan)["README.md"], "exists-alternative")
        self.apply()
        self.assertFalse((self.repo / "README.md").exists())

    def test_licence_detail_says_whether_the_text_is_standard(self):
        standard = (self.set_dir / "assets/templates/license-cc-by-sa-3.0.txt").read_text(encoding="utf-8")
        self.put("LICENSE", standard)
        detail = {a.target: a.detail for a in self.plan().acts}["LICENSE"]
        self.assertIn("matches the standard cc-by-sa-3.0", detail)
        self.put("LICENSE", standard + "\nextra\n")
        detail = {a.target: a.detail for a in self.plan().acts}["LICENSE"]
        self.assertIn("differs", detail)

    def test_json_merge_adds_missing_keys_and_keeps_existing_values(self):
        self.put(".claude/settings.json", json.dumps({
            "permissions": {"allow": ["Bash(make *)"], "deny": ["Bash(rm *)"]},
            "enabledPlugins": {"superpowers@claude-plugins-official": False}}))
        plan = self.plan()
        self.assertEqual(self.actions(plan)[".claude/settings.json"], "merge")
        self.apply()
        merged = json.loads(self.text(".claude/settings.json"))
        self.assertFalse(merged["enabledPlugins"]["superpowers@claude-plugins-official"])  # existing value wins
        self.assertTrue(merged["enabledPlugins"]["openehr-specs@openehr"])
        self.assertIn("Bash(make *)", merged["permissions"]["allow"])
        self.assertIn("WebFetch(domain:specifications.openehr.org)", merged["permissions"]["allow"])
        self.assertEqual(merged["permissions"]["deny"], ["Bash(rm *)"])
        self.assertEqual(merged["extraKnownMarketplaces"]["openehr"]["source"]["repo"], "openEHR/ai-plugins")
        self.assertEqual(self.actions(self.plan())[".claude/settings.json"], "unchanged")

    def test_json_merge_reports_invalid_json_instead_of_overwriting(self):
        self.put(".claude/settings.json", "{ not json")
        self.assertEqual(self.actions(self.plan())[".claude/settings.json"], "conflict")
        self.apply()
        self.assertEqual(self.text(".claude/settings.json"), "{ not json")

    def test_ensure_lines_appends_only_what_is_missing(self):
        self.put(".gitignore", "*.bak\n\nbuild/\n")
        plan = self.plan()
        self.assertEqual(self.actions(plan)[".gitignore"], "merge")
        self.apply()
        lines = self.text(".gitignore").splitlines()
        self.assertEqual(lines.count("*.bak"), 1)
        self.assertIn("build/", lines)
        self.assertIn(".claude/settings.local.json", lines)
        self.assertIn("# Git worktrees (isolated feature checkouts)", lines)
        self.assertEqual(self.actions(self.plan())[".gitignore"], "unchanged")

    def test_ensure_lines_by_key_does_not_duplicate_a_differing_attribute(self):
        self.put(".asciidoctorconfig", ":component: OTHER\n\n:diagrams_uri: ./diagrams")
        self.assertEqual(self.plan().values["component"], "OTHER")  # inferred from the file itself
        plan = self.plan(component="DEMO")  # an explicit value disagrees with the file
        self.assertEqual(self.actions(plan)[".asciidoctorconfig"], "merge")
        self.assertTrue(any("OTHER" in w for w in plan.warnings))
        self.apply(component="DEMO")
        text = self.text(".asciidoctorconfig")
        self.assertEqual(text.count(":component:"), 1)
        self.assertIn(":imagesdir: ../", text)
        self.assertIn(":diagrams_uri: ./diagrams", text)

    def test_whole_file_edited_locally_is_a_conflict_until_overwritten(self):
        self.apply()
        self.put(".claude/CLAUDE.md", "my own\n")
        self.assertEqual(self.actions(self.plan())[".claude/CLAUDE.md"], "conflict")
        self.apply()
        self.assertEqual(self.text(".claude/CLAUDE.md"), "my own\n")
        self.apply(overwrite=["claude-md"])
        self.assertIn("@../AGENTS.md", self.text(".claude/CLAUDE.md"))

    def test_pinned_files_are_left_alone_and_the_pin_is_remembered(self):
        self.apply()
        self.put(".claude/CLAUDE.md", "my own\n")
        self.apply(pin=["claude-md"])
        self.assertEqual(self.actions(self.plan())[".claude/CLAUDE.md"], "pinned")
        self.assertEqual(json.loads(self.text(".claude/scaffold.json"))["pinned"], ["claude-md"])


class RegionTests(Base):
    def region_actions(self, plan):
        agents = next(a for a in plan.acts if a.id == "agents")
        return {r["region"]: r["action"] for r in agents.extra.get("regions", [])}

    def test_text_outside_regions_is_never_touched(self):
        self.apply()
        self.put("AGENTS.md", self.text("AGENTS.md").replace("# AGENTS.md", "# AGENTS.md\n\nMy intro."))
        plan = self.plan()
        self.assertEqual(self.actions(plan)["AGENTS.md"], "unchanged")
        self.apply()
        self.assertIn("My intro.", self.text("AGENTS.md"))

    def test_an_edited_region_is_a_conflict_and_is_kept(self):
        self.apply()
        self.put("AGENTS.md", self.text("AGENTS.md").replace("understood, but use the leading form", "tolerated"))
        plan = self.plan()
        self.assertEqual(self.region_actions(plan)["conventions"], "conflict")
        self.assertEqual(self.actions(plan)["AGENTS.md"], "conflict")
        self.apply()
        self.assertIn("tolerated", self.text("AGENTS.md"))
        self.apply(overwrite=["agents:conventions"])
        self.assertNotIn("tolerated", self.text("AGENTS.md"))

    def test_a_region_pinned_by_id_stays_quiet(self):
        self.apply()
        self.put("AGENTS.md", self.text("AGENTS.md").replace("understood, but use the leading form", "tolerated"))
        self.assertEqual(self.region_actions(self.plan(pin=["agents:conventions"]))["conventions"], "pinned")

    def test_a_region_the_user_deleted_is_not_added_back(self):
        self.apply()
        text = self.text("AGENTS.md")
        start = text.index("<!-- openehr-scaffold:begin build -->")
        end = text.index("<!-- openehr-scaffold:end build -->") + len("<!-- openehr-scaffold:end build -->")
        self.put("AGENTS.md", text[:start] + text[end:])
        self.assertEqual(self.region_actions(self.plan())["build"], "removed")

    def test_a_region_that_was_never_recorded_is_added(self):
        self.apply()
        text = self.text("AGENTS.md")
        start = text.index("<!-- openehr-scaffold:begin build -->")
        end = text.index("<!-- openehr-scaffold:end build -->") + len("<!-- openehr-scaffold:end build -->")
        self.put("AGENTS.md", text[:start] + text[end:])
        desc = json.loads(self.text(".claude/scaffold.json"))
        del desc["files"]["agents"]["regions"]["build"]
        self.put(".claude/scaffold.json", json.dumps(desc))
        self.assertEqual(self.region_actions(self.plan())["build"], "add")
        self.apply()
        self.assertIn("<!-- openehr-scaffold:begin build -->", self.text("AGENTS.md"))

    def test_an_agents_file_without_markers_is_left_for_a_manual_merge(self):
        self.put("AGENTS.md", "# AGENTS.md\n\nhand written\n")
        plan = self.plan()
        self.assertEqual(self.actions(plan)["AGENTS.md"], "upgrade-manual")
        self.apply()
        self.assertEqual(self.text("AGENTS.md"), "# AGENTS.md\n\nhand written\n")
        self.assertEqual(scaffold.public(self.plan(pin=["agents"]))["files"][0]["action"], "pinned")


class UpgradeTests(Base):
    def edit_conventions(self, dst):
        path = dst / "assets/templates/agents-md.tmpl"
        path.write_text(path.read_text(encoding="utf-8").replace("one line, for example", "a single line, for example"),
                        encoding="utf-8")

    def test_a_template_change_updates_untouched_regions_and_reports_edited_ones(self):
        self.apply()
        self.put("AGENTS.md", self.text("AGENTS.md").replace("# AGENTS.md", "# AGENTS.md\n\nMy intro."))
        new_set = self.copy_set()
        rev = self.bump(new_set, edit=self.edit_conventions)
        self.set_dir = new_set
        plan = self.plan()
        self.assertEqual((plan.mode, plan.path), ("upgrade", [rev]))
        self.assertEqual(self.actions(plan)["AGENTS.md"], "update")
        self.apply()
        agents = self.text("AGENTS.md")
        self.assertIn("a single line, for example", agents)
        self.assertIn("My intro.", agents)
        self.assertEqual(json.loads(self.text(".claude/scaffold.json"))["revision"], rev)
        self.assertEqual(self.plan().mode, "current")

    def test_a_template_change_conflicts_with_a_locally_edited_region(self):
        self.apply()
        self.put("AGENTS.md", self.text("AGENTS.md").replace("understood, but use the leading form", "tolerated"))
        new_set = self.copy_set()
        rev = self.bump(new_set, edit=self.edit_conventions)
        self.set_dir = new_set
        agents = next(a for a in self.plan().acts if a.id == "agents")
        self.assertEqual(agents.action, "conflict")
        self.apply()
        self.assertIn("tolerated", self.text("AGENTS.md"))  # kept
        self.assertEqual(self.plan().recorded, rev)

    def test_the_path_chains_every_revision_between_recorded_and_latest(self):
        self.apply()
        new_set = self.copy_set()
        first = self.bump(new_set, steps=[{"op": "note", "text": "two"}])
        second = self.bump(new_set, steps=[{"op": "note", "text": "three"}])
        self.set_dir = new_set
        plan = self.plan()
        self.assertEqual(plan.path, [first, second])
        self.assertEqual([(s["revision"], s["text"]) for s in plan.steps], [(first, "two"), (second, "three")])

    def test_rename_moves_the_file_and_keeps_its_recorded_hash(self):
        self.apply()
        new_set = self.copy_set()

        def move_target(dst):
            path = dst / "assets/template-set.json"
            tset = json.loads(path.read_text(encoding="utf-8"))
            for spec in tset["files"]:
                if spec["id"] == "claude-md":
                    spec["target"] = ".claude/CLAUDE-OLD.md"
            path.write_text(json.dumps(tset, indent=2), encoding="utf-8")

        self.bump(new_set, steps=[{"op": "rename", "from": ".claude/CLAUDE.md", "to": ".claude/CLAUDE-OLD.md"}],
                  edit=move_target)
        self.set_dir = new_set
        result = self.apply()
        self.assertFalse((self.repo / ".claude/CLAUDE.md").exists())
        self.assertTrue((self.repo / ".claude/CLAUDE-OLD.md").exists())
        self.assertEqual(result["migration_steps"][0]["result"], "done")
        self.assertEqual(self.actions(self.plan())[".claude/CLAUDE-OLD.md"], "unchanged")

    def test_delete_only_removes_a_file_that_is_unmodified(self):
        self.apply()
        new_set = self.copy_set()
        self.bump(new_set, steps=[{"op": "delete", "path": ".claude/CLAUDE.md", "file_id": "claude-md"}])
        self.set_dir = new_set
        self.put(".claude/CLAUDE.md", "edited\n")
        result = self.apply(overwrite=[])
        step = result["migration_steps"][0]
        self.assertTrue(step["result"].startswith("skipped"))
        self.assertTrue((self.repo / ".claude/CLAUDE.md").exists())

    def test_a_missing_migration_file_is_an_error(self):
        self.apply()
        new_set = self.copy_set()
        rev = self.bump(new_set)
        (new_set / f"migrations/{rev:04d}.json").unlink()
        self.set_dir = new_set
        with self.assertRaises(scaffold.ScaffoldError):
            self.plan()

    def test_a_descriptor_newer_than_the_plugin_is_an_error(self):
        self.apply()
        desc = json.loads(self.text(".claude/scaffold.json"))
        desc["revision"] = 9
        self.put(".claude/scaffold.json", json.dumps(desc))
        with self.assertRaises(scaffold.ScaffoldError):
            self.plan()

    def test_a_descriptor_from_another_template_set_is_an_error(self):
        self.apply()
        desc = json.loads(self.text(".claude/scaffold.json"))
        desc["template_set"] = "someone/else"
        self.put(".claude/scaffold.json", json.dumps(desc))
        with self.assertRaises(scaffold.ScaffoldError):
            self.plan()

    def test_upgrade_mode_when_files_exist_but_there_is_no_descriptor(self):
        self.put(".gitignore", "*.bak\n")
        plan = self.plan()
        self.assertEqual((plan.mode, plan.recorded, plan.path), ("upgrade", None, []))


class CheckTests(Base):
    def test_the_shipped_template_set_is_sound(self):
        self.assertEqual(scaffold.check_template_set(scaffold.SET_DIR), [])

    def test_a_template_edit_without_a_new_revision_is_flagged(self):
        dst = self.copy_set()
        path = dst / "assets/templates/gitignore.tmpl"
        path.write_text(path.read_text(encoding="utf-8") + "\nextra/\n", encoding="utf-8")
        problems = scaffold.check_template_set(dst)
        self.assertTrue(any("without a new revision" in p for p in problems))

    def test_sealing_after_a_revision_bump_makes_it_sound_again(self):
        dst = self.copy_set()
        self.bump(dst)
        self.assertEqual(scaffold.check_template_set(dst), [])

    def test_a_revision_without_its_migration_file_is_flagged(self):
        dst = self.copy_set()
        rev = self.bump(dst)
        (dst / f"migrations/{rev:04d}.json").unlink()
        self.assertTrue(any(f"{rev:04d}.json" in p for p in scaffold.check_template_set(dst)))

    def test_a_missing_template_and_a_broken_template_are_flagged(self):
        dst = self.copy_set()
        (dst / "assets/templates/readme-md.tmpl").unlink()
        self.assertTrue(any("readme-md.tmpl" in p for p in scaffold.check_template_set(dst)))
        dst = self.copy_set()
        path = dst / "assets/templates/claude-md.tmpl"
        path.write_text("{{#if a}}{{#if b}}x{{/if}}{{/if}}", encoding="utf-8")
        self.assertTrue(any("claude-md" in p for p in scaffold.check_template_set(dst)))

    def test_unbalanced_region_markers_are_flagged(self):
        dst = self.copy_set()
        path = dst / "assets/templates/agents-md.tmpl"
        path.write_text(path.read_text(encoding="utf-8").replace("<!-- openehr-scaffold:end plugin -->", ""),
                        encoding="utf-8")
        self.assertTrue(any("agents" in p for p in scaffold.check_template_set(dst)))


class DiffTests(Base):
    def run_diff(self, file_id):
        return scaffold.diff_file(self.repo, self.set_dir, dict(TITLE), file_id)

    def test_a_missing_file_is_reported(self):
        self.assertIn("does not exist yet", self.run_diff("claude-md"))

    def test_identical_content_has_no_differences(self):
        self.apply()
        self.assertEqual(self.run_diff("claude-md"), "no differences\n")
        self.assertEqual(self.run_diff("agents"), "no differences\n")

    def test_a_whole_file_diff_labels_both_sides(self):
        self.apply()
        self.put(".claude/CLAUDE.md", "my own\n")
        out = self.run_diff("claude-md")
        self.assertIn("(repo)", out)
        self.assertIn("(template)", out)
        self.assertIn("-my own", out)

    def test_a_regions_diff_shows_only_the_regions_that_differ(self):
        self.apply()
        self.put("AGENTS.md", self.text("AGENTS.md").replace("understood, but use the leading form", "tolerated"))
        out = self.run_diff("agents")
        self.assertIn("[region conventions]", out)
        self.assertNotIn("[region plugin]", out)
        self.assertIn("+- Some history", out)

    def test_an_unmarked_agents_file_is_compared_as_a_whole(self):
        self.put("AGENTS.md", "# AGENTS.md\n\nhand written\n")
        out = self.run_diff("agents")
        self.assertIn("-hand written", out)

    def test_unknown_ids_and_missing_variables_are_errors(self):
        with self.assertRaises(scaffold.ScaffoldError):
            self.run_diff("nope")
        with self.assertRaises(scaffold.ScaffoldError):
            scaffold.diff_file(self.repo, self.set_dir, {}, "agents")


class HardeningTests(Base):
    def test_a_conflicting_region_does_not_block_a_clean_one_in_the_same_file(self):
        self.apply()
        self.put("AGENTS.md", self.text("AGENTS.md").replace("understood, but use the leading form", "tolerated"))

        def edit(dst):
            path = dst / "assets/templates/agents-md.tmpl"
            text = path.read_text(encoding="utf-8")
            text = text.replace("Docker is all you need", "Docker is all it takes")
            text = text.replace("one line, for example", "a single line, for example")
            path.write_text(text, encoding="utf-8")

        new_set = self.copy_set()
        self.bump(new_set, edit=edit)
        self.set_dir = new_set
        plan = self.plan()
        agents = next(a for a in plan.acts if a.id == "agents")
        regions = {r["region"]: r["action"] for r in agents.extra["regions"]}
        self.assertEqual((agents.action, regions["build"], regions["conventions"]), ("conflict", "update", "conflict"))
        self.apply()
        text = self.text("AGENTS.md")
        self.assertIn("Docker is all it takes", text)     # clean region written
        self.assertIn("tolerated", text)                  # conflicting region kept
        self.assertNotIn("a single line, for example", text)

    def test_invalid_settings_json_can_be_replaced_with_overwrite(self):
        self.put(".claude/settings.json", "{ not json")
        self.assertEqual(self.actions(self.plan())[".claude/settings.json"], "conflict")
        self.assertIn("--overwrite claude-settings", {a.target: a.detail for a in self.plan().acts}[".claude/settings.json"])
        self.apply(overwrite=["claude-settings"])
        self.assertTrue(json.loads(self.text(".claude/settings.json"))["enabledPlugins"]["openehr-specs@openehr"])

    def test_bmm_schemas_are_ordered_by_version_not_by_text(self):
        for name in ("openehr_am_1.4.0", "openehr_am_1.9.0", "openehr_am_1.10.0"):
            self.put(f"computable/BMM/{name}.bmm.json", "{}")
        plan = self.plan()
        self.assertEqual(plan.values["bmm_schema_id"], "openehr_am_1.10.0")
        self.assertTrue(any("several BMM schemas" in w and "1.9.0" in w for w in plan.warnings))
        self.assertEqual(self.plan(bmm_schema_id="openehr_am_1.4.0").values["bmm_schema_id"], "openehr_am_1.4.0")

    def test_a_single_bmm_schema_gives_no_warning(self):
        self.put("computable/BMM/openehr_demo_1.0.0.bmm.json", "{}")
        self.base_clone("openehr_base_1.3.0")  # without it, the missing BASE dependency is reported
        self.assertFalse(any("BMM" in w for w in self.plan().warnings))

    def test_git_warnings_distinguish_the_cases(self):
        self.assertTrue(any("not a git repository" in w for w in scaffold.public(self.plan())["warnings"]))
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        warnings = scaffold.public(self.plan())["warnings"]
        self.assertTrue(any("inside the git repository" in w and "repository root" in w for w in warnings))
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        warnings = scaffold.public(self.plan())["warnings"]
        self.assertFalse(any("not a git repository" in w or "inside the git repository" in w for w in warnings))

    def test_a_dirty_tree_is_mentioned(self):
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        self.put("notes.txt", "x")
        self.assertTrue(any("uncommitted" in w for w in scaffold.public(self.plan())["warnings"]))

    def test_malformed_migration_steps_are_rejected_with_a_clean_error(self):
        self.apply()
        for step in ({"op": "rename", "to": "x"}, {"op": "delete"}, {"op": "note"}, {"op": "explode"}):
            new_set = self.copy_set()
            self.bump(new_set, steps=[step])
            self.set_dir = new_set
            with self.assertRaises(scaffold.ScaffoldError, msg=step):
                self.plan()
            self.assertTrue(scaffold.check_template_set(new_set), step)  # check reports it too

    def test_migration_paths_cannot_leave_the_repository(self):
        self.apply()
        for step in ({"op": "rename", "from": "a", "to": "../outside"},
                     {"op": "delete", "path": "/etc/passwd"}):
            new_set = self.copy_set()
            self.bump(new_set, steps=[step])
            self.set_dir = new_set
            with self.assertRaises(scaffold.ScaffoldError, msg=step):
                self.plan()

    def test_check_rejects_a_target_outside_the_repository(self):
        dst = self.copy_set()
        path = dst / "assets/template-set.json"
        tset = json.loads(path.read_text(encoding="utf-8"))
        tset["files"][0]["target"] = "../escape.md"
        path.write_text(json.dumps(tset, indent=2), encoding="utf-8")
        self.assertTrue(any("relative path" in p for p in scaffold.check_template_set(dst)))


class FidelityTests(Base):
    def put_bytes(self, name, data):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def test_crlf_files_keep_their_line_endings_when_merged(self):
        self.put_bytes(".gitignore", b"*.bak\r\nbuild/\r\n")
        self.apply()
        data = (self.repo / ".gitignore").read_bytes()
        self.assertTrue(data.startswith(b"*.bak\r\nbuild/\r\n"))
        self.assertNotIn(b"\n", data.replace(b"\r\n", b""))   # every newline is CRLF
        self.assertIn(b".claude/settings.local.json", data)

    def test_lf_files_stay_lf_and_new_files_are_lf(self):
        self.put_bytes(".gitignore", b"*.bak\n")
        self.apply()
        self.assertNotIn(b"\r", (self.repo / ".gitignore").read_bytes())
        self.assertNotIn(b"\r", (self.repo / "AGENTS.md").read_bytes())

    def test_a_crlf_region_file_gets_the_region_update_in_crlf(self):
        self.apply()
        text = self.text("AGENTS.md").replace("\n", "\r\n")
        self.put_bytes("AGENTS.md", text.encode("utf-8"))
        self.assertEqual(self.actions(self.plan())["AGENTS.md"], "unchanged")   # CRLF never causes a conflict
        new_set = self.copy_set()
        self.bump(new_set, edit=lambda dst: (dst / "assets/templates/agents-md.tmpl").write_text(
            (dst / "assets/templates/agents-md.tmpl").read_text(encoding="utf-8").replace(
                "one line, for example", "a single line, for example"), encoding="utf-8"))
        self.set_dir = new_set
        self.apply()
        data = (self.repo / "AGENTS.md").read_bytes()
        self.assertIn(b"a single line, for example", data)
        self.assertNotIn(b"\n", data.replace(b"\r\n", b""))

    def test_the_file_mode_survives_a_rewrite(self):
        self.put(".gitignore", "*.bak\n")
        os.chmod(self.repo / ".gitignore", 0o755)
        self.apply()
        self.assertEqual((self.repo / ".gitignore").stat().st_mode & 0o777, 0o755)

    def test_a_byte_order_mark_does_not_hide_a_line(self):
        self.put_bytes(".gitignore", "\ufeff*.bak\nbuild/\n".encode("utf-8"))
        self.apply()
        self.assertEqual(self.text(".gitignore").count("*.bak"), 1)

    def test_no_temporary_files_are_left_behind(self):
        self.apply()
        self.assertEqual(list(self.repo.rglob("*.scaffold-tmp")), [])

    def test_symbolic_links_are_never_written_through(self):
        self.put("AGENTS.md", "# keep me\n")
        (self.repo / ".claude").mkdir()
        (self.repo / ".claude" / "CLAUDE.md").symlink_to("../AGENTS.md")
        plan = self.plan()
        self.assertEqual(self.actions(plan)[".claude/CLAUDE.md"], "conflict")
        self.apply(overwrite=["claude-md"], pin=["agents"])
        self.assertEqual(self.text("AGENTS.md"), "# keep me\n")
        self.assertTrue((self.repo / ".claude" / "CLAUDE.md").is_symlink())


class MarkerTests(Base):
    def test_a_begin_marker_without_an_end_stops_the_run_and_names_the_file(self):
        self.apply()
        text = self.text("AGENTS.md").replace("<!-- openehr-scaffold:end conventions -->", "")
        self.put("AGENTS.md", text)
        with self.assertRaises(scaffold.ScaffoldError) as caught:
            self.plan()
        self.assertIn("AGENTS.md", str(caught.exception))
        self.assertIn("conventions", str(caught.exception))
        with self.assertRaises(scaffold.ScaffoldError):
            self.apply(overwrite=["agents:conventions"])
        self.assertEqual(self.text("AGENTS.md"), text)   # nothing was touched

    def test_a_duplicated_region_in_the_repo_names_the_file(self):
        self.apply()
        text = self.text("AGENTS.md")
        start = text.index("<!-- openehr-scaffold:begin plugin -->")
        end = text.index("<!-- openehr-scaffold:end plugin -->") + len("<!-- openehr-scaffold:end plugin -->")
        self.put("AGENTS.md", text + "\n" + text[start:end] + "\n")
        with self.assertRaises(scaffold.ScaffoldError) as caught:
            self.plan()
        self.assertIn("AGENTS.md", str(caught.exception))

    def test_markers_that_are_not_at_the_start_of_a_line_are_ignored(self):
        self.put("AGENTS.md", "# AGENTS.md\n\nSee `<!-- openehr-scaffold:begin plugin -->` in the docs.\n")
        self.assertEqual(self.actions(self.plan())["AGENTS.md"], "upgrade-manual")

    def test_pinning_a_missing_region_stops_it_being_added(self):
        self.apply()
        text = self.text("AGENTS.md")
        start = text.index("<!-- openehr-scaffold:begin build -->")
        end = text.index("<!-- openehr-scaffold:end build -->") + len("<!-- openehr-scaffold:end build -->")
        desc = json.loads(self.text(".claude/scaffold.json"))
        del desc["files"]["agents"]["regions"]["build"]
        self.put(".claude/scaffold.json", json.dumps(desc))
        self.put("AGENTS.md", text[:start] + text[end:])
        plan = self.plan(pin=["agents:build"])
        agents = next(a for a in plan.acts if a.id == "agents")
        self.assertEqual({r["region"]: r["action"] for r in agents.extra["regions"]}["build"], "pinned")
        self.assertIsNone(agents.content)

    def test_overwrite_brings_back_a_region_the_user_deleted(self):
        self.apply()
        text = self.text("AGENTS.md")
        start = text.index("<!-- openehr-scaffold:begin build -->")
        end = text.index("<!-- openehr-scaffold:end build -->") + len("<!-- openehr-scaffold:end build -->")
        self.put("AGENTS.md", text[:start] + text[end:])
        self.assertIsNone(next(a for a in self.plan().acts if a.id == "agents").content)   # removed: left out
        self.apply(overwrite=["agents:build"])
        self.assertIn("<!-- openehr-scaffold:begin build -->", self.text("AGENTS.md"))


class RemovalTests(Base):
    def test_items_the_user_removed_from_settings_are_not_added_back(self):
        self.apply()
        settings = json.loads(self.text(".claude/settings.json"))
        settings["permissions"]["allow"].remove("Bash(git commit *)")
        del settings["enabledPlugins"]["superpowers@claude-plugins-official"]
        self.put(".claude/settings.json", json.dumps(settings, indent=2))
        plan = self.plan()
        act = next(a for a in plan.acts if a.id == "claude-settings")
        self.assertEqual(act.action, "unchanged")
        self.assertIn("removed earlier", act.detail)
        self.apply()
        after = json.loads(self.text(".claude/settings.json"))
        self.assertNotIn("Bash(git commit *)", after["permissions"]["allow"])
        self.assertNotIn("superpowers@claude-plugins-official", after["enabledPlugins"])

    def test_a_new_template_item_is_added_even_after_other_items_were_removed(self):
        self.apply()
        settings = json.loads(self.text(".claude/settings.json"))
        settings["permissions"]["allow"].remove("Bash(git commit *)")
        self.put(".claude/settings.json", json.dumps(settings))

        def edit(dst):
            path = dst / "assets/templates/claude-settings.json.tmpl"
            path.write_text(path.read_text(encoding="utf-8").replace(
                '"Bash(git add *)",', '"Bash(git add *)",\n      "Bash(git status *)",'), encoding="utf-8")

        new_set = self.copy_set()
        self.bump(new_set, edit=edit)
        self.set_dir = new_set
        self.apply()
        allow = json.loads(self.text(".claude/settings.json"))["permissions"]["allow"]
        self.assertIn("Bash(git status *)", allow)
        self.assertNotIn("Bash(git commit *)", allow)

    def test_a_removed_gitignore_line_stays_removed_but_a_new_one_is_added(self):
        self.apply()
        self.put(".gitignore", self.text(".gitignore").replace(".idea/\n", ""))
        act = next(a for a in self.plan().acts if a.id == "gitignore")
        self.assertEqual(act.action, "unchanged")
        self.assertIn("removed earlier", act.detail)

        def edit(dst):
            path = dst / "assets/templates/gitignore.tmpl"
            path.write_text(path.read_text(encoding="utf-8") + "\n# Build output\nout/\n", encoding="utf-8")

        new_set = self.copy_set()
        self.bump(new_set, edit=edit)
        self.set_dir = new_set
        self.apply()
        lines = self.text(".gitignore").splitlines()
        self.assertIn("out/", lines)
        self.assertNotIn(".idea/", lines)

    def test_an_unset_attribute_counts_as_present(self):
        self.put(".asciidoctorconfig", ":component: DEMO\n\n:package_qualifiers!:\n")
        self.apply(component="DEMO")
        self.assertNotIn("\n:package_qualifiers:", self.text(".asciidoctorconfig"))

    def test_an_existing_licence_in_another_file_name_blocks_a_second_one(self):
        self.put("LICENSE.md", "my licence\n")
        self.assertEqual(self.actions(self.plan())["LICENSE"], "exists-alternative")


class VariableTests(Base):
    def test_a_bmm_schema_added_after_scaffolding_is_picked_up_as_a_guess(self):
        self.apply()
        self.put("computable/BMM/openehr_demo_1.0.0.bmm.json", "{}")
        plan = self.plan()
        self.assertEqual(plan.values["bmm_schema_id"], "openehr_demo_1.0.0")
        self.assertTrue(plan.sources["bmm_schema_id"].startswith("inferred"))

    def test_confirmed_values_are_not_overridden_by_inference(self):
        self.apply(default_branch="main")
        self.assertEqual(self.plan().sources["default_branch"], "descriptor")

    def test_unknown_variable_names_are_an_error(self):
        with self.assertRaises(scaffold.ScaffoldError) as caught:
            self.plan(colour="red")
        self.assertIn("colour", str(caught.exception))
        with self.assertRaises(scaffold.ScaffoldError):
            self.plan(license_name="x")   # derived: cannot be set

    def test_an_empty_required_value_counts_as_missing(self):
        plan = scaffold.build_plan(self.repo, self.set_dir, {"component_title": "  "})
        self.assertEqual([m["name"] for m in plan.missing], ["component_title"])

    def test_unknown_overwrite_and_pin_ids_are_an_error(self):
        with self.assertRaises(scaffold.ScaffoldError):
            self.plan(pin=["agnts"])
        with self.assertRaises(scaffold.ScaffoldError):
            self.plan(overwrite=["agents:nope"])
        self.assertTrue(self.plan(pin=["agents:plugin"]))

    def test_apply_writes_nothing_when_input_is_missing(self):
        result = scaffold.apply_plan(self.repo, self.set_dir, {}, (), ())
        self.assertEqual(result["status"], "needs_input")
        self.assertNotIn("applied", result)
        self.assertEqual(list(self.repo.iterdir()), [])

    def test_plan_writes_nothing_in_upgrade_mode(self):
        self.put(".gitignore", "*.bak\n")
        before = sorted(p.name for p in self.repo.rglob("*"))
        self.plan()
        self.assertEqual(sorted(p.name for p in self.repo.rglob("*")), before)

    def test_a_conflict_is_still_a_conflict_after_apply(self):
        self.apply()
        self.put(".claude/CLAUDE.md", "my own\n")
        self.apply()
        self.assertEqual(self.actions(self.plan())[".claude/CLAUDE.md"], "conflict")


class MalformedInputTests(Base):
    def test_settings_json_that_is_not_an_object_is_a_conflict_not_a_crash(self):
        for body in ("[]", "null", '"text"', "3"):
            self.put(".claude/settings.json", body)
            self.assertEqual(self.actions(self.plan())[".claude/settings.json"], "conflict", body)
        self.apply(overwrite=["claude-settings"])
        self.assertIsInstance(json.loads(self.text(".claude/settings.json")), dict)

    def test_a_file_that_is_not_utf8_names_the_file(self):
        (self.repo / ".gitignore").write_bytes("*.bak\n".encode("utf-16"))
        with self.assertRaises(scaffold.ScaffoldError) as caught:
            self.plan()
        self.assertIn(".gitignore", str(caught.exception))
        self.assertIn("UTF-8", str(caught.exception))

    def test_a_pinned_file_is_never_read(self):
        (self.repo / ".gitignore").write_bytes("*.bak\n".encode("utf-16"))
        self.assertEqual(self.actions(self.plan(pin=["gitignore"]))[".gitignore"], "pinned")

    def test_a_licence_that_is_not_utf8_does_not_stop_inference(self):
        (self.repo / "LICENSE").write_bytes(b"caf\xe9 licence")
        self.assertEqual(self.plan().values["license"], "cc-by-sa-3.0")

    def test_odd_manifest_shapes_do_not_crash_inference(self):
        self.put("manifest.json", json.dumps({"id": "DEMO", "title": "Demo Model", "jira": [],
                                              "specifications": ["x", {"id": 7}, {"id": "ok"}]}))
        plan = scaffold.build_plan(self.repo, self.set_dir, {})
        self.assertEqual(plan.values["documents"], "`ok`")

    def test_a_hand_edited_descriptor_is_reported_cleanly(self):
        self.apply()
        for edit in ({"revision": "1"}, {"revision": 0}, {"files": []}, {"variables": "x"}, {"pinned": "agents"}):
            desc = json.loads(self.text(".claude/scaffold.json"))
            desc.update(edit)
            self.put(".claude/scaffold.json", json.dumps(desc))
            with self.assertRaises(scaffold.ScaffoldError, msg=edit):
                self.plan()
            desc = json.loads(json.dumps(desc))
        self.put(".claude/scaffold.json", "[1, 2]")
        with self.assertRaises(scaffold.ScaffoldError):
            self.plan()

    def test_the_cli_turns_any_failure_into_json_with_exit_code_2(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = scaffold.main(["plan", "--repo", str(self.repo), "--var", "component_title=T", "--var", "nope=1"])
        self.assertEqual(code, 2)
        self.assertIn("nope", json.loads(out.getvalue())["error"])
        with mock.patch.object(scaffold, "build_plan", side_effect=RuntimeError("boom")):
            out = io.StringIO()
            with redirect_stdout(out):
                code = scaffold.main(["plan", "--repo", str(self.repo)])
        self.assertEqual(code, 2)
        self.assertIn("boom", json.loads(out.getvalue())["error"])

    def test_check_reports_a_malformed_set_instead_of_crashing(self):
        dst = self.copy_set()
        path = dst / "assets/template-set.json"
        tset = json.loads(path.read_text(encoding="utf-8"))
        tset["revisions"] = []
        path.write_text(json.dumps(tset), encoding="utf-8")
        self.assertTrue(scaffold.check_template_set(dst))
        dst = self.copy_set()
        tset = json.loads((dst / "assets/template-set.json").read_text(encoding="utf-8"))
        tset["variables"]["license_name"]["derived"] = {}
        (dst / "assets/template-set.json").write_text(json.dumps(tset), encoding="utf-8")
        problems = scaffold.check_template_set(dst)
        self.assertTrue(problems and all(isinstance(p, str) for p in problems))


class MigrationStepTests(Base):
    def upgrade_with(self, steps):
        self.apply()
        new_set = self.copy_set()
        self.bump(new_set, steps=steps)
        self.set_dir = new_set

    def test_delete_removes_an_unmodified_scaffolded_file(self):
        self.upgrade_with([{"op": "delete", "path": ".claude/CLAUDE.md", "file_id": "claude-md"}])
        result = self.apply()
        self.assertEqual(result["migration_steps"][0]["result"], "done")

    def test_delete_and_rename_leave_a_pinned_file_alone(self):
        self.upgrade_with([{"op": "delete", "path": ".claude/CLAUDE.md", "file_id": "claude-md"},
                           {"op": "rename", "from": ".claude/CLAUDE.md", "to": ".claude/OLD.md", "file_id": "claude-md"}])
        result = self.apply(pin=["claude-md"])
        self.assertEqual([s["result"] for s in result["migration_steps"]], ["skipped: that file is pinned"] * 2)
        self.assertTrue((self.repo / ".claude/CLAUDE.md").exists())

    def test_rename_is_skipped_when_the_source_is_missing_or_the_target_exists(self):
        self.upgrade_with([{"op": "rename", "from": "nope.txt", "to": "x.txt"},
                           {"op": "rename", "from": "manifest.json", "to": "README.md"}])
        results = [s["result"] for s in self.apply()["migration_steps"]]
        self.assertEqual(results, ["skipped: source is missing", "skipped: target exists"])

    def test_a_note_is_reported_as_manual_and_a_delete_needs_a_file_id(self):
        self.upgrade_with([{"op": "note", "text": "do it by hand"}])
        self.assertEqual(self.apply()["migration_steps"][0]["result"], "manual: see note")
        new_set = self.copy_set()
        self.bump(new_set, steps=[{"op": "delete", "path": "x"}])
        self.assertTrue(scaffold.check_template_set(new_set))


class CliTests(Base):
    def run_cli(self, *args):
        out = io.StringIO()
        with redirect_stdout(out):
            code = scaffold.main(list(args))
        return code, out.getvalue()

    def test_plan_prints_json_and_writes_nothing(self):
        code, out = self.run_cli("plan", "--repo", str(self.repo), "--var", "component_title=Demo Model")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["status"], "ok")
        self.assertEqual(list(self.repo.iterdir()), [])

    def test_errors_are_json_with_exit_code_2(self):
        code, out = self.run_cli("plan", "--repo", str(self.repo / "nope"))
        self.assertEqual(code, 2)
        self.assertIn("error", json.loads(out))
        code, out = self.run_cli("plan", "--repo", str(self.repo), "--var", "broken")
        self.assertEqual(code, 2)

    def test_render_prints_one_file(self):
        code, out = self.run_cli("render", "--repo", str(self.repo), "--file", "claude-md",
                                 "--var", "component_title=Demo Model")
        self.assertEqual(code, 0)
        self.assertIn("@../AGENTS.md", out)

    def test_diff_prints_text(self):
        self.apply()
        code, out = self.run_cli("diff", "--repo", str(self.repo), "--file", "claude-md", "--var", "component_title=Demo Model")
        self.assertEqual((code, out), (0, "no differences\n"))

    def test_check_exit_code(self):
        code, out = self.run_cli("check")
        self.assertEqual((code, json.loads(out)["ok"]), (0, True))


BUNDLED = '{\n  "bmm_version": "2.4",\n  "rm_publisher": "openehr",\n  "schema_name": "demo"\n}\n'
BMM_GLOB = "computable/BMM/*.bmm.json"


class BmmTests(Base):
    """computable/BMM in a new repository: the schema the image bundles, else an empty one."""

    def bmm_act(self, plan):
        return next(a for a in plan.acts if a.id == "bmm")

    def test_the_highest_bundled_schema_of_the_component_is_copied(self):
        self.docker.schemas = {"openehr_demo_1.0.0": "{}", "openehr_demo_1.2.0": BUNDLED,
                               "openehr_demo_1.10.0-bmm3": "{}", "openehr_demox_9.0.0": "{}", "openehr_rm_1.2.0": "{}"}
        plan = self.plan()
        self.assertEqual((plan.values["bmm_schema_id"], plan.sources["bmm_schema_id"]),
                         ("openehr_demo_1.2.0", "inferred: bmm-publisher image"))
        self.assertIn("copied from ghcr.io/openehr/bmm-publisher", self.bmm_act(plan).detail)
        self.apply()
        self.assertEqual(self.text("computable/BMM/openehr_demo_1.2.0.bmm.json"), BUNDLED)
        self.assertIn("computable/BMM/openehr_demo_1.2.0.bmm.json", self.text("AGENTS.md"))
        self.assertIn(("run", "--rm", "--pull", "never", "--entrypoint", "ls",
                       "ghcr.io/openehr/bmm-publisher", "/app/resources"), self.docker.calls)

    def test_without_a_bundled_schema_an_empty_one_is_rendered(self):
        self.docker.schemas = {"openehr_rm_1.2.0": "{}"}
        self.base_clone("openehr_base_1.3.0")
        result = self.apply(first_release="1.0.0", component_title='Demo "Quoted" Model')
        self.assertIn("computable/BMM/openehr_demo_1.0.0.bmm.json", result["written"])
        schema = json.loads(self.text("computable/BMM/openehr_demo_1.0.0.bmm.json"))
        self.assertEqual({k: schema[k] for k in ("bmm_version", "rm_publisher", "schema_name", "rm_release",
                                                 "schema_revision", "schema_description")},
                         {"bmm_version": "2.4", "rm_publisher": "openehr", "schema_name": "demo",
                          "rm_release": "1.0.0", "schema_revision": "1.0.0.1",
                          "schema_description": 'openEHR Demo "Quoted" Model Component'})
        self.assertEqual(schema["includes"], {"openehr_base_1.3.0": {"id": "openehr_base_1.3.0"}})
        # bmm-publisher refuses a schema without a package
        self.assertEqual(schema["packages"], {"org.openehr.demo": {"name": "org.openehr.demo", "classes": []}})
        self.assertEqual(schema["class_definitions"], {})
        self.assertIn("  -d /in/openehr_base_1.3.0.bmm.json \\\n", self.text("AGENTS.md"))
        self.assertEqual(self.bmm_act(self.plan()).action, "exists")

    def test_without_a_base_clone_the_empty_schema_includes_nothing(self):
        self.docker.schemas = {}
        plan = self.plan()
        self.assertTrue(any("no sibling specifications-BASE" in w for w in plan.warnings))
        self.assertNotIn("includes", json.loads(self.bmm_act(plan).content))

    def test_without_docker_the_schema_is_blocked_and_the_rest_is_written(self):
        plan = self.plan()
        act = self.bmm_act(plan)
        self.assertEqual((act.action, act.target), ("blocked", BMM_GLOB))
        self.assertIn("(docker is not installed)", act.detail)
        self.assertIn("docker pull ghcr.io/openehr/bmm-publisher", act.detail)
        self.assertIn("--var bmm_schema_id=openehr_demo_0.1.0", act.detail)
        self.assertEqual(plan.values["bmm_schema_id"], "")
        result = self.apply()
        self.assertFalse((self.repo / "computable").exists())
        self.assertIn("AGENTS.md", result["written"])
        self.assertNotIn("class-generation", self.text("AGENTS.md"))

    def test_a_given_schema_id_creates_an_empty_schema_without_docker(self):
        act = self.bmm_act(self.plan(bmm_schema_id="openehr_demo_2.0.0"))
        self.assertEqual((act.action, act.target), ("create", "computable/BMM/openehr_demo_2.0.0.bmm.json"))
        self.assertIn("was not checked for a bundled copy (docker is not installed)", act.detail)
        self.assertEqual(json.loads(act.content)["rm_release"], "2.0.0")

    def test_a_given_schema_id_is_copied_when_the_image_bundles_it_and_rendered_when_not(self):
        self.docker.schemas = {"openehr_demo_1.0.0": BUNDLED, "openehr_demo_1.2.0": "{}"}
        act = self.bmm_act(self.plan(bmm_schema_id="openehr_demo_1.0.0"))
        self.assertEqual((act.action, act.content), ("create", BUNDLED))
        act = self.bmm_act(self.plan(bmm_schema_id="openehr_demo_3.0.0"))
        self.assertEqual(json.loads(act.content)["schema_revision"], "3.0.0.1")
        self.assertIn("bundles openehr_demo_1.0.0, openehr_demo_1.2.0, not openehr_demo_3.0.0", act.detail)

    def test_an_unreadable_bundled_copy_blocks_instead_of_being_written(self):
        self.docker.schemas = {"openehr_demo_1.0.0": "not json"}
        act = self.bmm_act(self.plan())
        self.assertEqual(act.action, "blocked")
        self.assertIn("not valid JSON", act.detail)

    def test_an_existing_repository_is_not_offered_one_and_docker_is_not_asked(self):
        self.put("README.md", "# demo\n")
        self.docker.schemas = {}
        plan = self.plan()
        self.assertEqual(plan.mode, "upgrade")
        act = self.bmm_act(plan)
        self.assertEqual((act.action, act.target), ("skipped", BMM_GLOB))
        self.assertIn("--overwrite bmm", act.detail)
        self.assertEqual((plan.values["bmm_schema_id"], self.docker.calls), ("", []))

    def test_overwrite_offers_one_to_an_existing_repository(self):
        self.put("README.md", "# demo\n")
        self.docker.schemas = {}
        self.apply(overwrite=("bmm",))
        self.assertTrue((self.repo / "computable/BMM/openehr_demo_0.1.0.bmm.json").is_file())

    def test_a_schema_already_in_computable_bmm_is_left_alone(self):
        self.put("computable/BMM/openehr_demo_1.0.0.bmm.json", "{}")
        self.docker.schemas = {"openehr_demo_1.2.0": BUNDLED}
        act = self.bmm_act(self.plan())
        self.assertEqual((act.action, act.detail), ("exists", "openehr_demo_1.0.0.bmm.json"))
        self.assertEqual(self.docker.calls, [])

    def test_a_pinned_schema_is_not_created_and_docker_is_not_asked(self):
        self.docker.schemas = {}
        plan = self.plan(pin=("bmm",))
        self.assertEqual((self.bmm_act(plan).action, self.bmm_act(plan).target), ("pinned", BMM_GLOB))
        self.assertEqual((plan.values["bmm_schema_id"], self.docker.calls), ("", []))

    def test_a_hyphenated_component_gets_an_underscored_schema_name(self):
        self.docker.schemas = {}
        plan = self.plan(component="ITS-DEMO", jira_project="SPECITS")
        self.assertEqual((plan.values["bmm_schema_id"], plan.values["bmm_schema_name"]),
                         ("openehr_its_demo_0.1.0", "its_demo"))

    def test_base_copies_its_own_schema_and_has_no_base_dependency(self):
        repo = self.root / "specifications-BASE"
        repo.mkdir()
        self.docker.schemas = {"openehr_base_1.3.0": BUNDLED}
        plan = self.plan(repo=repo, component_title="Base Model")
        self.assertEqual((plan.values["bmm_schema_id"], plan.values["base_bmm_schema_id"]),
                         ("openehr_base_1.3.0", ""))

    def test_check_flags_a_bmm_seed_file_without_its_keys_and_a_derived_without_a_rule(self):
        dst = self.copy_set()
        path = dst / "assets" / "template-set.json"
        tset = json.loads(path.read_text(encoding="utf-8"))
        del next(f for f in tset["files"] if f["id"] == "bmm")["image"]
        del tset["variables"]["bmm_rm_release"]["derived"]["match"]
        path.write_text(json.dumps(tset), encoding="utf-8")
        problems = scaffold.check_template_set(dst)
        self.assertTrue(any("a bmm-seed file needs image" in p for p in problems), problems)
        self.assertTrue(any("'bmm_rm_release': derived needs either map or match" in p for p in problems), problems)


class DockerHelperTests(unittest.TestCase):
    def test_a_missing_docker_binary_is_reported_not_raised(self):
        with mock.patch.dict(os.environ, {"PATH": ""}):
            self.assertEqual(scaffold.docker("--version"), (None, "docker is not installed"))


if __name__ == "__main__":
    unittest.main()
