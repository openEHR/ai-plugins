#!/usr/bin/env python3
"""Install or upgrade the standard openEHR specification-repo file set.

Python 3.8+, standard library only. The file set (templates, variables, strategies and
revisions) is described by ../assets/template-set.json; see ../SKILL.md for how the skill
drives this script and ../references/maintaining.md for how to change the set.

  scaffold.py plan   --repo DIR [--var NAME=VALUE ...]   what would change; writes nothing
  scaffold.py apply  --repo DIR [--var ...] [--overwrite ID ...] [--pin ID ...]
  scaffold.py render --repo DIR --file ID [--var ...]    print one rendered template
  scaffold.py diff   --repo DIR --file ID [--var ...]    show how the repo's file differs from it
  scaffold.py check                                      validate the template set (CI)
  scaffold.py seal                                       record the template digest

plan and apply print JSON (render and diff print text); errors are {"error": ...}, exit 2.
Nothing is written outside --repo, through a symbolic link, or without the file being complete
first (each write goes to a temporary file that then replaces the target). When a new repository
gets a BMM schema, plan and apply ask the local bmm-publisher image for a bundled one
(docker run --pull never: nothing is downloaded).
"""
import argparse
import copy
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

SET_DIR = Path(__file__).resolve().parent.parent
DESCRIPTOR = ".claude/scaffold.json"
STRATEGIES = ("seed", "whole", "json-merge", "ensure-lines", "regions", "bmm-seed")
BMM_SEED_KEYS = ("present_glob", "image", "image_dir")
MIGRATION_OPS = ("rename", "delete", "note")
STEP_FIELDS = {"rename": ("from", "to"), "delete": ("path", "file_id"), "note": ("text",)}
COMMENT_PREFIXES = ("#", "//")
TODO_MARK = "TODO(scaffold)"
BEGIN_RE = re.compile(r"^<!-- openehr-scaffold:begin ([\w-]+) -->", re.M)
REGION_RE = re.compile(
    r"^<!-- openehr-scaffold:begin (?P<id>[\w-]+) -->\n(?P<body>.*?)^<!-- openehr-scaffold:end (?P=id) -->",
    re.S | re.M,
)


class ScaffoldError(Exception):
    pass


# --------------------------------------------------------------------------- files

def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_raw(path):
    try:
        with open(path, encoding="utf-8", newline="") as handle:
            return handle.read()
    except UnicodeDecodeError:
        raise ScaffoldError(f"{path} is not UTF-8 text: convert it to UTF-8 first")


def normalise(text):
    """Line endings and a byte-order mark never matter for comparing or hashing."""
    return text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")


def read(path):
    return normalise(read_raw(path)) if path.is_file() else None


def read_quiet(path):
    try:
        return read(path)
    except (ScaffoldError, OSError):
        return None


def eol_of(path):
    raw = read_raw(path)
    crlf = raw.count("\r\n")
    return "\r\n" if crlf and crlf * 2 > raw.count("\n") else "\n"


def inside(repo, path):
    try:
        Path(os.path.realpath(path)).relative_to(Path(os.path.realpath(repo)))
        return True
    except ValueError:
        return False


def write(repo, path, text, eol="\n"):
    """Replace `path` atomically, keeping its line endings and file mode."""
    if not inside(repo, path):
        raise ScaffoldError(f"refusing to write outside the repository: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".scaffold-tmp")
    try:
        with open(tmp, "w", encoding="utf-8", newline="") as handle:
            handle.write(text.replace("\n", eol))
        if path.exists():
            shutil.copymode(path, tmp)
        os.replace(tmp, path)
    except BaseException:
        if tmp.exists():
            tmp.unlink()
        raise


def dump_json(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def load_json(path, what):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError) as exc:
        raise ScaffoldError(f"cannot read {what} ({path}): {exc}")


def git(repo, *args):
    try:
        done = subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def git_installed():
    try:
        return subprocess.run(["git", "--version"], capture_output=True, timeout=10).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def docker(*args):
    """(stdout, None) of a docker command, or (None, why it did not work)."""
    try:
        done = subprocess.run(["docker", *args], capture_output=True, timeout=60)
    except FileNotFoundError:
        return None, "docker is not installed"
    except (OSError, subprocess.SubprocessError) as exc:
        return None, f"docker did not run ({type(exc).__name__})"
    if done.returncode != 0:
        lines = [l.strip() for l in done.stderr.decode("utf-8", "replace").splitlines() if l.strip()]
        return None, (lines[0] if lines else f"docker exited with {done.returncode}")[:200]
    try:
        return done.stdout.decode("utf-8"), None
    except UnicodeDecodeError:
        return None, "docker printed something that is not UTF-8 text"


def require_relative(path, where):
    """Paths in the template set and in migrations must stay inside the repository."""
    parts = Path(str(path)).parts
    if not str(path) or Path(str(path)).is_absolute() or ".." in parts:
        raise ScaffoldError(f"{where}: '{path}' must be a relative path inside the repository")


# --------------------------------------------------------------------------- template engine
# {{name}}, {{name|lower}}, {{name|upper}}, and non-nested {{#if name}}..{{/if}} and
# {{#unless name}}..{{/unless}}. A block tag alone on a line disappears with its line.

_STANDALONE = re.compile(r"^[ \t]*(\{\{\s*[#/](?:if|unless)\b[^}]*\}\})[ \t]*\n", re.M)
_COND = re.compile(r"\{\{\s*#(if|unless)\s+([\w-]+)\s*\}\}(.*?)\{\{\s*/\1\s*\}\}", re.S)
_VAR = re.compile(r"\{\{\s*([\w-]+)(?:\|(lower|upper))?\s*\}\}")


def truthy(value):
    return bool(value) and str(value).strip().lower() not in ("false", "0", "no")


def render(text, values, escape=None):
    text = _STANDALONE.sub(r"\1", text)

    def cond(match):
        kind, name, body = match.groups()
        if name not in values:
            raise ScaffoldError(f"template uses unknown variable '{name}'")
        return body if truthy(values[name]) == (kind == "if") else ""

    text = _COND.sub(cond, text)
    if re.search(r"\{\{\s*[#/](?:if|unless)\b", text):
        raise ScaffoldError("unbalanced or nested {{#if}} / {{#unless}} block in a template")

    def var(match):
        name, flt = match.groups()
        if name not in values:
            raise ScaffoldError(f"template uses unknown variable '{name}'")
        value = str(values[name])
        if flt == "lower":
            value = value.lower()
        elif flt == "upper":
            value = value.upper()
        return escape(value) if escape else value

    return _VAR.sub(var, text)


def json_escape(value):
    return json.dumps(value, ensure_ascii=False)[1:-1]


# --------------------------------------------------------------------------- template set

def load_set(set_dir):
    tset = load_json(set_dir / "assets" / "template-set.json", "template set")
    for key in ("id", "revision", "revisions", "variables", "files"):
        if key not in tset:
            raise ScaffoldError(f"template-set.json lacks '{key}'")
    return tset


def strip_descriptions(obj):
    if isinstance(obj, dict):
        return {k: strip_descriptions(v) for k, v in obj.items() if k != "description"}
    if isinstance(obj, list):
        return [strip_descriptions(v) for v in obj]
    return obj


def template_digest(set_dir, tset):
    """Digest of everything that decides what gets written (templates, variables, files)."""
    digest = hashlib.sha256()
    tdir = set_dir / "assets" / "templates"
    for path in sorted(p for p in tdir.rglob("*") if p.is_file() and p.name not in (".DS_Store", "Thumbs.db")):
        digest.update(path.relative_to(tdir).as_posix().encode("utf-8") + b"\0")
        digest.update(path.read_bytes().replace(b"\r\n", b"\n") + b"\0")
    spec = strip_descriptions({"variables": tset["variables"], "files": tset["files"]})
    digest.update(json.dumps(spec, sort_keys=True).encode("utf-8"))
    return digest.hexdigest()


def load_migrations(set_dir, path):
    steps = []
    for rev in path:
        where = f"migrations/{rev:04d}.json"
        mfile = set_dir / "migrations" / f"{rev:04d}.json"
        if not mfile.is_file():
            raise ScaffoldError(f"template set has no migration file {where}")
        migration = load_json(mfile, f"migration {rev}")
        if not isinstance(migration, dict) or migration.get("from") != rev - 1 or migration.get("to") != rev:
            raise ScaffoldError(f"{where} must go from {rev - 1} to {rev}")
        for step in migration.get("steps", []):
            if not isinstance(step, dict) or step.get("op") not in MIGRATION_OPS:
                raise ScaffoldError(f"{where}: unknown op '{step.get('op') if isinstance(step, dict) else step}'")
            for field in STEP_FIELDS[step["op"]]:
                if field not in step:
                    raise ScaffoldError(f"{where}: a {step['op']} step lacks '{field}'")
            for field in ("from", "to", "path"):
                if field in step:
                    require_relative(step[field], where)
            steps.append(dict(step, revision=rev))
    return steps


# --------------------------------------------------------------------------- variables

def version_key(name):
    return (tuple(int(n) for n in re.findall(r"\d+", name)), name)


def repo_bmm_ids(repo):
    bmm_dir = repo / "computable" / "BMM"
    return sorted((p.name[: -len(".bmm.json")] for p in bmm_dir.glob("*.bmm.json")),
                  key=version_key) if bmm_dir.is_dir() else []


def sibling_base(repo, notes):
    """The highest BASE schema id in the sibling specifications-BASE clone, or None (with a note).

    The classes of every component but BASE refer to BASE types, which bmm-publisher only links when
    the BASE BMM is loaded as a dependency (-d)."""
    base_dir = repo.resolve().parent / "specifications-BASE" / "computable" / "BMM"
    base = sorted((p.name[: -len(".bmm.json")] for p in base_dir.glob("openehr_base_*.bmm.json")),
                  key=version_key) if base_dir.is_dir() else []
    if base:
        return base[-1]
    notes.append("no sibling specifications-BASE clone with a BMM schema: the class-table command in "
                 "AGENTS.md will not load BASE with -d, so links to BASE types break; clone it, or "
                 "pass --var base_bmm_schema_id=<id>")
    return None


def infer(repo, tset, set_dir, notes):
    """Variable values read from the repository itself: name -> (value, where from)."""
    found = {}

    def put(name, value, where):
        if isinstance(value, (str, int, float)) and str(value) != "" and name not in found:
            found[name] = (str(value), where)

    manifest = None
    mtext = read_quiet(repo / "manifest.json")
    if mtext:
        try:
            manifest = json.loads(mtext)
        except ValueError:
            manifest = None
    if isinstance(manifest, dict):
        jira = manifest.get("jira") if isinstance(manifest.get("jira"), dict) else {}
        put("component", manifest.get("id"), "manifest.json")
        put("component_title", manifest.get("title"), "manifest.json")
        put("component_description", manifest.get("description"), "manifest.json")
        put("keywords", manifest.get("keywords"), "manifest.json")
        put("jira_project", jira.get("roadmap"), "manifest.json")
        put("jira_open_issues", jira.get("open_issues"), "manifest.json")
        specs = manifest.get("specifications") if isinstance(manifest.get("specifications"), list) else []
        ids = [s["id"] for s in specs if isinstance(s, dict) and isinstance(s.get("id"), str) and s["id"]]
        if ids:
            put("documents", ", ".join(f"`{i}`" for i in ids), "manifest.json")

    config = read_quiet(repo / ".asciidoctorconfig")
    if config:
        match = re.search(r"^:component:\s*(\S+)", config, re.M)
        if match:
            put("component", match.group(1), ".asciidoctorconfig")

    remote = git(repo, "remote", "get-url", "origin")
    if remote:
        match = re.search(r"/(specifications-[\w-]+?)(?:\.git)?/?$", remote)
        if match:
            put("repo_name", match.group(1), "git remote")
            put("component", match.group(1)[len("specifications-"):].upper(), "git remote")

    match = re.fullmatch(r"specifications-(.+)", repo.name)
    if match:
        put("repo_name", repo.name, "directory name")
        put("component", match.group(1).upper(), "directory name")

    bmm = repo_bmm_ids(repo)
    if bmm:
        put("bmm_schema_id", bmm[-1], "computable/BMM")
        if len(bmm) > 1:
            notes.append(f"several BMM schemas in computable/BMM ({', '.join(bmm)}): using {bmm[-1]}; "
                         "pass --var bmm_schema_id=<id> to choose another")
        if not bmm[-1].startswith("openehr_base_"):
            put("base_bmm_schema_id", sibling_base(repo, notes), "sibling specifications-BASE")

    head = git(repo, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    if head:
        put("default_branch", head.split("/", 1)[-1], "git origin/HEAD")

    lic = read_quiet(repo / "LICENSE")
    if lic is not None:
        for file_spec in tset["files"]:
            for key, name in (file_spec.get("templates") or {}).items():
                text = read_quiet(set_dir / "assets" / "templates" / name)
                if text is not None and sha(text) == sha(lic):
                    put(file_spec["template_var"], key, "LICENSE text")
    return found


def resolve_variables(tset, explicit, saved, inferred, defaulted=()):
    """Merge by priority: explicit, recorded as confirmed, inferred, recorded as a default, default."""
    schema = tset["variables"]
    values, sources = {}, {}
    missing, invalid = [], []
    confirmed = {k: v for k, v in saved.items() if k not in defaulted}
    unconfirmed = {k: v for k, v in saved.items() if k in defaulted}
    pools = (("explicit", explicit), ("descriptor", confirmed), ("inferred", inferred),
             ("descriptor (default)", unconfirmed))
    for name, spec in schema.items():
        if "derived" in spec:
            continue
        for label, pool in pools:
            if name in pool:
                entry = pool[name]
                value, where = entry if isinstance(entry, tuple) else (entry, None)
                if spec.get("required") and not str(value).strip():
                    continue  # an empty required value is no value
                values[name] = str(value)
                sources[name] = label if where is None else f"{label}: {where}"
                break
        else:
            default = spec.get("default")
            for rule in spec.get("default_if", []):
                if re.search(rule["matches"], values.get(rule["var"], "")):
                    default = rule["value"]
            if default is not None:
                try:
                    values[name] = render(default, values)
                    sources[name] = "default"
                except ScaffoldError:
                    pass  # depends on a variable that is itself missing
        if name not in values and spec.get("required"):
            missing.append({"name": name, "description": spec.get("description", "")})

    for name, spec in schema.items():
        derived = spec.get("derived")
        if derived and derived["from"] in values:
            source = values[derived["from"]]
            if "match" in derived:  # a regex group of the source, empty when it does not match
                match = re.search(derived["match"], source)
                values[name] = match.group(derived.get("group", 1)) if match else ""
            else:
                values[name] = derived.get("map", {}).get(source, source)
            sources[name] = "derived"

    for name, value in values.items():
        spec = schema[name]
        if spec.get("pattern") and not re.search(spec["pattern"], value):
            invalid.append({"name": name, "value": value, "problem": f"does not match {spec['pattern']}"})
        if spec.get("choices") and value not in spec["choices"]:
            invalid.append({"name": name, "value": value, "problem": f"must be one of {spec['choices']}"})
    return values, sources, missing, invalid


# --------------------------------------------------------------------------- file strategies

class Act:
    """What to do about one managed file. `content` is written when it is not None."""

    def __init__(self, spec, action, detail=None, content=None, record=None, **extra):
        self.id, self.target, self.strategy = spec["id"], spec["target"], spec["strategy"]
        self.action, self.detail, self.content, self.record, self.extra = action, detail, content, record, extra
        self.eol = "\n"

    def public(self):
        out = {"id": self.id, "target": self.target, "strategy": self.strategy, "action": self.action}
        if self.detail:
            out["detail"] = self.detail
        out.update({k: v for k, v in self.extra.items() if v not in (None, [], "")})
        return out


class Ctx:
    def __init__(self, repo, set_dir, tset, values, desc, overwrite, pinned, new_bmm=None):
        self.repo, self.set_dir, self.tset, self.values = repo, set_dir, tset, values
        self.desc_files = (desc or {}).get("files", {})
        self.overwrite, self.pinned = set(overwrite), set(pinned)
        self.new_bmm = new_bmm  # what new_bmm() decided, when this run offers a BMM schema
        self.warnings = []


def template_name(ctx, spec):
    if "templates" in spec:
        return spec["templates"][ctx.values[spec["template_var"]]]
    return spec["template"]


def rendered_for(ctx, spec):
    name = template_name(ctx, spec)
    text = normalise((ctx.set_dir / "assets" / "templates" / name).read_text(encoding="utf-8"))
    if name.endswith(".txt"):
        return text  # licence texts are verbatim
    escape = json_escape if spec["target"].endswith(".json") else None
    out = render(text, ctx.values, escape)
    return out if out.endswith("\n") else out + "\n"


def plan_seed(ctx, spec, rendered):
    target = ctx.repo / spec["target"]
    if target.is_file():  # a seed file is never changed, so it never needs decoding
        detail = None
        if "templates" in spec:
            current = read_quiet(target)
            wanted = ctx.values[spec["template_var"]]
            family = None
            for key, name in spec["templates"].items():
                text = read_quiet(ctx.set_dir / "assets" / "templates" / name)
                if text is not None and current is not None and sha(text) == sha(current):
                    family = key
            if current is None:
                detail = "could not be read as UTF-8 text, so it was not compared with the standard texts"
            elif family is None:
                detail = "differs from the standard licence texts"
            elif family != wanted:
                detail = f"has the standard {family} text, but license is {wanted}"
            else:
                detail = f"matches the standard {family} text"
        return Act(spec, "exists", detail)
    for alt in spec.get("alternatives", []):
        if (ctx.repo / alt).exists():
            return Act(spec, "exists-alternative", alt)
    return Act(spec, "create", content=rendered)


def plan_whole(ctx, spec, rendered):
    current = read(ctx.repo / spec["target"])
    new_sha = sha(rendered)
    recorded = ctx.desc_files.get(spec["id"], {}).get("sha256")
    if current is None:
        return Act(spec, "create", content=rendered, record={"sha256": new_sha})
    if sha(current) == new_sha:
        return Act(spec, "unchanged", record={"sha256": new_sha})
    if recorded == sha(current) or spec["id"] in ctx.overwrite:
        return Act(spec, "update", content=rendered, record={"sha256": new_sha})
    why = "edited since it was scaffolded" if recorded else "exists and differs from the template"
    return Act(spec, "conflict", why)


def json_items(obj, path=""):
    """Ids of the leaves and list items of a JSON document: what a merge has already offered."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield from json_items(value, f"{path}.{key}" if path else key)
    elif isinstance(obj, list):
        for item in obj:
            yield f"{path}[]={json.dumps(item, sort_keys=True, ensure_ascii=False)}"
    else:
        yield path


def merge_list(base, extra, here, added, removed, known):
    for item in extra:
        item_id = f"{here}[]={json.dumps(item, sort_keys=True, ensure_ascii=False)}"
        if item in base:
            continue
        if item_id in known:
            removed.append(item_id)
            continue
        base.append(copy.deepcopy(item))
        added.append(f"{here}[] {item if not isinstance(item, (dict, list)) else '...'}")


def deep_merge(base, extra, path, added, removed, known):
    """Add what `extra` has and `base` lacks; existing values win, and items the user removed
    after an earlier run (they are in `known` but absent) are not added back."""
    for key, value in extra.items():
        here = f"{path}.{key}" if path else key
        if key in base:
            if isinstance(base[key], dict) and isinstance(value, dict):
                deep_merge(base[key], value, here, added, removed, known)
            elif isinstance(base[key], list) and isinstance(value, list):
                merge_list(base[key], value, here, added, removed, known)
        elif isinstance(value, dict):
            sub = {}
            deep_merge(sub, value, here, added, removed, known)
            if sub or not value:
                base[key] = sub
                if not value:
                    added.append(here)
        elif isinstance(value, list):
            sub = []
            merge_list(sub, value, here, added, removed, known)
            if sub or not value:
                base[key] = sub
                if not value:
                    added.append(here)
        elif here in known:
            removed.append(here)
        else:
            base[key] = copy.deepcopy(value)
            added.append(here)


def plan_json_merge(ctx, spec, rendered):
    current = read(ctx.repo / spec["target"])
    template = json.loads(rendered)
    known = set(ctx.desc_files.get(spec["id"], {}).get("items", []))
    record = {"items": sorted(known | set(json_items(template)))}
    if current is None:
        return Act(spec, "create", content=rendered, record=record)
    try:
        existing = json.loads(current)
        problem = None if isinstance(existing, dict) else "its top level is not a JSON object"
    except ValueError as exc:
        problem = f"not valid JSON ({exc})"
    if problem:
        if spec["id"] in ctx.overwrite:
            return Act(spec, "update", f"replaced the file ({problem}) with the template", content=rendered, record=record)
        return Act(spec, "conflict", f"{problem}; fix it, or take the template with --overwrite {spec['id']}")
    added, removed = [], []
    deep_merge(existing, template, "", added, removed, known)
    detail = f"{len(removed)} item(s) you removed earlier are left out" if removed else None
    if not added:
        return Act(spec, "unchanged", detail, record=record)
    detail = f"adds {len(added)}: " + "; ".join(added) + (f"; {detail}" if detail else "")
    return Act(spec, "merge", detail, content=dump_json(existing), record=record, added=added)


def parse_groups(text):
    """Blocks of consecutive non-blank lines: comment lines first, then the required lines."""
    groups, block = [], []
    for line in text.splitlines() + [""]:
        if line.strip():
            block.append(line)
        elif block:
            comments = [l for l in block if l.startswith(COMMENT_PREFIXES)]
            groups.append({"comments": comments, "lines": [l for l in block if l not in comments]})
            block = []
    return groups


def plan_ensure_lines(ctx, spec, rendered):
    current = read(ctx.repo / spec["target"])
    key = re.compile(spec["key"]) if spec.get("key") else None

    def keyof(line):
        match = key.match(line) if key else None
        return match.group(1) if match else line.strip()

    groups = parse_groups(rendered)
    known = set(ctx.desc_files.get(spec["id"], {}).get("items", []))
    record = {"items": sorted(known | {keyof(l) for g in groups for l in g["lines"]})}
    if current is None:
        return Act(spec, "create", content=rendered, record=record)
    present = {}
    for line in current.splitlines():
        if line.strip() and not line.startswith(COMMENT_PREFIXES):
            present.setdefault(keyof(line), line.strip())
    blocks, added, removed, notes = [], [], [], []
    for group in groups:
        missing = []
        for line in group["lines"]:
            if keyof(line) in present:
                if present[keyof(line)] != line.strip():
                    notes.append(f"{spec['target']} has `{present[keyof(line)]}` where the standard has `{line.strip()}`")
            elif keyof(line) in known:
                removed.append(line)
            else:
                missing.append(line)
        if missing:
            blocks.append(group["comments"] + missing)
            added.extend(missing)
    ctx.warnings.extend(notes)
    left_out = f"{len(removed)} line(s) you removed earlier are left out" if removed else None
    if not added:
        return Act(spec, "unchanged", left_out, record=record)
    out = current if current.endswith("\n") or not current else current + "\n"
    for block in blocks:
        out += ("\n" if out else "") + "\n".join(block) + "\n"
    detail = f"adds {len(added)} line(s): " + ", ".join(added) + (f"; {left_out}" if left_out else "")
    return Act(spec, "merge", detail, content=out, record=record, added=added)


def parse_regions(text, where="the template"):
    """Regions of a file, by id. Every begin marker must close, or a replace could swallow user text."""
    regions = {}
    for match in REGION_RE.finditer(text):
        if match.group("id") in regions:
            raise ScaffoldError(f"{where}: region '{match.group('id')}' appears twice")
        regions[match.group("id")] = match.group("body")
    begins = BEGIN_RE.findall(text)
    if len(begins) != len(regions):
        unclosed = [b for b in begins if b not in regions] or begins
        raise ScaffoldError(f"{where}: scaffold markers do not pair up (no matching end marker for "
                            f"{', '.join(unclosed)}); fix the markers by hand and run again")
    return regions


def wrap_region(rid, body):
    body = body if body.endswith("\n") else body + "\n"
    return f"<!-- openehr-scaffold:begin {rid} -->\n{body}<!-- openehr-scaffold:end {rid} -->"


def plan_regions(ctx, spec, rendered):
    current = read(ctx.repo / spec["target"])
    template = parse_regions(rendered)
    recorded = ctx.desc_files.get(spec["id"], {}).get("regions", {})
    if current is None:
        return Act(spec, "create", content=rendered,
                   record={"regions": {rid: sha(body.strip()) for rid, body in template.items()}})
    existing = parse_regions(current, spec["target"])
    if not existing:
        return Act(spec, "upgrade-manual",
                   "exists without scaffold regions; compare it with `render --file "
                   f"{spec['id']}` and merge by hand, or pin it")
    text, new_record, results = current, dict(recorded), []
    for rid, body in template.items():
        tsha, here = sha(body.strip()), existing.get(rid)
        key = f"{spec['id']}:{rid}"
        forced = spec["id"] in ctx.overwrite or key in ctx.overwrite
        if here is None:
            if key in ctx.pinned:
                results.append({"region": rid, "action": "pinned"})
            elif rid in recorded and not forced:
                results.append({"region": rid, "action": "removed"})
            else:
                text = text.rstrip("\n") + "\n\n" + wrap_region(rid, body) + "\n"
                new_record[rid] = tsha
                results.append({"region": rid, "action": "add"})
        elif sha(here.strip()) == tsha:
            new_record[rid] = tsha
            results.append({"region": rid, "action": "unchanged"})
        elif key in ctx.pinned:
            results.append({"region": rid, "action": "pinned"})
        elif recorded.get(rid) == sha(here.strip()) or forced:
            text = REGION_RE.sub(lambda m, r=rid, b=body: wrap_region(r, b) if m.group("id") == r else m.group(0), text)
            new_record[rid] = tsha
            results.append({"region": rid, "action": "update"})
        else:
            results.append({"region": rid, "action": "conflict"})
    actions = {r["action"] for r in results}
    overall = ("conflict" if "conflict" in actions
               else "update" if actions & {"add", "update"}
               else "unchanged")
    return Act(spec, overall, content=text if text != current else None,
               record={"regions": new_record}, regions=results)


def plan_bmm_seed(ctx, spec, rendered):
    """Like seed, but only for a new repository and only while computable/BMM holds no schema;
    the content is the image's bundled schema when there is one, else the empty-schema template."""
    shown = dict(spec, target=spec["present_glob"])
    present = sorted(p.name for p in ctx.repo.glob(spec["present_glob"]))
    if present:
        return Act(shown, "exists", ", ".join(present))
    new = ctx.new_bmm
    if new is None:
        return Act(shown, "skipped", "offered only when a repository is initialised; "
                                     f"pass --overwrite {spec['id']} to create one here")
    if "blocked" in new:
        return Act(shown, "blocked", new["blocked"])
    if "text" in new:
        return Act(spec, "create", f"copied from {spec['image']} ({new['schema_id']})", content=new["text"])
    return Act(spec, "create", f"new empty schema {new['schema_id']}: one root package, no classes yet"
               + (f"; {new['note']}" if new.get("note") else ""), content=rendered)


STRATEGY_FUNCS = {
    "seed": plan_seed,
    "whole": plan_whole,
    "json-merge": plan_json_merge,
    "ensure-lines": plan_ensure_lines,
    "regions": plan_regions,
    "bmm-seed": plan_bmm_seed,
}


def target_of(spec, values):
    """A target may use variables (computable/BMM/{{bmm_schema_id}}.bmm.json)."""
    target = render(spec["target"], values) if "{{" in spec["target"] else spec["target"]
    require_relative(target, f"file '{spec['id']}' target")
    return target


def plan_file(ctx, spec):
    if spec["id"] in ctx.pinned:
        return Act(dict(spec, target=spec.get("present_glob", spec["target"])), "pinned")
    spec = dict(spec, target=target_of(spec, ctx.values))
    target = ctx.repo / spec["target"]
    if target.is_symlink():
        return Act(spec, "conflict", "is a symbolic link; scaffold never writes through links")
    act = STRATEGY_FUNCS[spec["strategy"]](ctx, spec, rendered_for(ctx, spec))
    if act.content is not None and target.is_file():
        act.eol = eol_of(target)
    return act


# --------------------------------------------------------------------------- plan / apply

class Plan:
    pass


def validate_descriptor(desc):
    if not isinstance(desc, dict) or not isinstance(desc.get("revision"), int) or desc["revision"] < 1:
        raise ScaffoldError(f"{DESCRIPTOR} is malformed: 'revision' must be a positive integer")
    for key in ("variables", "files"):
        if not isinstance(desc.setdefault(key, {}), dict):
            raise ScaffoldError(f"{DESCRIPTOR} is malformed: '{key}' must be an object")
    if not all(isinstance(rec, dict) for rec in desc["files"].values()):
        raise ScaffoldError(f"{DESCRIPTOR} is malformed: every entry of 'files' must be an object")
    for key in ("pinned", "defaulted"):
        if not isinstance(desc.setdefault(key, []), list):
            raise ScaffoldError(f"{DESCRIPTOR} is malformed: '{key}' must be a list")


def present(repo, spec):
    if "present_glob" in spec:
        return any(repo.glob(spec["present_glob"]))
    return (repo / spec["target"]).exists() or (repo / spec["target"]).is_symlink()


def bundled_bmm(spec, name):
    """Ids of the schemas the bmm-publisher image bundles for schema `name`, highest version last,
    or (None, why) when the image could not be listed."""
    out, problem = docker("run", "--rm", "--pull", "never", "--entrypoint", "ls", spec["image"], spec["image_dir"])
    if problem:
        return None, problem
    pattern = re.compile(rf"openehr_{re.escape(name)}_[0-9]+\.[0-9]+\.[0-9]+")
    ids = [line.strip()[: -len(".bmm.json")] for line in out.splitlines() if line.strip().endswith(".bmm.json")]
    return sorted((i for i in ids if pattern.fullmatch(i)), key=version_key), None


def new_bmm(repo, spec, values, sources, notes):
    """Decide the BMM schema of a new repository: the image's bundled copy, or the empty template.

    Returns {"schema_id", "inferred"} plus "text" (the bundled copy) or "note", or {"blocked": why}
    when the image could not be checked and the user gave no schema id."""
    component = values["component"]
    name = component.lower().replace("-", "_")
    given = values.get("bmm_schema_id", "") if sources.get("bmm_schema_id") in ("explicit", "descriptor") else ""
    fresh = given or f"openehr_{name}_{values['first_release']}"
    ids, problem = bundled_bmm(spec, name)
    if problem:
        if not given:
            return {"blocked": f"could not check whether {spec['image']} bundles a {component} schema ({problem}); "
                               f"start Docker (`docker pull {spec['image']}` if the image is missing) and plan "
                               f"again, or create an empty schema with --var bmm_schema_id={fresh}"}
        result = {"schema_id": given, "note": f"{spec['image']} was not checked for a bundled copy ({problem})"}
    else:
        chosen = given or (ids[-1] if ids else fresh)
        result = {"schema_id": chosen}
        if chosen in ids:
            text, problem = docker("run", "--rm", "--pull", "never", "--entrypoint", "cat", spec["image"],
                                   f"{spec['image_dir']}/{chosen}.bmm.json")
            if problem is None:
                try:
                    json.loads(text)
                except ValueError:
                    problem = "it is not valid JSON"
            if problem:
                return {"blocked": f"could not copy {chosen} from {spec['image']} ({problem}); plan again, or "
                                   "create an empty schema with --var bmm_schema_id=<another id>"}
            result["text"] = normalise(text)
        elif ids:
            result["note"] = f"{spec['image']} bundles {', '.join(ids)}, not {chosen}"
    inferred = {}
    if not given:
        inferred["bmm_schema_id"] = (result["schema_id"],
                                     "bmm-publisher image" if "text" in result else "new empty schema")
    if not result["schema_id"].startswith("openehr_base_"):
        base = sibling_base(repo, notes)
        if base:
            inferred["base_bmm_schema_id"] = (base, "sibling specifications-BASE")
    result["inferred"] = inferred
    return result


def build_plan(repo, set_dir, explicit, overwrite=(), pin=()):
    tset = load_set(set_dir)
    unknown = [k for k in explicit if k not in tset["variables"] or "derived" in tset["variables"][k]]
    if unknown:
        known = [k for k, v in tset["variables"].items() if "derived" not in v]
        raise ScaffoldError(f"unknown variable(s) {', '.join(unknown)}; known: {', '.join(known)}")
    desc_path = repo / DESCRIPTOR
    desc = load_json(desc_path, "scaffold descriptor") if desc_path.is_file() else None
    latest = tset["revision"]
    if desc is not None:
        validate_descriptor(desc)
        if desc.get("template_set") != tset["id"]:
            raise ScaffoldError(f"{DESCRIPTOR} belongs to template set '{desc.get('template_set')}', not '{tset['id']}'")
        if desc["revision"] > latest:
            raise ScaffoldError(f"{DESCRIPTOR} is revision {desc['revision']}, newer than this plugin's {latest}: update the openehr-specs plugin")
        recorded = desc["revision"]
        mode = "current" if recorded == latest else "upgrade"
        path = list(range(recorded + 1, latest + 1))
    else:
        recorded, path = None, []
        mode = "upgrade" if any(present(repo, f) for f in tset["files"]) else "init"

    plan = Plan()
    plan.repo, plan.set_dir, plan.tset, plan.desc = repo, set_dir, tset, desc
    plan.mode, plan.recorded, plan.latest, plan.path = mode, recorded, latest, path
    plan.steps = load_migrations(set_dir, path)
    plan.pinned = set((desc or {}).get("pinned", [])) | set(pin)

    plan.notes = []
    saved, defaulted = (desc or {}).get("variables", {}), (desc or {}).get("defaulted", [])
    inferred = infer(repo, tset, set_dir, plan.notes)
    resolved = resolve_variables(tset, explicit, saved, inferred, defaulted)
    # a BMM schema is offered to a new repository only (or on request), so its id and the BASE
    # dependency are known before the other templates (AGENTS.md) are rendered
    plan.new_bmm = None
    bmm_spec = next((f for f in tset["files"] if f["strategy"] == "bmm-seed"), None)
    if (bmm_spec and bmm_spec["id"] not in plan.pinned and (mode == "init" or bmm_spec["id"] in overwrite)
            and not present(repo, bmm_spec) and not resolved[2] and not resolved[3]):
        plan.new_bmm = new_bmm(repo, bmm_spec, resolved[0], resolved[1], plan.notes)
        if plan.new_bmm.get("inferred"):
            inferred.update(plan.new_bmm["inferred"])
            resolved = resolve_variables(tset, explicit, saved, inferred, defaulted)
    plan.values, plan.sources, plan.missing, plan.invalid = resolved
    plan.acts, plan.warnings = [], list(plan.notes)
    if not plan.missing and not plan.invalid:
        for spec in tset["files"]:
            require_relative(spec["target"], f"file '{spec['id']}' target")
        ctx = Ctx(repo, set_dir, tset, plan.values, desc, overwrite, plan.pinned, plan.new_bmm)
        valid = {spec["id"] for spec in tset["files"]}
        for spec in tset["files"]:
            if spec["strategy"] == "regions":
                valid |= {f"{spec['id']}:{rid}" for rid in parse_regions(rendered_for(ctx, spec))}
        wrong = [x for x in list(overwrite) + list(pin) if x not in valid]
        if wrong:
            raise ScaffoldError(f"unknown id(s) {', '.join(wrong)} for --overwrite/--pin; valid: {', '.join(sorted(valid))}")
        plan.acts = [plan_file(ctx, spec) for spec in tset["files"]]
        plan.warnings = plan.notes + ctx.warnings
    return plan


def todo_markers(repo, tset):
    found = []
    for spec in tset["files"]:
        text = read_quiet(repo / spec["target"])
        for number, line in enumerate((text or "").splitlines(), 1):
            if TODO_MARK in line:
                found.append({"file": spec["target"], "line": number, "text": line.strip()[:160]})
    return found


def public(plan):
    repo = plan.repo
    warnings = list(plan.warnings)
    installed = git_installed()
    top = git(repo, "rev-parse", "--show-toplevel") if installed else None
    inside_repo = top is not None and Path(top).resolve() == repo.resolve()
    if not installed:
        warnings.append("git is not installed: install it before this directory can become a repository")
    elif top is None:
        warnings.append("not a git repository: run `git init -b <default branch>` first if this is a new repository")
    elif not inside_repo:
        warnings.append(f"{repo} is inside the git repository at {top}: run from the repository root")
    elif git(repo, "status", "--porcelain"):
        warnings.append("the working tree has uncommitted changes: review the result with `git diff`")
    return {
        "status": "needs_input" if (plan.missing or plan.invalid) else "ok",
        "repo": str(repo),
        "mode": plan.mode,
        "template_set": plan.tset["id"],
        "recorded_revision": plan.recorded,
        "latest_revision": plan.latest,
        "migration_path": plan.path,
        "variables": {k: {"value": v, "source": plan.sources.get(k)} for k, v in plan.values.items()},
        "missing_variables": plan.missing,
        "invalid_variables": plan.invalid,
        "files": [a.public() for a in plan.acts],
        "migration_steps": plan.steps,
        "warnings": warnings,
        "todo_markers": todo_markers(repo, plan.tset),
        "git_repository": inside_repo,
    }


def run_migration_steps(plan):
    repo, files = plan.repo, (plan.desc or {}).get("files", {})
    results = []
    for step in plan.steps:
        op, entry = step["op"], dict(step)
        fid = step.get("file_id")
        if op == "note":
            entry["result"] = "manual: see note"
        elif fid and fid in plan.pinned:
            entry["result"] = "skipped: that file is pinned"
        elif op == "rename":
            src, dst = repo / step["from"], repo / step["to"]
            if not src.exists():
                entry["result"] = "skipped: source is missing"
            elif dst.exists():
                entry["result"] = "skipped: target exists"
            elif not (inside(repo, src) and inside(repo, dst)):
                entry["result"] = "skipped: outside the repository"
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                src.rename(dst)
                entry["result"] = "done"
        else:  # delete
            path = repo / step["path"]
            recorded = files.get(fid, {}).get("sha256")
            current = read_quiet(path)
            if not path.exists():
                entry["result"] = "skipped: already gone"
            elif path.is_symlink() or not inside(repo, path):
                entry["result"] = "skipped: a link or outside the repository"
            elif recorded and current is not None and sha(current) == recorded:
                path.unlink()
                entry["result"] = "done"
            else:
                entry["result"] = "skipped: modified or not recorded as scaffolded, delete by hand if wanted"
        results.append(entry)
    return results


def apply_plan(repo, set_dir, explicit, overwrite, pin):
    first = build_plan(repo, set_dir, explicit, overwrite, pin)
    if first.missing or first.invalid:
        return public(first)
    migration_results = run_migration_steps(first) if first.steps else []
    plan = build_plan(repo, set_dir, explicit, overwrite, pin) if first.steps else first
    plan.steps = migration_results or plan.steps

    written = []
    for act in plan.acts:
        if act.content is not None:
            write(repo, repo / act.target, act.content, act.eol)
            written.append(act.target)

    files = copy.deepcopy((plan.desc or {}).get("files", {}))
    for act in plan.acts:
        if act.record:
            merged = files.setdefault(act.id, {})
            for key, value in act.record.items():
                if isinstance(value, dict):
                    merged.setdefault(key, {}).update(value)
                else:
                    merged[key] = value
    desc = {
        "template_set": plan.tset["id"],
        "revision": plan.latest,
        "variables": {k: v for k, v in plan.values.items() if "derived" not in plan.tset["variables"][k]},
        "defaulted": sorted(k for k, s in plan.sources.items() if s in ("default", "descriptor (default)")),
        "files": files,
    }
    if plan.pinned:
        desc["pinned"] = sorted(plan.pinned)
    write(repo, repo / DESCRIPTOR, dump_json(desc))

    out = public(plan)
    out["applied"] = True
    out["written"] = written + [DESCRIPTOR]
    return out


def diff_file(repo, set_dir, explicit, file_id):
    """Unified diff of the repo's file against what the template would write."""
    plan = build_plan(repo, set_dir, explicit)
    if plan.missing or plan.invalid:
        raise ScaffoldError(f"variables missing or invalid: {plan.missing or plan.invalid}")
    spec = next((f for f in plan.tset["files"] if f["id"] == file_id), None)
    if spec is None:
        raise ScaffoldError(f"unknown file id '{file_id}'")
    spec = dict(spec, target=target_of(spec, plan.values))
    rendered = rendered_for(Ctx(repo, set_dir, plan.tset, plan.values, plan.desc, (), ()), spec)
    current = read(repo / spec["target"])
    if current is None:
        return f"{spec['target']} does not exist yet\n"
    pairs = [(spec["target"], current, rendered)]
    if spec["strategy"] == "regions" and parse_regions(current, spec["target"]):
        here = parse_regions(current, spec["target"])
        pairs = [(f"{spec['target']} [region {rid}]", here[rid], body)
                 for rid, body in parse_regions(rendered).items()
                 if rid in here and here[rid].strip() != body.strip()]
    out = "".join(
        "".join(difflib.unified_diff(a.splitlines(True), b.splitlines(True),
                                     fromfile=f"{label} (repo)", tofile=f"{label} (template)"))
        for label, a, b in pairs)
    return out or "no differences\n"


# --------------------------------------------------------------------------- check / seal

def sample_values(tset, bmm):
    explicit = {}
    for name, spec in tset["variables"].items():
        if spec.get("required"):
            explicit[name] = "EXAMPLE" if name == "component" else "Example Title"
    explicit["bmm_schema_id"] = "openehr_example_1.0.0" if bmm else ""
    explicit["base_bmm_schema_id"] = "openehr_base_1.0.0" if bmm else ""
    return resolve_variables(tset, explicit, {}, {})


def check_template_set(set_dir):
    """Problems with the template set itself (an empty list means it is sound)."""
    try:
        return _check_template_set(set_dir)
    except Exception as exc:  # a malformed set must be reported, not crash the checker
        return [f"the template set could not be checked: {type(exc).__name__}: {exc}"]


def _check_template_set(set_dir):
    problems = []
    try:
        tset = load_set(set_dir)
    except ScaffoldError as exc:
        return [str(exc)]
    revisions = [r.get("revision") for r in tset["revisions"]]
    if not revisions:
        return ["revisions is empty: the first revision needs an entry"]
    if revisions != list(range(1, len(revisions) + 1)):
        problems.append(f"revisions must run 1..N without gaps, found {revisions}")
    elif tset["revision"] != revisions[-1]:
        problems.append(f"revision {tset['revision']} is not the last entry of revisions ({revisions[-1]})")
    for rev in range(2, revisions[-1] + 1):
        try:
            load_migrations(set_dir, [rev])
        except ScaffoldError as exc:
            problems.append(str(exc))
    if tset["revisions"][-1].get("digest") != template_digest(set_dir, tset):
        problems.append("the templates or the variables/files changed without a new revision: "
                        "add a revision and a migration file, then run `scaffold.py seal`")

    ids = [f.get("id") for f in tset["files"]]
    if len(ids) != len(set(ids)):
        problems.append("file ids must be unique")
    for spec in tset["files"]:
        label = spec.get("id", "?")
        try:
            require_relative(spec.get("target", ""), f"file '{label}' target")
        except ScaffoldError as exc:
            problems.append(str(exc))
        if spec.get("strategy") not in STRATEGIES:
            problems.append(f"file '{label}': unknown strategy '{spec.get('strategy')}'")
        if spec.get("strategy") == "bmm-seed":
            lacking = [k for k in BMM_SEED_KEYS if not spec.get(k)]
            if lacking:
                problems.append(f"file '{label}': a bmm-seed file needs {', '.join(lacking)}")
            if "{{bmm_schema_id}}" not in spec.get("target", ""):
                problems.append(f"file '{label}': a bmm-seed target must contain {{{{bmm_schema_id}}}}")
        names = list((spec.get("templates") or {}).values()) or [spec.get("template")]
        for name in names:
            if not name or not (set_dir / "assets" / "templates" / name).is_file():
                problems.append(f"file '{label}': template '{name}' is missing")
    if sum(1 for f in tset["files"] if f.get("strategy") == "bmm-seed") > 1:
        problems.append("only one file may use the bmm-seed strategy")
    for name, spec in tset["variables"].items():
        derived = spec.get("derived")
        if derived and derived["from"] not in tset["variables"]:
            problems.append(f"variable '{name}' derives from unknown '{derived['from']}'")
        if derived and ("map" in derived) == ("match" in derived):
            problems.append(f"variable '{name}': derived needs either map or match")
        elif derived and "match" in derived:
            try:
                if re.compile(derived["match"]).groups < derived.get("group", 1):
                    problems.append(f"variable '{name}': match has no group {derived.get('group', 1)}")
            except re.error as exc:
                problems.append(f"variable '{name}': match is not a valid regex ({exc})")
        if not derived and "default" not in spec and not spec.get("required"):
            problems.append(f"variable '{name}' needs a default or required: true")

    for bmm in (False, True):
        values, _, missing, invalid = sample_values(tset, bmm)
        if missing or invalid:
            problems.append(f"sample variables do not resolve: {missing or invalid}")
            continue
        ctx = Ctx(Path("/nonexistent"), set_dir, tset, values, None, (), ())
        for spec in tset["files"]:
            names = list((spec.get("templates") or {}).values()) or [spec.get("template")]
            if not all(n and (set_dir / "assets" / "templates" / n).is_file() for n in names):
                continue  # already reported as a missing template
            try:
                target_of(spec, values)
                text = rendered_for(ctx, spec)
                if spec["target"].endswith(".json"):
                    json.loads(text)
                if spec["strategy"] == "regions":
                    parse_regions(text)
            except (ScaffoldError, ValueError, KeyError) as exc:
                problems.append(f"file '{spec['id']}' (bmm={bmm}): {exc}")
    return problems


def seal(set_dir):
    path = set_dir / "assets" / "template-set.json"
    tset = load_set(set_dir)
    if not tset["revisions"]:
        raise ScaffoldError("revisions is empty: add the first revision before sealing")
    tset["revisions"][-1]["digest"] = template_digest(set_dir, tset)
    path.write_text(dump_json(tset), encoding="utf-8")
    return {"sealed": tset["revisions"][-1]["revision"], "digest": tset["revisions"][-1]["digest"]}


# --------------------------------------------------------------------------- CLI

def parse_vars(pairs):
    out = {}
    for pair in pairs or []:
        if "=" not in pair:
            raise ScaffoldError(f"--var expects NAME=VALUE, got '{pair}'")
        name, value = pair.split("=", 1)
        out[name.strip()] = value
    return out


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--set-dir", default=str(SET_DIR), help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("plan", "apply", "render", "diff"):
        p = sub.add_parser(name)
        p.add_argument("--repo", required=True)
        p.add_argument("--var", action="append", default=[])
        if name in ("plan", "apply"):
            p.add_argument("--overwrite", action="append", default=[], help="file id or file:region to take from the template")
            p.add_argument("--pin", action="append", default=[], help="file id or file:region to leave alone from now on")
        if name in ("render", "diff"):
            p.add_argument("--file", required=True)
    sub.add_parser("check")
    sub.add_parser("seal")
    args = parser.parse_args(argv)
    set_dir = Path(args.set_dir)

    try:
        if args.cmd == "check":
            problems = check_template_set(set_dir)
            print(json.dumps({"ok": not problems, "problems": problems}, indent=2))
            return 1 if problems else 0
        if args.cmd == "seal":
            print(json.dumps(seal(set_dir), indent=2))
            return 0
        repo = Path(args.repo).resolve()
        if not repo.is_dir():
            raise ScaffoldError(f"{repo} is not a directory")
        explicit = parse_vars(args.var)
        if args.cmd == "plan":
            print(json.dumps(public(build_plan(repo, set_dir, explicit, args.overwrite, args.pin)), indent=2, ensure_ascii=False))
        elif args.cmd == "apply":
            print(json.dumps(apply_plan(repo, set_dir, explicit, args.overwrite, args.pin), indent=2, ensure_ascii=False))
        elif args.cmd == "diff":
            sys.stdout.write(diff_file(repo, set_dir, explicit, args.file))
        else:
            plan = build_plan(repo, set_dir, explicit)
            if plan.missing or plan.invalid:
                raise ScaffoldError(f"variables missing or invalid: {plan.missing or plan.invalid}")
            spec = next((f for f in plan.tset["files"] if f["id"] == args.file), None)
            if spec is None:
                raise ScaffoldError(f"unknown file id '{args.file}'")
            sys.stdout.write(rendered_for(Ctx(repo, set_dir, plan.tset, plan.values, plan.desc, (), ()), spec))
        return 0
    except ScaffoldError as exc:
        print(json.dumps({"error": str(exc)}))
        return 2
    except Exception as exc:  # the contract is JSON on stdout, never a traceback
        print(json.dumps({"error": f"unexpected {type(exc).__name__}: {exc}"}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
