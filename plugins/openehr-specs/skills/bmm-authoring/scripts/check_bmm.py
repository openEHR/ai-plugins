#!/usr/bin/env python3
"""Check an openEHR BMM schema in P_BMM JSON form for the mistakes bmm-publisher accepts silently.

Python 3.8+, standard library only. Reads the files, writes nothing. See ../SKILL.md for when to run
it and ../references/p-bmm-json.md for the format.

  check_bmm.py SCHEMA.bmm.json [-d DEPENDENCY.bmm.json ...] [--strict]

-d loads another schema (for example the BASE schema that RM includes) so that type names it
defines resolve; it is not checked itself. Without it, names that only an included schema could
define cannot be checked, and neither can the generic parameters and constraints of those types.

Each finding is printed as `LEVEL  /json/path: message`, then a summary line. ERROR: bmm-publisher
fails, or silently reads something other than what the file says, or a generic argument breaks its
parameter's constraint. WARNING: a convention is broken, or the file holds something the publisher
does not read. INFO: what could not be checked.
Exit status: 0 when the check is complete and found no ERROR (with --strict, no WARNING either);
1 when it found an ERROR (with --strict, or a WARNING); 3 when it found none but could not check
every name, because an included schema was not loaded with -d (with errors as well, the status is 1,
and the summary and an "incomplete" notice still say how many names went unchecked); 2 when a file
cannot be read, is not UTF-8 JSON, is nested too deeply, or (for -d) is not a BMM schema.
"""
import argparse
import difflib
import json
import re
import sys
from pathlib import Path

# Keys that bmm-publisher reads (through the cadasto/openehr-bmm library), per kind of object.
_PROPERTY = {"_type", "name", "documentation", "is_mandatory"}
_PARAMETER = {"_type", "name", "documentation", "is_nullable"}
_ENUMERATION = {"_type", "name", "documentation", "ancestors", "item_names", "item_values",
                "item_documentations", "functions"}
READ_KEYS = {
    "schema": {"bmm_version", "rm_publisher", "schema_name", "rm_release", "schema_revision",
               "schema_lifecycle_state", "schema_description", "schema_author", "includes",
               "packages", "primitive_types", "class_definitions"},
    "include": {"id"},
    "package": {"name", "packages", "classes"},
    "P_BMM_CLASS": {"_type", "name", "documentation", "is_abstract", "ancestors",
                    "generic_parameter_defs", "constants", "properties", "functions", "invariants"},
    "P_BMM_INTERFACE": {"_type", "name", "documentation", "functions"},
    "P_BMM_ENUMERATION_STRING": _ENUMERATION,
    "P_BMM_ENUMERATION_INTEGER": _ENUMERATION,
    "generic_parameter": {"name", "conforms_to_type"},
    "constant": {"name", "documentation", "type", "value"},
    "P_BMM_SINGLE_PROPERTY": _PROPERTY | {"type", "default"},
    "P_BMM_SINGLE_PROPERTY_OPEN": _PROPERTY | {"type", "default"},
    "P_BMM_CONTAINER_PROPERTY": _PROPERTY | {"type_def", "cardinality"},
    "P_BMM_GENERIC_PROPERTY": _PROPERTY | {"type_def"},
    "P_BMM_SIMPLE_TYPE": {"_type", "type"},
    "P_BMM_CONTAINER_TYPE": {"_type", "container_type", "type", "type_def"},
    "P_BMM_GENERIC_TYPE": {"_type", "root_type", "generic_parameters", "generic_parameter_defs"},
    "function": {"name", "aliases", "documentation", "is_abstract", "parameters", "pre_conditions",
                 "post_conditions", "result", "is_nullable"},
    "P_BMM_SINGLE_FUNCTION_PARAMETER": _PARAMETER | {"type"},
    "P_BMM_SINGLE_FUNCTION_PARAMETER_OPEN": _PARAMETER | {"type"},
    "P_BMM_CONTAINER_FUNCTION_PARAMETER": _PARAMETER | {"type_def", "cardinality"},
    "P_BMM_GENERIC_FUNCTION_PARAMETER": _PARAMETER | {"type_def"},
    "cardinality": {"lower", "upper", "lower_unbounded", "upper_unbounded"},
}

# Keys the persistence specification knows that bmm-publisher does not read: they stay in the JSON
# but are missing from every generated output, including the ODIN and YAML forms.
_SPEC_PROPERTY = {"is_computed", "is_im_infrastructure", "is_im_runtime", "type_ref"}
SPEC_ONLY_KEYS = {
    "schema": {"model_name", "schema_contributors", "archetype_parent_class",
               "archetype_data_value_parent_class", "archetype_rm_closure_packages",
               "archetype_visualise_descendants_of"},
    "P_BMM_CLASS": {"ancestor_defs", "is_override"},
    "P_BMM_ENUMERATION_STRING": {"ancestor_defs"},
    "P_BMM_ENUMERATION_INTEGER": {"ancestor_defs"},
    "P_BMM_SINGLE_PROPERTY": _SPEC_PROPERTY,
    "P_BMM_SINGLE_PROPERTY_OPEN": _SPEC_PROPERTY,
    "P_BMM_CONTAINER_PROPERTY": _SPEC_PROPERTY,
    "P_BMM_GENERIC_PROPERTY": _SPEC_PROPERTY,
    "P_BMM_SIMPLE_TYPE": {"value_constraint"},
    "P_BMM_CONTAINER_TYPE": {"index_type"},
    "P_BMM_GENERIC_TYPE": {"value_constraint"},
}
HASH_HINT = "write Hash<K,V> as P_BMM_GENERIC_PROPERTY with root_type Hash and two generic_parameters"
# Spec-only keys whose loss changes what the tables show: ERROR rather than WARNING.
LOSSY_KEYS = {("P_BMM_CONTAINER_TYPE", "index_type"): "the index is dropped, so a Hash renders as its "
                                                      "container_type; " + HASH_HINT}

HEADER_REQUIRED = ["rm_publisher", "schema_name", "rm_release", "schema_revision",
                   "schema_lifecycle_state", "schema_description", "schema_author"]
CLASS_TYPES = ["P_BMM_CLASS", "P_BMM_INTERFACE", "P_BMM_ENUMERATION_STRING", "P_BMM_ENUMERATION_INTEGER"]
PROPERTY_TYPES = ["P_BMM_SINGLE_PROPERTY", "P_BMM_SINGLE_PROPERTY_OPEN", "P_BMM_CONTAINER_PROPERTY",
                  "P_BMM_GENERIC_PROPERTY"]
TYPE_TYPES = ["P_BMM_SIMPLE_TYPE", "P_BMM_CONTAINER_TYPE", "P_BMM_GENERIC_TYPE"]
PARAMETER_TYPES = ["P_BMM_SINGLE_FUNCTION_PARAMETER", "P_BMM_SINGLE_FUNCTION_PARAMETER_OPEN",
                   "P_BMM_CONTAINER_FUNCTION_PARAMETER", "P_BMM_GENERIC_FUNCTION_PARAMETER"]
UNSUPPORTED_TYPES = {
    "P_BMM_INDEXED_CONTAINER_PROPERTY": HASH_HINT,
    "P_BMM_INDEXED_CONTAINER_TYPE": HASH_HINT,
}
SIMPLE, CONTAINER, GENERIC = TYPE_TYPES
# bmm-publisher writes class tables for packages down to this depth (top-level package = 1)
MAX_PACKAGE_DEPTH = 4
# an AsciiDoc attribute reference such as {base_release}; bmm-publisher escapes it, so it never resolves
ATTRIBUTE_REF = re.compile(r"\{[a-z][a-z0-9_]*\}")
# result type of a procedure in the published schemas; bmm-publisher prints it without a link
PROCEDURE_RESULT = "void"
GENERIC_NAME = re.compile(r"[<>,]")


class Checker:
    def __init__(self, schema_path, dependency_paths=()):
        self.path = Path(schema_path)
        self.findings = []  # (level, path, message)
        self.data = load(self.path)
        self.classes = {}  # class name -> summary (see summarise), for this schema
        self.class_paths = {}  # class name -> JSON path of its definition
        self.unchecked = set()  # type names an included but unloaded schema might define
        self.suggestions = {}  # unchecked name -> a close name of a loaded class
        self.missing_includes = set()
        self.dependencies = {}  # schema id -> {class name: summary}
        own_id = schema_id(self.data) if isinstance(self.data, dict) else None
        for dep in dependency_paths:
            dep_data = load(Path(dep))
            if not isinstance(dep_data, dict) or not all(
                    isinstance(dep_data.get(k), str) for k in ("rm_publisher", "schema_name", "rm_release")):
                raise SystemExit(fail("%s is not a BMM schema (it needs rm_publisher, schema_name and "
                                      "rm_release)" % dep))
            dep_id = schema_id(dep_data)
            if dep_id == own_id:
                self.warning("/", "-d %s is the schema being checked; it is ignored" % dep)
            elif dep_id in self.dependencies:
                self.warning("/", "-d %s has the same schema id as another -d file (%s); their classes "
                                  "are merged" % (dep, dep_id))
                self.dependencies[dep_id].update(class_index(dep_data))
            else:
                self.dependencies[dep_id] = class_index(dep_data)

    # --- reporting -------------------------------------------------------------------------
    def error(self, path, message):
        self.findings.append(("ERROR", path, message))

    def warning(self, path, message):
        self.findings.append(("WARNING", path, message))

    def info(self, path, message):
        self.findings.append(("INFO", path, message))

    def count(self, level):
        return sum(1 for f in self.findings if f[0] == level)

    # --- driver ----------------------------------------------------------------------------
    def run(self):
        d = self.data
        if not isinstance(d, dict):
            self.error("/", "the schema must be a JSON object")
            return self
        self.check_header(d)
        self.collect_classes(d)
        listed = self.check_packages(d)
        for section, name, cls in self.class_blocks(d):
            path = "/%s/%s" % (section, name)
            self.check_class(cls, path)
            cls_name = cls.get("name")
            if isinstance(cls_name, str) and cls_name not in listed:
                self.error(path, "class is not listed in any package, so no class table is generated for it")
        self.check_ancestor_cycles(d)
        if self.unchecked:
            names = ["%s (or %s?)" % (n, self.suggestions[n]) if n in self.suggestions else n
                     for n in sorted(self.unchecked)]
            self.info("/includes", "not checked, as no loaded schema defines them; pass each included "
                                   "schema with -d: " + ", ".join(names))
        return self

    def class_blocks(self, d):
        """(section, key, class) for every class definition that is an object."""
        for section in ("primitive_types", "class_definitions"):
            block = d.get(section)
            if isinstance(block, dict):
                for key, cls in block.items():
                    if isinstance(cls, dict):
                        yield section, key, cls

    # --- header ----------------------------------------------------------------------------
    def check_header(self, d):
        if "bmm_version" not in d:
            self.warning("/bmm_version", "missing; bmm-publisher assumes \"2.4\"")
        elif d["bmm_version"] != "2.4":
            self.warning("/bmm_version", "the published openEHR schemas use \"2.4\"")
        for key in HEADER_REQUIRED:
            if key not in d:
                self.error("/" + key, "required header field is missing; bmm-publisher refuses the file")
            elif not isinstance(d[key], str):
                self.error("/" + key, "must be a string")
        self.check_keys(d, "schema", "")
        release = d.get("rm_release")
        if isinstance(release, str):
            if not re.fullmatch(r"\d+\.\d+\.\d+", release):
                self.warning("/rm_release", "expected a 3-part numeric release such as 1.2.0")
            revision = d.get("schema_revision")
            if isinstance(revision, str) and not revision.startswith(release + "."):
                self.warning("/schema_revision", "published schemas use <rm_release>.<build>, "
                                                 "for example %s.1" % release)
        if all(isinstance(d.get(k), str) for k in ("rm_publisher", "schema_name", "rm_release")):
            expected = schema_id(d) + ".bmm.json"
            if self.path.name != expected:
                self.warning("/", "file name %s does not match the schema id; expected %s"
                             % (self.path.name, expected))
        included = set()
        includes = d.get("includes")
        if includes is not None and not isinstance(includes, dict):
            self.error("/includes", "must be an object keyed by schema id")
        elif includes:
            for key, inc in includes.items():
                path = "/includes/" + key
                if not isinstance(inc, dict) or not isinstance(inc.get("id"), str):
                    self.error(path, "each include needs an \"id\" naming the included schema")
                    continue
                self.check_keys(inc, "include", path)
                included.add(inc["id"])
                if inc["id"] != key:
                    self.warning(path, "published schemas key each include by its id (%s)" % inc["id"])
        for dep_id in self.dependencies:
            if dep_id not in included:
                self.warning("/includes", "schema %s was loaded with -d but is not included" % dep_id)
        self.missing_includes = included - set(self.dependencies)

    # --- classes and packages ----------------------------------------------------------------
    def collect_classes(self, d):
        for section in ("primitive_types", "class_definitions"):
            block = d.get(section)
            if block is None:
                continue
            if not isinstance(block, dict):
                self.error("/" + section, "must be an object keyed by class name")
                continue
            for key, cls in block.items():
                path = "/%s/%s" % (section, key)
                if not isinstance(cls, dict):
                    self.error(path, "a class definition must be an object")
                    continue
                name = cls.get("name")
                if not isinstance(name, str):
                    self.error(path, "class has no \"name\"")
                    continue
                if name != key:
                    self.error(path, "key and \"name\" (%s) differ; bmm-publisher uses the name" % name)
                if name in self.class_paths:
                    self.error(path, "class %s is also defined at %s" % (name, self.class_paths[name]))
                self.class_paths[name] = path
                self.classes[name] = summarise(cls)
        for dep_id, dep_classes in self.dependencies.items():
            for name in sorted(set(self.classes) & set(dep_classes)):
                self.warning(self.class_paths[name], "class %s is also defined in %s" % (name, dep_id))

    def check_packages(self, d):
        listed = {}
        packages = d.get("packages")
        if not isinstance(packages, dict) or not packages:
            self.error("/packages", "must be an object keyed by package name, with at least one package")
            return listed
        publisher, schema_name = d.get("rm_publisher"), d.get("schema_name")
        for key, pkg in packages.items():
            path = "/packages/" + key
            if publisher == "openehr" and isinstance(schema_name, str) and isinstance(pkg, dict):
                root = "org.openehr." + schema_name.lower()
                name = pkg.get("name")
                if not isinstance(name, str):
                    pass  # reported by check_package
                elif name != root and not name.startswith(root + "."):
                    self.warning(path, "class table file names are built from %s.<package>; name the "
                                       "top-level package %s.<package>, or %s with sub-packages"
                                 % (root, root, root))
                elif name == root and pkg.get("classes"):
                    self.warning(path + "/classes", "classes listed directly in %s get table files named "
                                                    "%s.org.<class>.adoc; list them in a sub-package"
                                 % (root, root))
            self.check_package(pkg, key, path, listed, depth=1)
        return listed

    def check_package(self, pkg, key, path, listed, depth):
        if not isinstance(pkg, dict):
            self.error(path, "a package must be an object")
            return
        self.check_keys(pkg, "package", path)
        name = pkg.get("name")
        if not isinstance(name, str):
            self.error(path, "package has no \"name\"")
        elif name != key:
            self.error(path, "key and \"name\" (%s) differ" % name)
        elif depth > 1 and "." in name:
            self.error(path, "only top-level package names may contain '.'")
        classes = pkg.get("classes", [])
        subpackages = pkg.get("packages", {})
        if not isinstance(classes, list) or not all(isinstance(c, str) for c in classes):
            self.error(path + "/classes", "must be a list of class names")
            classes = []
        if not isinstance(subpackages, dict):
            self.error(path + "/packages", "must be an object keyed by package name")
            subpackages = {}
        if not classes and not subpackages:
            self.warning(path, "empty package")
        if classes and depth > MAX_PACKAGE_DEPTH:
            self.error(path, "bmm-publisher visits packages only %d levels deep, so these classes get no "
                             "class table" % MAX_PACKAGE_DEPTH)
        for cls in classes:
            if cls not in self.classes:
                self.error(path + "/classes", "%s is not defined in this schema; bmm-publisher stops "
                                              "with 'Class %s not found in schema'" % (cls, cls))
            elif cls in listed:
                self.warning(path + "/classes", "%s is also listed in %s" % (cls, listed[cls]))
            else:
                listed[cls] = path
        for sub_key, sub in subpackages.items():
            self.check_package(sub, sub_key, path + "/packages/" + sub_key, listed, depth + 1)

    def check_class(self, cls, path):
        kind, recognised = self.kind_of(cls, path, CLASS_TYPES, "P_BMM_CLASS", "a plain class")
        # with an unknown _type bmm-publisher reads a plain class, so that is what decides which keys it drops
        self.check_keys(cls, kind if recognised else "P_BMM_CLASS", path)
        self.check_documentation(cls, path, required=True)
        scope = {}  # generic parameter name -> its conforms_to_type, or None
        params = cls.get("generic_parameter_defs")
        if params is not None and not isinstance(params, dict):
            self.error(path + "/generic_parameter_defs", "must be an object keyed by parameter name")
        elif params:
            for key, param in params.items():
                p_path = path + "/generic_parameter_defs/" + key
                if not isinstance(param, dict) or param.get("name") != key:
                    self.error(p_path, "needs a \"name\" equal to its key")
                    continue
                self.check_keys(param, "generic_parameter", p_path)
                constraint = param.get("conforms_to_type")
                if constraint is not None and not isinstance(constraint, str):
                    self.error(p_path + "/conforms_to_type", "must be a class name")
                    constraint = None
                scope[key] = constraint
            for key, constraint in scope.items():
                if constraint is not None:
                    self.check_type_name(constraint, path + "/generic_parameter_defs/" + key
                                         + "/conforms_to_type", scope)
        if "is_abstract" in cls and not isinstance(cls["is_abstract"], bool):
            self.error(path + "/is_abstract", "must be true or false")
        ancestors = cls.get("ancestors", [])
        if not isinstance(ancestors, list) or not all(isinstance(a, str) for a in ancestors):
            self.error(path + "/ancestors", "must be a list of class names")
            ancestors = []
        self.check_ancestor_defs(cls, ancestors, path)
        for i, ancestor in enumerate(ancestors):
            a_path = "%s/ancestors/%d" % (path, i)
            if GENERIC_NAME.search(ancestor):
                self.error(a_path, "ancestors name classes only; for generic inheritance give the "
                                   "root class (%s) and declare the parameters in generic_parameter_defs"
                           % ancestor.split("<")[0].strip())
            else:
                self.check_type_name(ancestor, a_path, {})
        if kind.startswith("P_BMM_ENUMERATION"):
            self.check_enumeration(cls, kind, ancestors if "ancestors" in cls else None, path)
        for key, constant in self.keyed(cls, "constants", path):
            c_path = path + "/constants/" + key
            self.check_name(constant, c_path)
            self.check_keys(constant, "constant", c_path)
            if not isinstance(constant.get("type"), str):
                self.error(c_path, "a constant needs a \"type\"; bmm-publisher fails without one")
            else:
                self.check_type_name(constant["type"], c_path + "/type", scope)
            self.check_documentation(constant, c_path)
        for key, prop in self.keyed(cls, "properties", path):
            self.check_property(prop, path + "/properties/" + key, scope)
        for key, function in self.keyed(cls, "functions", path):
            self.check_function(function, path + "/functions/" + key, scope)
        self.check_assertions(cls, "invariants", path)

    def check_ancestor_defs(self, cls, ancestors, path):
        """bmm-publisher reads only ancestors: a parent named only in ancestor_defs is lost."""
        defs = cls.get("ancestor_defs")
        if defs is None:
            return
        entries = list(defs.items()) if isinstance(defs, dict) else list(enumerate(defs)) \
            if isinstance(defs, list) else []
        roots = []
        for key, entry in entries:
            if isinstance(entry, dict) and isinstance(entry.get("root_type") or entry.get("type"), str):
                roots.append(entry.get("root_type") or entry.get("type"))
            elif isinstance(key, str):
                roots.append(key.split("<")[0].strip())
        lost = [r for r in roots if r not in ancestors]
        if lost:
            self.error(path + "/ancestor_defs", "bmm-publisher reads only \"ancestors\", so the parent %s "
                                                "lost; list the root class name there (for an open binding "
                                                "such as A<T>, also redeclare T in generic_parameter_defs; "
                                                "state a closed binding in documentation)"
                       % ("%s is" % lost[0] if len(lost) == 1 else "%s are" % ", ".join(lost)))

    def check_enumeration(self, cls, kind, ancestors, path):
        names = cls.get("item_names")
        if not isinstance(names, list) or not names or not all(isinstance(n, str) for n in names):
            self.error(path + "/item_names", "an enumeration needs a non-empty list of item names")
            return
        integer = kind == "P_BMM_ENUMERATION_INTEGER"
        if integer and ancestors is not None and "Integer" not in ancestors:
            self.warning(path + "/ancestors", "the table prints item values only when Integer is among "
                                              "the ancestors")
        values = cls.get("item_values")
        if values is not None:
            value_type = int if integer else str
            if not isinstance(values, list) or len(values) != len(names):
                self.error(path + "/item_values", "needs one value per item name (%d)" % len(names))
            elif not all(isinstance(v, value_type) and not isinstance(v, bool) for v in values):
                self.error(path + "/item_values", "values must be %s" % ("integers" if integer else "strings"))
        docs = cls.get("item_documentations")
        if docs is not None and (not isinstance(docs, list) or len(docs) != len(names)
                                 or not all(isinstance(t, str) for t in docs)):
            self.error(path + "/item_documentations", "needs one text per item name (%d); the "
                                                      "table pairs them by position" % len(names))

    def check_ancestor_cycles(self, d):
        graph = {}
        for _, _, cls in self.class_blocks(d):
            ancestors = cls.get("ancestors")
            if isinstance(cls.get("name"), str):
                graph[cls["name"]] = [a for a in ancestors if isinstance(a, str)] \
                    if isinstance(ancestors, list) else []
        state = {}

        def visit(name, trail):
            state[name] = 1
            for ancestor in graph.get(name, []):
                if state.get(ancestor) == 1:
                    self.error(self.class_paths.get(name, "/"), "inheritance cycle: "
                               + " -> ".join(trail + [ancestor]))
                elif ancestor in graph and not state.get(ancestor):
                    visit(ancestor, trail + [ancestor])
            state[name] = 2

        for name in graph:
            if not state.get(name):
                visit(name, [name])

    # --- properties, functions and types -----------------------------------------------------
    def check_property(self, prop, path, scope):
        kind = prop.get("_type")
        if kind is None:
            if "type_def" in prop:
                self.error(path, "no _type: read as P_BMM_SINGLE_PROPERTY, whose type then defaults "
                                 "to Any; set the property _type")
                kind = self.closest_kind_from_shape(prop)
            else:
                self.warning(path, "no _type: read as P_BMM_SINGLE_PROPERTY; published schemas always set it")
                kind = "P_BMM_SINGLE_PROPERTY"
        elif isinstance(kind, str) and kind in UNSUPPORTED_TYPES:
            self.error(path, "bmm-publisher does not read %s (it becomes a property of type Any); %s"
                       % (kind, UNSUPPORTED_TYPES[kind]))
            self.check_name(prop, path)
            self.check_documentation(prop, path, required=True)
            return
        else:
            kind, _ = self.kind_of(prop, path, PROPERTY_TYPES, "P_BMM_SINGLE_PROPERTY", "P_BMM_SINGLE_PROPERTY")
        self.check_name(prop, path)
        self.check_keys(prop, kind, path)
        self.check_documentation(prop, path, required=True)
        if "is_mandatory" in prop and not isinstance(prop["is_mandatory"], bool):
            self.error(path + "/is_mandatory", "must be true or false")
        if kind in ("P_BMM_SINGLE_PROPERTY", "P_BMM_SINGLE_PROPERTY_OPEN"):
            target = prop.get("type")
            if not isinstance(target, str):
                hint = " (a value-set constraint in type_ref is not read)" if "type_ref" in prop else ""
                self.error(path, "no \"type\": the property is read as type Any" + hint)
            elif GENERIC_NAME.search(target):
                self.error(path + "/type", "%s is not a class name; use P_BMM_CONTAINER_PROPERTY or "
                                           "P_BMM_GENERIC_PROPERTY with a type_def" % target)
            elif kind == "P_BMM_SINGLE_PROPERTY_OPEN":
                if target not in scope:
                    self.error(path + "/type", "%s is not a generic parameter of this class" % target)
            elif target in scope:
                self.warning(path, "type %s is a generic parameter: use P_BMM_SINGLE_PROPERTY_OPEN" % target)
            else:
                self.check_type_name(target, path + "/type", scope)
        elif kind == "P_BMM_CONTAINER_PROPERTY":
            self.check_inline_type(prop, CONTAINER, path, scope)
            if "cardinality" in prop:
                self.check_cardinality(prop["cardinality"], path + "/cardinality")
        else:
            self.check_inline_type(prop, GENERIC, path, scope)

    def closest_kind_from_shape(self, prop):
        type_def = prop.get("type_def")
        if isinstance(type_def, dict) and "root_type" in type_def:
            return "P_BMM_GENERIC_PROPERTY"
        return "P_BMM_CONTAINER_PROPERTY"

    def check_inline_type(self, owner, kind, path, scope):
        type_def = owner.get("type_def")
        if not isinstance(type_def, dict):
            self.error(path, "needs a \"type_def\" object")
            return
        marker = type_def.get("_type", kind)
        if marker != kind:
            self.error(path + "/type_def", "_type %s is ignored here: this type_def is always read as %s"
                       % (marker if isinstance(marker, str) else "(not a string)", kind))
        self.check_type_body(type_def, kind, path + "/type_def", scope)

    def check_type(self, t, path, scope):
        """A nested type object (result, generic parameter, element type_def). Returns the kind
        it is checked as, or None when it is not an object or bmm-publisher cannot read it."""
        if not isinstance(t, dict):
            self.error(path, "a type must be an object")
            return None
        kind = t.get("_type")
        if kind is None:
            if "container_type" in t or "root_type" in t:
                self.error(path, "no _type: a nested type is read as P_BMM_SIMPLE_TYPE; set _type")
                kind = GENERIC if "root_type" in t else CONTAINER
            else:
                self.warning(path, "no _type: read as P_BMM_SIMPLE_TYPE; published schemas always set it")
                kind = SIMPLE
        elif isinstance(kind, str) and kind in UNSUPPORTED_TYPES:
            self.error(path, "bmm-publisher does not read %s (it becomes a simple type); %s"
                       % (kind, UNSUPPORTED_TYPES[kind]))
            return None
        elif kind == "P_BMM_OPEN_TYPE":
            self.warning(path, "read as P_BMM_SIMPLE_TYPE; published schemas write P_BMM_SIMPLE_TYPE")
            kind = SIMPLE
        else:
            kind, _ = self.kind_of(t, path, TYPE_TYPES, SIMPLE, SIMPLE)
        self.check_type_body(t, kind, path, scope)
        return kind

    def check_type_body(self, t, kind, path, scope):
        self.check_keys(t, kind, path)
        if kind == SIMPLE:
            target = t.get("type")
            if not isinstance(target, str):
                self.error(path, "needs a \"type\"")
            elif GENERIC_NAME.search(target):
                self.error(path + "/type", "%s is not a class name; use P_BMM_CONTAINER_TYPE or "
                                           "P_BMM_GENERIC_TYPE" % target)
            else:
                self.check_type_name(target, path + "/type", scope)
        elif kind == CONTAINER:
            self.check_container_type(t, path, scope)
        else:
            self.check_generic_type(t, path, scope)

    def check_container_type(self, t, path, scope):
        container = t.get("container_type")
        if not isinstance(container, str):
            self.error(path, "needs a \"container_type\" (List, Set, Array)")
        else:
            self.check_type_name(container, path + "/container_type", scope)
            arity = self.arity(container)
            if arity is not None and arity != 1:
                self.error(path + "/container_type", "%s takes %d generic parameters; %s"
                           % (container, arity, HASH_HINT))
        has_type, has_def = "type" in t, "type_def" in t
        if has_type == has_def:
            self.error(path, "give the element type as either \"type\" (a name) or \"type_def\" "
                             "(a nested type), not %s" % ("both" if has_type else "neither: it is read as Any"))
        elif has_type:
            if not isinstance(t["type"], str) or GENERIC_NAME.search(t["type"]):
                self.error(path + "/type", "must be a class or parameter name; nest other types "
                                           "in \"type_def\"")
            else:
                self.check_type_name(t["type"], path + "/type", scope)
        elif self.check_type(t["type_def"], path + "/type_def", scope) == SIMPLE:
            self.error(path + "/type_def", "a simple element type goes in \"type\": bmm-publisher renders "
                                           "a simple type in \"type_def\" as Any")

    def check_generic_type(self, t, path, scope):
        root = t.get("root_type")
        if not isinstance(root, str):
            self.error(path, "needs a \"root_type\"")
        else:
            self.check_type_name(root, path + "/root_type", scope)
        simple = t.get("generic_parameters")
        nested = t.get("generic_parameter_defs")
        if simple is not None and not isinstance(simple, list):
            self.error(path + "/generic_parameters", "must be a list of class or parameter names")
            simple = None
        if nested is not None and not isinstance(nested, dict):
            self.error(path + "/generic_parameter_defs", "must be an object of nested types keyed by "
                                                         "parameter name")
            nested = None
        params = self.lookup(root)["params"] if isinstance(root, str) and self.lookup(root) else None
        args = []  # (argument class or parameter name, or None; JSON path), in binding order
        if simple and nested:
            self.error(path, "bmm-publisher uses generic_parameters and ignores generic_parameter_defs "
                             "when both are given; use one of them")
            for key, param in nested.items():
                self.check_type(param, path + "/generic_parameter_defs/" + key, scope)
        if simple:
            for i, param in enumerate(simple):
                args.append(self.check_simple_argument(param, "%s/generic_parameters/%d" % (path, i), scope))
        elif nested:
            for i, (key, param) in enumerate(nested.items()):
                p_path = path + "/generic_parameter_defs/" + key
                args.append(self.check_nested_argument(param, p_path, scope))
                if params is not None and i < len(params) and key != params[i][0]:
                    self.warning(p_path, "generic_parameter_defs bind by position: entry %d is parameter %s "
                                         "of %s" % (i + 1, params[i][0], root))
        if not args:
            self.error(path, "a generic type needs generic_parameters or generic_parameter_defs")
        elif params is not None and len(params) != len(args):
            self.error(path, "%s takes %d generic parameters, %d given" % (root, len(params), len(args)))
        elif params:
            self.check_generic_arguments(root, params, args, scope)

    def check_simple_argument(self, param, path, scope):
        """An entry of generic_parameters: returns (argument name or None, path)."""
        if isinstance(param, str):
            if GENERIC_NAME.search(param):
                self.error(path, "must be a class or parameter name; nest other types in "
                                 "generic_parameter_defs")
                return None, path
            self.check_type_name(param, path, scope)
            return param, path
        if isinstance(param, dict):
            # BASE writes nested generic types here (FUNCTION<TUPLE1<T>, Boolean>), and bmm-publisher reads them
            kind = self.check_type(param, path, scope)
            if kind == GENERIC:
                return param.get("root_type"), path
            if kind is not None:
                self.error(path, "bmm-publisher accepts only names and generic types here and stops with "
                                 "a type error on a %s" % kind)
            return None, path
        self.error(path, "must be a class or parameter name")
        return None, path

    def check_nested_argument(self, param, path, scope):
        """An entry of generic_parameter_defs: returns (argument name or None, path)."""
        kind = self.check_type(param, path, scope)
        if kind == CONTAINER:
            self.error(path, "bmm-publisher prints nothing for a container type in generic_parameter_defs; "
                             "use a generic type with root_type List instead")
            return param.get("container_type"), path
        if kind == GENERIC:
            return param.get("root_type"), path
        if kind == SIMPLE:
            return param.get("type"), path
        return None, path

    def check_generic_arguments(self, root, params, args, scope):
        """Each argument, bound by position, must conform to its parameter's conforms_to_type."""
        names = ", ".join(p for p, _ in params)
        for (param, constraint), (arg, arg_path) in zip(params, args):
            if not constraint or constraint == "Any" or not isinstance(arg, str):
                continue
            # an argument that is a parameter of the enclosing class conforms through its own constraint
            effective = (scope[arg] or "Any") if arg in scope else arg
            if self.conforms(effective, constraint) is False:
                what = arg if effective == arg else "%s (constrained to %s)" % (arg, effective)
                self.error(arg_path, "%s does not conform to %s, the constraint on parameter %s of %s "
                                     "(arguments bind in the order %s declares its parameters: %s)"
                           % (what, constraint, param, root, root, names))

    def check_function(self, function, path, scope):
        self.check_name(function, path)
        self.check_keys(function, "function", path)
        self.check_documentation(function, path, required=True)
        for flag in ("is_abstract", "is_nullable"):
            if flag in function and not isinstance(function[flag], bool):
                self.error(path + "/" + flag, "must be true or false")
        aliases = function.get("aliases", [])
        if not isinstance(aliases, list) or not all(isinstance(a, str) for a in aliases):
            self.error(path + "/aliases", "must be a list of names, as the published schemas write it")
        result = function.get("result")
        if result is None:
            self.warning(path, "no result: the specification reads that as a procedure, but the table "
                               "prints an empty result type; published schemas write the result type void")
        elif not (isinstance(result, dict) and result.get("type") == PROCEDURE_RESULT
                  and result.get("_type", SIMPLE) == SIMPLE):
            self.check_type(result, path + "/result", scope)
        for key, param in self.keyed(function, "parameters", path):
            self.check_parameter(param, path + "/parameters/" + key, scope)
        self.check_assertions(function, "pre_conditions", path)
        self.check_assertions(function, "post_conditions", path)

    def check_parameter(self, param, path, scope):
        kind = param.get("_type")
        if kind is None:
            if "type_def" in param:
                self.error(path, "no _type: read as P_BMM_SINGLE_FUNCTION_PARAMETER of type Any")
                type_def = param.get("type_def")
                kind = "P_BMM_GENERIC_FUNCTION_PARAMETER" if isinstance(type_def, dict) and "root_type" in type_def \
                    else "P_BMM_CONTAINER_FUNCTION_PARAMETER"
            else:
                kind = "P_BMM_SINGLE_FUNCTION_PARAMETER"
        else:
            kind, _ = self.kind_of(param, path, PARAMETER_TYPES, "P_BMM_SINGLE_FUNCTION_PARAMETER",
                                   "P_BMM_SINGLE_FUNCTION_PARAMETER")
        self.check_name(param, path)
        self.check_keys(param, kind, path)
        self.check_documentation(param, path)
        if "is_nullable" in param and not isinstance(param["is_nullable"], bool):
            self.error(path + "/is_nullable", "must be true or false")
        if kind in ("P_BMM_SINGLE_FUNCTION_PARAMETER", "P_BMM_SINGLE_FUNCTION_PARAMETER_OPEN"):
            target = param.get("type")
            if not isinstance(target, str) or GENERIC_NAME.search(target):
                self.error(path, "needs a \"type\" naming a class or generic parameter")
            elif kind.endswith("_OPEN") and target not in scope:
                self.error(path + "/type", "%s is not a generic parameter of this class" % target)
            else:
                self.check_type_name(target, path + "/type", scope)
        elif kind == "P_BMM_CONTAINER_FUNCTION_PARAMETER":
            self.check_inline_type(param, CONTAINER, path, scope)
            if "cardinality" in param:
                self.check_cardinality(param["cardinality"], path + "/cardinality")
        else:
            self.check_inline_type(param, GENERIC, path, scope)

    def check_cardinality(self, card, path):
        if not isinstance(card, dict):
            self.error(path, "must be an object such as {\"lower\": 0, \"upper_unbounded\": true}")
            return
        self.check_keys(card, "cardinality", path)
        for key in ("lower", "upper"):
            if key in card and (not isinstance(card[key], int) or isinstance(card[key], bool) or card[key] < 0):
                self.error(path + "/" + key, "must be a non-negative integer")
        for key in ("lower_unbounded", "upper_unbounded"):
            if key in card and not isinstance(card[key], bool):
                self.error(path + "/" + key, "must be true or false")
        if "upper" in card and card.get("upper_unbounded", True) is not False:
            self.error(path, "an upper limit needs \"upper_unbounded\": false; bmm-publisher treats a "
                             "missing upper_unbounded as true and ignores the limit")
        if card.get("upper_unbounded") is False and "upper" not in card:
            self.error(path, "\"upper_unbounded\": false needs an \"upper\" limit")
        lower, upper = card.get("lower"), card.get("upper")
        if is_count(lower) and is_count(upper) and upper < lower:
            self.error(path, "upper is below lower")
        if card.get("lower_unbounded") is True:
            self.warning(path + "/lower_unbounded", "a cardinality has a lower limit (0 or more)")

    # --- shared helpers ------------------------------------------------------------------------
    def kind_of(self, item, path, kinds, read_as, read_as_label):
        """(kind, recognised): the _type an item is checked as, and whether bmm-publisher knows it. An
        unknown _type is reported with what bmm-publisher reads it as, and the item is then checked as
        the closest known _type, so that its content is still checked."""
        kind = item.get("_type", kinds[0])
        if isinstance(kind, str) and kind in kinds:
            return kind, True
        if not isinstance(kind, str):
            self.error(path + "/_type", "must be a string; read as %s" % read_as_label)
            return read_as, False
        close = difflib.get_close_matches(kind, kinds, n=1, cutoff=0.6)
        checked = close[0] if close else read_as
        self.error(path, "unknown _type %s: read as %s%s" % (kind, read_as_label,
                                                            "; checked below as " + checked if close else ""))
        return checked, False

    def keyed(self, owner, key, path):
        block = owner.get(key)
        if block is None:
            return []
        if not isinstance(block, dict):
            self.error(path + "/" + key, "must be an object keyed by name")
            return []
        items = []
        for item_key, item in block.items():
            if not isinstance(item, dict):
                self.error("%s/%s/%s" % (path, key, item_key), "must be an object")
            else:
                items.append((item_key, item))
        return items

    def check_name(self, item, path):
        key = path.rsplit("/", 1)[-1]
        name = item.get("name")
        if not isinstance(name, str):
            self.error(path, "has no \"name\"")
        elif name != key:
            self.error(path, "key and \"name\" (%s) differ; keep them equal (depending on the map, the "
                             "tables show one or both)" % name)

    def check_keys(self, item, kind, path):
        for key in item:
            if key in READ_KEYS[kind]:
                continue
            k_path = "%s/%s" % (path, key)
            if key in SPEC_ONLY_KEYS.get(kind, ()):
                if (kind, key) in LOSSY_KEYS:
                    self.error(k_path, "not read by bmm-publisher: " + LOSSY_KEYS[(kind, key)])
                else:
                    self.warning(k_path, "known to the persistence specification but not read by "
                                         "bmm-publisher, so it is missing from every output")
            elif kind in CLASS_TYPES[1:] and key in READ_KEYS["P_BMM_CLASS"]:
                self.error(k_path, "bmm-publisher does not read %s on a %s, so it is lost" % (key, kind))
            elif self.misspelling(key, kind, item):
                near = self.misspelling(key, kind, item)
                self.error(k_path, "unknown key, probably a misspelling of %s; bmm-publisher ignores it, "
                                   "so %s keeps its default" % (near, near))
            else:
                self.warning(k_path, "unknown key, ignored by bmm-publisher (expected one of: %s)"
                             % ", ".join(sorted(READ_KEYS[kind])))

    def misspelling(self, key, kind, item):
        near = difflib.get_close_matches(key, sorted(READ_KEYS[kind]), n=1, cutoff=0.8)
        return near[0] if near and near[0] not in item else None

    def check_documentation(self, item, path, required=False):
        doc = item.get("documentation")
        if doc is None:
            if required:
                self.warning(path, "no documentation: the table description is empty")
            return
        if not isinstance(doc, str):
            self.error(path + "/documentation", "must be a string")
        elif ATTRIBUTE_REF.search(doc):
            self.warning(path + "/documentation", "bmm-publisher escapes the attribute reference %s, so it "
                                                  "is printed literally; write the value"
                         % ATTRIBUTE_REF.search(doc).group(0))

    def check_assertions(self, owner, key, path):
        block = owner.get(key)
        if block is None:
            return
        if not isinstance(block, dict) or not all(isinstance(v, str) for v in block.values()):
            self.error(path + "/" + key, "must be an object mapping a tag to an expression string")

    def lookup(self, name):
        if name in self.classes:
            return self.classes[name]
        for dep_classes in self.dependencies.values():
            if name in dep_classes:
                return dep_classes[name]
        return None

    def arity(self, name):
        info = self.lookup(name)
        return None if info is None else len(info["params"])

    def conforms(self, name, target):
        """True or False; None when the ancestry leaves the loaded schemas, so it cannot be decided."""
        if target == "Any":
            return True
        seen, todo, undecided = set(), [name], False
        while todo:
            current = todo.pop()
            if current == target:
                return True
            if current in seen:
                continue
            seen.add(current)
            info = self.lookup(current)
            if info is None:
                undecided = True
                if self.missing_includes:
                    self.unchecked.add(current)
            else:
                todo.extend(info["ancestors"])
        return None if undecided else False

    def check_type_name(self, name, path, scope):
        if not isinstance(name, str) or not name:
            self.error(path, "must be a non-empty class name")
            return
        if name in scope or self.lookup(name) is not None:
            return
        if name == PROCEDURE_RESULT:
            self.warning(path, "void is only the result type of a procedure")
            return
        if len(name) == 1:
            self.warning(path, "%s is not a generic parameter of this class; declare it in "
                               "generic_parameter_defs" % name)
            return
        known = set(self.classes)
        for dep_classes in self.dependencies.values():
            known.update(dep_classes)
        near = difflib.get_close_matches(name, sorted(known), n=1, cutoff=0.85)
        if self.missing_includes:
            # it may be defined in the include that was not loaded, so it is unchecked, not wrong
            self.unchecked.add(name)
            if near:
                self.suggestions[name] = near[0]
        elif near:
            self.warning(path, "type %s is not defined; did you mean %s?" % (name, near[0]))
        else:
            self.warning(path, "type %s is not defined in this schema or any loaded schema" % name)


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except OSError as exc:
        raise SystemExit(fail("cannot read %s: %s" % (path, exc.strerror or exc)))
    except json.JSONDecodeError as exc:
        raise SystemExit(fail("%s is not valid JSON: %s (line %d, column %d)"
                              % (path, exc.msg, exc.lineno, exc.colno)))
    except UnicodeDecodeError:
        raise SystemExit(fail("%s is not UTF-8 text" % path))
    except RecursionError:
        raise SystemExit(fail("%s is nested too deeply to read" % path))


def fail(message):
    print("check_bmm: " + message, file=sys.stderr)
    return 2


def is_count(value):
    return isinstance(value, int) and not isinstance(value, bool)


def schema_id(d):
    return "%s_%s_%s" % (d.get("rm_publisher"), d.get("schema_name"), d.get("rm_release"))


def summarise(cls):
    """What other classes need to know about a class: its generic parameters and its ancestors."""
    params = cls.get("generic_parameter_defs")
    params = params if isinstance(params, dict) else {}
    ancestors = cls.get("ancestors")
    ancestors = ancestors if isinstance(ancestors, list) else []
    constraints = []
    for key, p in params.items():
        constraint = p.get("conforms_to_type") if isinstance(p, dict) else None
        constraints.append((key, constraint if isinstance(constraint, str) else None))
    return {"params": constraints, "ancestors": [a for a in ancestors if isinstance(a, str)]}


def class_index(d):
    classes = {}
    for section in ("primitive_types", "class_definitions"):
        block = d.get(section)
        if isinstance(block, dict):
            for cls in block.values():
                if isinstance(cls, dict) and isinstance(cls.get("name"), str):
                    classes[cls["name"]] = summarise(cls)
    return classes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("schema", help="the .bmm.json file to check")
    parser.add_argument("-d", "--dependency", action="append", default=[],
                        help="a schema whose classes the checked one uses (repeatable)")
    parser.add_argument("--strict", action="store_true", help="exit 1 on warnings too")
    args = parser.parse_args(argv)
    try:
        checker = Checker(args.schema, args.dependency).run()
    except RecursionError:
        return fail("%s is nested too deeply to check" % args.schema)
    for level, path, message in checker.findings:
        print("%-7s %s: %s" % (level, path, message))
    errors, warnings, unchecked = checker.count("ERROR"), checker.count("WARNING"), len(checker.unchecked)
    print("check_bmm: %s: %d class(es), %d error(s), %d warning(s), %d name(s) not checked"
          % (args.schema, len(checker.classes), errors, warnings, unchecked))
    if unchecked:
        print("check_bmm: incomplete: %d name(s) not checked; pass each included schema with -d before "
              "relying on this result" % unchecked, file=sys.stderr)
    if errors or (args.strict and warnings):
        return 1
    return 3 if unchecked else 0


if __name__ == "__main__":
    sys.exit(main())
