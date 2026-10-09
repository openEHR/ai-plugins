#!/usr/bin/env python3
"""Check an openEHR BMM schema in P_BMM JSON form for the mistakes bmm-publisher accepts silently.

Python 3.8+, standard library only. Reads the files, writes nothing. See ../SKILL.md for when to run
it and ../references/p-bmm-json.md for the format.

  check_bmm.py SCHEMA.bmm.json [-d DEPENDENCY.bmm.json ...] [--strict]

-d loads another schema (for example the BASE schema that RM includes) so that type names it
defines resolve; it is not checked itself. Without it, names that only an included schema could
define are listed once as unchecked.

Each finding is printed as `LEVEL  /json/path: message`, then a summary line. ERROR: bmm-publisher
fails, or silently reads something other than what the file says, or a generic argument breaks its
parameter's constraint. WARNING: a convention is broken, or the file holds something the publisher
does not read. INFO: what could not be checked.
Exit status: 0 when there is no ERROR (and, with --strict, no WARNING); 1 otherwise; 2 when a file
cannot be read or is not JSON.
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

# Keys the P_BMM model defines (LANG, BMM persistence) that bmm-publisher does not read: they stay
# in the JSON but are missing from every generated output, including the ODIN and YAML forms.
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

HEADER_REQUIRED = ["bmm_version", "rm_publisher", "schema_name", "rm_release", "schema_revision",
                   "schema_lifecycle_state", "schema_description", "schema_author"]
CLASS_TYPES = {"P_BMM_CLASS", "P_BMM_INTERFACE", "P_BMM_ENUMERATION_STRING", "P_BMM_ENUMERATION_INTEGER"}
PROPERTY_TYPES = {"P_BMM_SINGLE_PROPERTY", "P_BMM_SINGLE_PROPERTY_OPEN", "P_BMM_CONTAINER_PROPERTY",
                  "P_BMM_GENERIC_PROPERTY"}
TYPE_TYPES = {"P_BMM_SIMPLE_TYPE", "P_BMM_CONTAINER_TYPE", "P_BMM_GENERIC_TYPE"}
PARAMETER_TYPES = {"P_BMM_SINGLE_FUNCTION_PARAMETER", "P_BMM_SINGLE_FUNCTION_PARAMETER_OPEN",
                   "P_BMM_CONTAINER_FUNCTION_PARAMETER", "P_BMM_GENERIC_FUNCTION_PARAMETER"}
HASH_HINT = "write Hash<K,V> as P_BMM_GENERIC_PROPERTY with root_type Hash and two generic_parameters"
UNSUPPORTED_TYPES = {
    "P_BMM_INDEXED_CONTAINER_PROPERTY": HASH_HINT,
    "P_BMM_INDEXED_CONTAINER_TYPE": HASH_HINT,
}
# an AsciiDoc attribute reference such as {base_release}; bmm-publisher escapes it, so it never resolves
ATTRIBUTE_REF = re.compile(r"\{[a-z][a-z0-9_-]*\}")
# result type of a procedure; bmm-publisher prints it without a link
PROCEDURE_RESULT = "void"
GENERIC_NAME = re.compile(r"[<>,]")


class Checker:
    def __init__(self, schema_path, dependency_paths=()):
        self.path = Path(schema_path)
        self.findings = []  # (level, path, message)
        self.data = load(self.path)
        self.dependencies = {}  # schema id -> {class name: summary}, see summarise()
        own_id = schema_id(self.data) if isinstance(self.data, dict) else None
        for dep in dependency_paths:
            dep_data = load(Path(dep))
            if not isinstance(dep_data, dict):
                continue
            if schema_id(dep_data) == own_id:
                self.warning("/", "-d %s is the schema being checked; it is ignored" % dep)
                continue
            self.dependencies[schema_id(dep_data)] = class_index(dep_data)
        self.classes = {}  # class name -> summary, for this schema
        self.unchecked = set()  # type names an included but unloaded schema might define

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
        for section in ("primitive_types", "class_definitions"):
            for name, cls in (d.get(section) or {}).items():
                path = "/%s/%s" % (section, name)
                if isinstance(cls, dict):
                    self.check_class(cls, path)
                    if cls.get("name") not in listed and cls.get("name") is not None:
                        self.error(path, "class is not listed in any package, so no class table is "
                                         "generated for it")
        self.check_ancestor_cycles(d)
        if self.unchecked:
            self.info("/includes", "not checked, as no loaded schema defines them (pass the included "
                                   "schema with -d): " + ", ".join(sorted(self.unchecked)))
        return self

    # --- header ----------------------------------------------------------------------------
    def check_header(self, d):
        for key in HEADER_REQUIRED:
            if key not in d:
                self.error("/" + key, "required header field is missing")
            elif not isinstance(d[key], str):
                self.error("/" + key, "must be a string")
        self.check_keys(d, "schema", "")
        if d.get("bmm_version") not in (None, "2.4"):
            self.warning("/bmm_version", "published openEHR schemas use \"2.4\", the version "
                                         "bmm-publisher reads and writes")
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
        includes = d.get("includes")
        if includes is not None:
            if not isinstance(includes, dict):
                self.error("/includes", "must be an object keyed by schema id")
            else:
                for key, inc in includes.items():
                    path = "/includes/" + key
                    if not isinstance(inc, dict) or not isinstance(inc.get("id"), str):
                        self.error(path, "each include needs an \"id\" naming the included schema")
                        continue
                    self.check_keys(inc, "include", path)
                    if inc["id"] != key:
                        self.warning(path, "published schemas key each include by its id (%s)" % inc["id"])
        included = set(i.get("id") for i in (includes or {}).values() if isinstance(i, dict)) \
            if isinstance(includes, dict) else set()
        for dep_id in self.dependencies:
            if dep_id not in included:
                self.warning("/includes", "schema %s was loaded with -d but is not included" % dep_id)
        self.missing_includes = included - set(self.dependencies)
        if "class_definitions" not in d:
            self.warning("/class_definitions", "the persistence model makes class_definitions mandatory")

    # --- classes and packages ----------------------------------------------------------------
    def collect_classes(self, d):
        seen = {}
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
                if name in seen:
                    self.error(path, "class %s is also defined at %s" % (name, seen[name]))
                seen[name] = path
                self.classes[name] = summarise(cls)
        for dep_id, dep_classes in self.dependencies.items():
            for name in set(self.classes) & set(dep_classes):
                self.warning("/", "class %s is also defined in %s" % (name, dep_id))

    def check_packages(self, d):
        listed = {}
        packages = d.get("packages")
        if not isinstance(packages, dict) or not packages:
            self.error("/packages", "the schema needs at least one package")
            return listed
        publisher, schema_name = d.get("rm_publisher"), d.get("schema_name")
        for key, pkg in packages.items():
            path = "/packages/" + key
            if publisher == "openehr" and isinstance(schema_name, str) and isinstance(pkg, dict):
                root = "org.openehr." + schema_name.lower()
                name = str(pkg.get("name", ""))
                if name != root and not name.startswith(root + "."):
                    self.warning(path, "class table file names are built from %s.<package>; name the "
                                       "top-level package %s.<package>, or %s with sub-packages"
                                 % (root, root, root))
                elif name == root and pkg.get("classes"):
                    self.warning(path + "/classes", "classes listed directly in %s get table files named "
                                                    "%s.org.<class>.adoc; list them in a sub-package"
                                 % (root, root))
            self.check_package(pkg, key, path, listed, top=True)
        return listed

    def check_package(self, pkg, key, path, listed, top):
        if not isinstance(pkg, dict):
            self.error(path, "a package must be an object")
            return
        self.check_keys(pkg, "package", path)
        name = pkg.get("name")
        if not isinstance(name, str):
            self.error(path, "package has no \"name\"")
        elif name != key:
            self.error(path, "key and \"name\" (%s) differ" % name)
        elif not top and "." in name:
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
        for cls in classes:
            if cls not in self.classes:
                self.error(path + "/classes", "%s is not defined in this schema; bmm-publisher stops "
                                              "with 'Class %s not found in schema'" % (cls, cls))
            elif cls in listed:
                self.warning(path + "/classes", "%s is also listed in %s" % (cls, listed[cls]))
            else:
                listed[cls] = path
        for sub_key, sub in subpackages.items():
            self.check_package(sub, sub_key, path + "/packages/" + sub_key, listed, top=False)

    def check_class(self, cls, path):
        kind = cls.get("_type", "P_BMM_CLASS")
        if kind not in CLASS_TYPES:
            self.error(path, "unknown _type %s, read as a plain class" % kind)
            kind = "P_BMM_CLASS"
        self.check_keys(cls, kind, path)
        self.check_documentation(cls, path, required=True)
        scope = set()
        params = cls.get("generic_parameter_defs")
        if params is not None:
            if not isinstance(params, dict):
                self.error(path + "/generic_parameter_defs", "must be an object keyed by parameter name")
            else:
                for key, param in params.items():
                    p_path = path + "/generic_parameter_defs/" + key
                    if not isinstance(param, dict) or param.get("name") != key:
                        self.error(p_path, "needs a \"name\" equal to its key")
                        continue
                    self.check_keys(param, "generic_parameter", p_path)
                    scope.add(key)
                for key, param in params.items():
                    if isinstance(param, dict) and "conforms_to_type" in param:
                        self.check_type_name(param["conforms_to_type"], path + "/generic_parameter_defs/"
                                             + key + "/conforms_to_type", scope)
        if "is_abstract" in cls and not isinstance(cls["is_abstract"], bool):
            self.error(path + "/is_abstract", "must be true or false")
        ancestors = cls.get("ancestors", [])
        if "ancestor_defs" in cls and not ancestors:
            self.error(path, "bmm-publisher reads only \"ancestors\", so this class has no parent; list the "
                             "root class name there (for an open binding such as A<T>, also redeclare T in "
                             "generic_parameter_defs; state a closed binding in documentation)")
        if not isinstance(ancestors, list) or not all(isinstance(a, str) for a in ancestors):
            self.error(path + "/ancestors", "must be a list of class names")
            ancestors = []
        for i, ancestor in enumerate(ancestors):
            a_path = "%s/ancestors/%d" % (path, i)
            if GENERIC_NAME.search(ancestor):
                self.error(a_path, "ancestors name classes only; for generic inheritance give the "
                                   "root class (%s) and declare the parameters in generic_parameter_defs"
                           % ancestor.split("<")[0].strip())
            else:
                self.check_type_name(ancestor, a_path, set())
        if kind.startswith("P_BMM_ENUMERATION"):
            self.check_enumeration(cls, kind, path)
        for key, constant in self.keyed(cls, "constants", path):
            c_path = path + "/constants/" + key
            self.check_keys(constant, "constant", c_path)
            if not isinstance(constant.get("type"), str):
                self.error(c_path, "a constant needs a \"type\"")
            else:
                self.check_type_name(constant["type"], c_path + "/type", scope)
            self.check_documentation(constant, c_path)
        for key, prop in self.keyed(cls, "properties", path):
            self.check_property(prop, path + "/properties/" + key, scope)
        for key, function in self.keyed(cls, "functions", path):
            self.check_function(function, path + "/functions/" + key, scope)
        self.check_assertions(cls, "invariants", path)

    def check_enumeration(self, cls, kind, path):
        names = cls.get("item_names")
        if not isinstance(names, list) or not names or not all(isinstance(n, str) for n in names):
            self.error(path + "/item_names", "an enumeration needs a non-empty list of item names")
            return
        base = "String" if kind == "P_BMM_ENUMERATION_STRING" else "Integer"
        if base not in (cls.get("ancestors") or []):
            self.warning(path + "/ancestors", "the persistence model requires %s among the ancestors" % base)
        values = cls.get("item_values")
        if values is not None:
            value_type = str if base == "String" else int
            if not isinstance(values, list) or len(values) != len(names):
                self.error(path + "/item_values", "needs one value per item name (%d)" % len(names))
            elif not all(isinstance(v, value_type) and not isinstance(v, bool) for v in values):
                self.error(path + "/item_values", "values must be %ss" % base)
        docs = cls.get("item_documentations")
        if docs is not None and (not isinstance(docs, list) or len(docs) != len(names)):
            self.error(path + "/item_documentations", "needs one text per item name (%d); the "
                                                      "table pairs them by position" % len(names))

    def check_ancestor_cycles(self, d):
        graph = {}
        for section in ("primitive_types", "class_definitions"):
            for cls in (d.get(section) or {}).values():
                if isinstance(cls, dict) and isinstance(cls.get("name"), str):
                    graph[cls["name"]] = [a for a in cls.get("ancestors") or [] if isinstance(a, str)]
        state = {}

        def visit(name, trail):
            state[name] = 1
            for ancestor in graph.get(name, []):
                if state.get(ancestor) == 1:
                    self.error("/class_definitions/" + name, "inheritance cycle: "
                               + " -> ".join(trail + [ancestor]))
                elif ancestor in graph and not state.get(ancestor):
                    visit(ancestor, trail + [ancestor])
            state[name] = 2

        for name in graph:
            if not state.get(name):
                visit(name, [name])

    # --- properties, functions and types -----------------------------------------------------
    def check_property(self, prop, path, scope):
        if not isinstance(prop, dict):
            self.error(path, "a property must be an object")
            return
        kind = prop.get("_type")
        if kind is None:
            if "type_def" in prop:
                self.error(path, "no _type: read as P_BMM_SINGLE_PROPERTY, whose type then defaults "
                                 "to Any; set the property _type")
                return
            self.warning(path, "no _type: read as P_BMM_SINGLE_PROPERTY; published schemas always set it")
            kind = "P_BMM_SINGLE_PROPERTY"
        elif kind in UNSUPPORTED_TYPES:
            self.error(path, "bmm-publisher does not read %s (it becomes a property of type Any); %s"
                       % (kind, UNSUPPORTED_TYPES[kind]))
            return
        elif kind not in PROPERTY_TYPES:
            self.error(path, "unknown _type %s: read as P_BMM_SINGLE_PROPERTY" % kind)
            return
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
            self.check_inline_type(prop, "P_BMM_CONTAINER_TYPE", path, scope)
            if "cardinality" in prop:
                self.check_cardinality(prop["cardinality"], path + "/cardinality")
        else:
            self.check_inline_type(prop, "P_BMM_GENERIC_TYPE", path, scope)

    def check_inline_type(self, owner, kind, path, scope):
        type_def = owner.get("type_def")
        if not isinstance(type_def, dict):
            self.error(path, "needs a \"type_def\" object")
            return
        if type_def.get("_type", kind) != kind:
            self.error(path + "/type_def", "_type %s is ignored here: this type_def is always read as %s"
                       % (type_def["_type"], kind))
        self.check_type_body(type_def, kind, path + "/type_def", scope)

    def check_type(self, t, path, scope):
        """A nested type object (result, generic_parameter_defs entry, element type_def)."""
        if not isinstance(t, dict):
            self.error(path, "a type must be an object")
            return
        kind = t.get("_type")
        if kind is None:
            if "container_type" in t or "root_type" in t:
                self.error(path, "no _type: a nested type is read as P_BMM_SIMPLE_TYPE; set _type")
                return
            self.warning(path, "no _type: read as P_BMM_SIMPLE_TYPE; published schemas always set it")
            kind = "P_BMM_SIMPLE_TYPE"
        elif kind in UNSUPPORTED_TYPES:
            self.error(path, "bmm-publisher does not read %s; %s" % (kind, UNSUPPORTED_TYPES[kind]))
            return
        elif kind == "P_BMM_OPEN_TYPE":
            self.warning(path, "read as P_BMM_SIMPLE_TYPE; published schemas write P_BMM_SIMPLE_TYPE")
            kind = "P_BMM_SIMPLE_TYPE"
        elif kind not in TYPE_TYPES:
            self.error(path, "unknown _type %s: read as P_BMM_SIMPLE_TYPE" % kind)
            return
        self.check_type_body(t, kind, path, scope)

    def check_type_body(self, t, kind, path, scope):
        self.check_keys(t, kind, path)
        if kind == "P_BMM_SIMPLE_TYPE":
            if not isinstance(t.get("type"), str):
                self.error(path, "needs a \"type\"")
            elif GENERIC_NAME.search(t["type"]):
                self.error(path + "/type", "%s is not a class name; use P_BMM_CONTAINER_TYPE or "
                                           "P_BMM_GENERIC_TYPE" % t["type"])
            else:
                self.check_type_name(t["type"], path + "/type", scope)
        elif kind == "P_BMM_CONTAINER_TYPE":
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
            else:
                self.check_type(t["type_def"], path + "/type_def", scope)
        else:
            root = t.get("root_type")
            if not isinstance(root, str):
                self.error(path, "needs a \"root_type\"")
                return
            self.check_type_name(root, path + "/root_type", scope)
            simple = t.get("generic_parameters", [])
            nested = t.get("generic_parameter_defs", {})
            if not isinstance(simple, list) or not isinstance(nested, dict):
                self.error(path, "generic_parameters is a list of names and generic_parameter_defs an "
                                 "object of nested types")
                return
            for i, param in enumerate(simple):
                if isinstance(param, dict):
                    self.check_type(param, "%s/generic_parameters/%d" % (path, i), scope)
                elif not isinstance(param, str) or GENERIC_NAME.search(param):
                    self.error("%s/generic_parameters/%d" % (path, i), "must be a class or parameter "
                                                                       "name; nest other types in "
                                                                       "generic_parameter_defs")
                else:
                    self.check_type_name(param, "%s/generic_parameters/%d" % (path, i), scope)
            for key, param in nested.items():
                self.check_type(param, path + "/generic_parameter_defs/" + key, scope)
            given = len(simple) + len(nested)
            arity = self.arity(root)
            if given == 0:
                self.error(path, "a generic type needs generic_parameters or generic_parameter_defs")
            elif arity is not None and arity != given:
                self.error(path, "%s takes %d generic parameters, %d given" % (root, arity, given))
            elif arity:
                self.check_generic_arguments(root, simple, nested, path, scope)

    def check_generic_arguments(self, root, simple, nested, path, scope):
        """Each argument must conform to the conforms_to_type of the parameter it binds."""
        params = self.lookup(root)["params"]
        bound = []  # (parameter, constraint, argument class name, path)
        if not nested:
            for i, ((param, constraint), arg) in enumerate(zip(params, simple)):
                if isinstance(arg, str):
                    bound.append((param, constraint, arg, "%s/generic_parameters/%d" % (path, i)))
        else:
            constraints = dict(params)
            for key, arg in nested.items():
                if key in constraints and isinstance(arg, dict):
                    name = arg.get("type") or arg.get("root_type")
                    if isinstance(name, str):
                        bound.append((key, constraints[key], name, path + "/generic_parameter_defs/" + key))
        for param, constraint, arg, arg_path in bound:
            if constraint and arg not in scope and self.conforms(arg, constraint) is False:
                self.error(arg_path, "%s does not conform to %s, the constraint on parameter %s of %s "
                                     "(generic_parameters bind in the order %s declares them: %s)"
                           % (arg, constraint, param, root, root, ", ".join(p for p, _ in params)))

    def check_function(self, function, path, scope):
        if not isinstance(function, dict):
            self.error(path, "a function must be an object")
            return
        self.check_name(function, path)
        self.check_keys(function, "function", path)
        self.check_documentation(function, path, required=True)
        for flag in ("is_abstract", "is_nullable"):
            if flag in function and not isinstance(function[flag], bool):
                self.error(path + "/" + flag, "must be true or false")
        aliases = function.get("aliases", [])
        if not isinstance(aliases, list) or not all(isinstance(a, str) for a in aliases):
            self.error(path + "/aliases", "must be a list of strings")
        if "result" in function:
            self.check_type(function["result"], path + "/result", scope)
        else:
            self.warning(path, "no result: the table shows an empty result type")
        for key, param in self.keyed(function, "parameters", path):
            self.check_parameter(param, path + "/parameters/" + key, scope)
        self.check_assertions(function, "pre_conditions", path)
        self.check_assertions(function, "post_conditions", path)

    def check_parameter(self, param, path, scope):
        kind = param.get("_type")
        if kind is None:
            if "type_def" in param:
                self.error(path, "no _type: read as P_BMM_SINGLE_FUNCTION_PARAMETER of type Any")
                return
            kind = "P_BMM_SINGLE_FUNCTION_PARAMETER"
        elif kind not in PARAMETER_TYPES:
            self.error(path, "unknown _type %s: read as P_BMM_SINGLE_FUNCTION_PARAMETER" % kind)
            return
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
            self.check_inline_type(param, "P_BMM_CONTAINER_TYPE", path, scope)
            if "cardinality" not in param:
                self.error(path, "a container parameter needs a \"cardinality\"; bmm-publisher fails "
                                 "without one")
            else:
                self.check_cardinality(param["cardinality"], path + "/cardinality")
        else:
            self.check_inline_type(param, "P_BMM_GENERIC_TYPE", path, scope)

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
        if isinstance(card.get("upper"), int) and isinstance(card.get("lower"), int) and card["upper"] < card["lower"]:
            self.error(path, "upper is below lower")
        if card.get("lower_unbounded"):
            self.warning(path + "/lower_unbounded", "a cardinality has a lower limit (0 or more)")

    # --- shared helpers ------------------------------------------------------------------------
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
            self.error(path, "key and \"name\" (%s) differ; bmm-publisher uses the name" % name)

    def check_keys(self, item, kind, path):
        for key in item:
            if key in READ_KEYS[kind]:
                continue
            near = difflib.get_close_matches(key, sorted(READ_KEYS[kind]), n=1, cutoff=0.8)
            if key in SPEC_ONLY_KEYS.get(kind, ()):
                self.warning("%s/%s" % (path, key), "defined by the persistence model but not read by "
                                                   "bmm-publisher, so it is missing from every output")
            elif near and near[0] not in item:
                self.error("%s/%s" % (path, key), "unknown key, probably a misspelling of %s; bmm-publisher "
                                                 "ignores it, so %s keeps its default" % (near[0], near[0]))
            else:
                self.warning("%s/%s" % (path, key), "unknown key, ignored by bmm-publisher (expected "
                                                   "one of: %s)" % ", ".join(sorted(READ_KEYS[kind])))

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
            else:
                todo.extend(info["ancestors"])
        return None if undecided else False

    def check_type_name(self, name, path, scope):
        if not isinstance(name, str) or not name:
            self.error(path, "must be a non-empty class name")
            return
        if name in scope or name == PROCEDURE_RESULT or self.arity(name) is not None:
            return
        if len(name) == 1:
            self.warning(path, "%s is not a generic parameter of this class; declare it in "
                               "generic_parameter_defs" % name)
        elif self.missing_includes:
            self.unchecked.add(name)
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


def fail(message):
    print("check_bmm: " + message, file=sys.stderr)
    return 2


def schema_id(d):
    return "%s_%s_%s" % (d.get("rm_publisher"), d.get("schema_name"), d.get("rm_release"))


def summarise(cls):
    """What other classes need to know about a class: its generic parameters and its ancestors."""
    params = cls.get("generic_parameter_defs")
    params = params if isinstance(params, dict) else {}
    ancestors = cls.get("ancestors")
    ancestors = ancestors if isinstance(ancestors, list) else []
    return {
        "params": [(key, p.get("conforms_to_type") if isinstance(p, dict) else None) for key, p in params.items()],
        "ancestors": [a for a in ancestors if isinstance(a, str)],
    }


def class_index(d):
    classes = {}
    for section in ("primitive_types", "class_definitions"):
        for cls in (d.get(section) or {}).values():
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
    checker = Checker(args.schema, args.dependency).run()
    for level, path, message in checker.findings:
        print("%-7s %s: %s" % (level, path, message))
    errors, warnings = checker.count("ERROR"), checker.count("WARNING")
    print("check_bmm: %s: %d error(s), %d warning(s)" % (args.schema, errors, warnings))
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
