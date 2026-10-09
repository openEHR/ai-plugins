#!/usr/bin/env python3
"""Tests for the bmm-authoring skill's checker (plugins/openehr-specs/skills/bmm-authoring/scripts/check_bmm.py).

Run from the repo root: python3 -m unittest discover -s scripts -p 'test_*.py'
Standard library only; every test works in a temporary directory.
"""
import copy
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "plugins/openehr-specs/skills/bmm-authoring"
_spec = importlib.util.spec_from_file_location("check_bmm", SKILL / "scripts/check_bmm.py")
check_bmm = importlib.util.module_from_spec(_spec)
sys.modules["check_bmm"] = check_bmm
_spec.loader.exec_module(check_bmm)

EXAMPLE = json.loads((SKILL / "assets/openehr_demo_0.1.0.bmm.json").read_text(encoding="utf-8"))
# The published BASE schema, when a sibling clone exists (it does not in CI).
REAL_BASE = next((p for p in (ROOT.parent / "specifications-BASE", ROOT.parent.parent.parent / "specifications-BASE")
                  if (p / "computable/BMM/openehr_base_1.3.0.bmm.json").is_file()), ROOT) \
    / "computable/BMM/openehr_base_1.3.0.bmm.json"


def base_class(name, ancestors=None, **params):
    cls = {"name": name}
    if ancestors:
        cls["ancestors"] = ancestors
    if params:
        cls["generic_parameter_defs"] = {
            p: dict({"name": p}, **({"conforms_to_type": c} if c else {})) for p, c in params.items()}
    return cls


# A slice of openehr_base_1.3.0.bmm.json: the ancestry and generic constraints the tests rely on,
# copied from the published schema.
_BASE_CLASSES = [
    base_class("Any"), base_class("Ordered", ["Any"]), base_class("Numeric", ["Any"]),
    base_class("Ordered_Numeric", ["Ordered", "Numeric"]), base_class("Integer", ["Ordered_Numeric"]),
    base_class("Real", ["Ordered_Numeric"]), base_class("String", ["Ordered"]),
    base_class("Boolean", ["Any"]), base_class("Temporal", ["Ordered"]), base_class("Time_Definitions"),
    base_class("Iso8601_type", ["Temporal", "Time_Definitions"]),
    base_class("Iso8601_date_time", ["Iso8601_type"]),
    base_class("Container", ["Any"], T="Any"), base_class("List", ["Container"], T="Any"),
    base_class("Set", ["Container"], T="Any"), base_class("Array", ["Container"], T="Any"),
    base_class("Hash", ["Container"], K="Ordered", V=None),
    base_class("Interval", ["Any"], T="Ordered"), base_class("TUPLE"), base_class("TUPLE2", ["TUPLE"], A="Any", B="Any"),
    base_class("ROUTINE", None, ARGS="TUPLE"), base_class("FUNCTION", ["ROUTINE"], ARGS="TUPLE", RESULT="Any"),
    base_class("OBJECT_ID"), base_class("UID_BASED_ID", ["OBJECT_ID"]), base_class("HIER_OBJECT_ID", ["UID_BASED_ID"]),
]
BASE = {
    "bmm_version": "2.4", "rm_publisher": "openehr", "schema_name": "base", "rm_release": "1.3.0",
    "schema_revision": "1.3.0.2", "schema_lifecycle_state": "stable", "schema_description": "stub",
    "schema_author": "test",
    "packages": {"org.openehr.base.foundation_types": {
        "name": "org.openehr.base.foundation_types", "classes": [c["name"] for c in _BASE_CLASSES]}},
    "class_definitions": {c["name"]: c for c in _BASE_CLASSES},
}


class Base(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.base = self.write("openehr_base_1.3.0.bmm.json", BASE)

    def write(self, name, data):
        path = self.root / name
        path.write_text(json.dumps(data, indent=4), encoding="utf-8")
        return path

    def check(self, data, name="openehr_demo_0.1.0.bmm.json", deps=True):
        path = self.write(name, data)
        return check_bmm.Checker(path, [self.base] if deps else []).run()

    def demo(self):
        return copy.deepcopy(EXAMPLE)

    def cls(self, d, name):
        return d["class_definitions"][name]

    def props(self, d, cls="DEMO_GROUP"):
        return d["class_definitions"][cls]["properties"]

    def fn(self, d, cls="DEMO_ITEM", name="is_tagged"):
        return d["class_definitions"][cls]["functions"][name]

    def listing(self, checker):
        return "\n".join("%s %s: %s" % f for f in checker.findings)

    def assertFinding(self, checker, level, path, text):
        hits = [f for f in checker.findings if f[0] == level and f[1] == path and text in f[2]]
        self.assertTrue(hits, "no %s at %s containing %r in:\n%s" % (level, path, text, self.listing(checker)))

    def assertNoFinding(self, checker, level="ERROR"):
        self.assertFalse([f for f in checker.findings if f[0] == level], self.listing(checker))

    def assertOnly(self, checker, level, path, text):
        """Exactly one finding, the expected one: no extra or duplicate reports."""
        self.assertFinding(checker, level, path, text)
        self.assertEqual(len(checker.findings), 1, self.listing(checker))


class ExampleTest(Base):
    def test_example_is_clean_with_its_dependency(self):
        checker = self.check(self.demo())
        self.assertEqual(checker.findings, [])
        self.assertEqual(len(checker.classes), 5)

    def test_without_dependency_base_types_are_listed_as_unchecked(self):
        checker = self.check(self.demo(), deps=False)
        self.assertEqual([lvl for lvl, _, _ in checker.findings], ["INFO"])
        self.assertIn("HIER_OBJECT_ID", checker.findings[0][2])
        self.assertIn("Hash", checker.unchecked)

    @unittest.skipUnless(REAL_BASE.is_file(), "needs a sibling specifications-BASE clone")
    def test_example_is_clean_against_the_published_base(self):
        path = self.write("openehr_demo_0.1.0.bmm.json", self.demo())
        self.assertEqual(check_bmm.Checker(path, [REAL_BASE]).run().findings, [])


class HeaderTest(Base):
    def test_missing_required_field(self):
        for key in check_bmm.HEADER_REQUIRED:
            with self.subTest(key=key):
                d = self.demo()
                del d[key]
                self.assertFinding(self.check(d), "ERROR", "/" + key, "required header field")

    def test_missing_bmm_version_is_assumed(self):
        d = self.demo()
        del d["bmm_version"]
        self.assertOnly(self.check(d), "WARNING", "/bmm_version", "assumes \"2.4\"")

    def test_other_bmm_version(self):
        d = self.demo()
        d["bmm_version"] = "2.3"
        self.assertOnly(self.check(d), "WARNING", "/bmm_version", "use \"2.4\"")

    def test_header_field_must_be_a_string(self):
        d = self.demo()
        d["schema_author"] = ["someone"]
        self.assertFinding(self.check(d), "ERROR", "/schema_author", "must be a string")

    def test_file_name_must_match_schema_id(self):
        self.assertOnly(self.check(self.demo(), name="demo.bmm.json"), "WARNING", "/",
                        "expected openehr_demo_0.1.0.bmm.json")

    def test_revision_follows_release(self):
        d = self.demo()
        d["schema_revision"] = "7"
        self.assertOnly(self.check(d), "WARNING", "/schema_revision", "<rm_release>.<build>")

    def test_release_has_three_parts(self):
        d = self.demo()
        d["rm_release"], d["schema_revision"] = "0.1", "0.1.1"
        self.assertFinding(self.check(d, name="openehr_demo_0.1.bmm.json"), "WARNING", "/rm_release", "3-part")

    def test_spec_only_header_key_is_reported_as_ignored(self):
        d = self.demo()
        d["archetype_parent_class"] = "DEMO_ITEM"
        self.assertOnly(self.check(d), "WARNING", "/archetype_parent_class", "not read by bmm-publisher")

    def test_dependency_not_included(self):
        d = self.demo()
        del d["includes"]
        self.assertOnly(self.check(d), "WARNING", "/includes", "loaded with -d but is not included")

    def test_include_keyed_by_its_id(self):
        d = self.demo()
        d["includes"] = {"1": {"id": "openehr_base_1.3.0"}}
        self.assertOnly(self.check(d), "WARNING", "/includes/1", "key each include by its id")

    def test_include_needs_an_id(self):
        d = self.demo()
        d["includes"]["openehr_base_1.3.0"] = {"id": ["openehr_base_1.3.0"]}
        self.assertFinding(self.check(d), "ERROR", "/includes/openehr_base_1.3.0", "needs an \"id\"")


class PackageTest(Base):
    def packages(self, d):
        return d["packages"]["org.openehr.demo.inventory"]["packages"]

    def test_class_not_in_any_package_gets_no_table(self):
        d = self.demo()
        self.packages(d)["box"]["classes"].remove("DEMO_BOX_REF")
        self.assertOnly(self.check(d), "ERROR", "/class_definitions/DEMO_BOX_REF", "not listed in any package")

    def test_listed_class_must_be_defined(self):
        d = self.demo()
        self.packages(d)["box"]["classes"].append("DEMO_GHOST")
        self.assertOnly(self.check(d), "ERROR", "/packages/org.openehr.demo.inventory/packages/box/classes",
                        "DEMO_GHOST is not defined")

    def test_class_listed_twice(self):
        d = self.demo()
        self.packages(d)["box"]["classes"].append("DEMO_ITEM")
        self.assertOnly(self.check(d), "WARNING", "/packages/org.openehr.demo.inventory/packages/box/classes",
                        "DEMO_ITEM is also listed")

    def test_package_key_and_name(self):
        d = self.demo()
        self.packages(d)["box"]["name"] = "boxes"
        self.assertOnly(self.check(d), "ERROR", "/packages/org.openehr.demo.inventory/packages/box", "differ")

    def test_only_top_level_names_contain_dots(self):
        d = self.demo()
        pkgs = self.packages(d)
        pkgs["a.b"] = dict(pkgs.pop("box"), name="a.b")
        self.assertOnly(self.check(d), "ERROR", "/packages/org.openehr.demo.inventory/packages/a.b", "only top-level")

    def test_top_level_package_name_drives_table_file_names(self):
        d = self.demo()
        d["packages"] = {"demo": dict(d["packages"]["org.openehr.demo.inventory"], name="demo")}
        self.assertOnly(self.check(d), "WARNING", "/packages/demo", "org.openehr.demo.<package>")

    def test_package_holding_only_sub_packages_is_accepted(self):
        d = self.demo()
        d["packages"] = {"org.openehr.demo": dict(d["packages"]["org.openehr.demo.inventory"], name="org.openehr.demo")}
        self.assertEqual(self.check(d).findings, [])

    def test_classes_directly_in_the_component_root_package(self):
        d = self.demo()
        classes = [c for p in self.packages(d).values() for c in p["classes"]]
        d["packages"] = {"org.openehr.demo": {"name": "org.openehr.demo", "classes": classes}}
        self.assertOnly(self.check(d), "WARNING", "/packages/org.openehr.demo/classes", "org.openehr.demo.org.<class>.adoc")

    def nest(self, d, depth):
        """Move the box classes into a chain of sub-packages, so that they sit at the given depth."""
        box = self.packages(d).pop("box")
        parent, path = self.packages(d), "/packages/org.openehr.demo.inventory/packages"
        for level in range(2, depth):
            name = "p%d" % level
            parent[name] = {"name": name, "packages": {}}
            parent, path = parent[name]["packages"], "%s/%s/packages" % (path, name)
        parent["box"] = box
        return path + "/box"

    def test_packages_deeper_than_four_levels_get_no_table(self):
        d = self.demo()
        path = self.nest(d, 5)
        self.assertOnly(self.check(d), "ERROR", path, "only 4 levels deep")

    def test_four_levels_are_visited(self):
        d = self.demo()
        self.nest(d, 4)
        self.assertEqual(self.check(d).findings, [])

    def test_empty_package(self):
        d = self.demo()
        self.packages(d)["spare"] = {"name": "spare", "classes": []}
        self.assertOnly(self.check(d), "WARNING", "/packages/org.openehr.demo.inventory/packages/spare", "empty package")

    def test_packages_must_be_an_object(self):
        d = self.demo()
        d["packages"] = [d["packages"]]
        self.assertFinding(self.check(d), "ERROR", "/packages", "must be an object keyed by package name")


class ClassTest(Base):
    def packages_add(self, d, name):
        d["packages"]["org.openehr.demo.inventory"]["packages"]["item"]["classes"].append(name)

    def test_key_and_name_differ(self):
        d = self.demo()
        self.cls(d, "DEMO_ITEM")["name"] = "DEMO_THING"
        self.assertFinding(self.check(d), "ERROR", "/class_definitions/DEMO_ITEM", "key and \"name\"")

    def test_class_defined_twice(self):
        d = self.demo()
        d["primitive_types"] = {"DEMO_ITEM": copy.deepcopy(self.cls(d, "DEMO_ITEM"))}
        self.assertFinding(self.check(d), "ERROR", "/class_definitions/DEMO_ITEM", "also defined at /primitive_types/DEMO_ITEM")

    def test_class_redefines_a_dependency_class(self):
        d = self.demo()
        d["class_definitions"]["Boolean"] = {"name": "Boolean", "documentation": "x"}
        self.packages_add(d, "Boolean")
        self.assertOnly(self.check(d), "WARNING", "/class_definitions/Boolean", "also defined in openehr_base_1.3.0")

    def test_unknown_class_type_is_reported_and_its_content_still_checked(self):
        d = self.demo()
        status = self.cls(d, "DEMO_STATUS")
        status["_type"] = "P_BMM_ENUMERATON_STRING"
        status["item_documentations"].pop()
        checker = self.check(d)
        self.assertFinding(checker, "ERROR", "/class_definitions/DEMO_STATUS", "unknown _type P_BMM_ENUMERATON_STRING")
        self.assertFinding(checker, "ERROR", "/class_definitions/DEMO_STATUS/item_documentations", "one text per item")

    def test_class_type_must_be_a_string(self):
        d = self.demo()
        self.cls(d, "DEMO_ITEM")["_type"] = ["P_BMM_CLASS"]
        self.assertOnly(self.check(d), "ERROR", "/class_definitions/DEMO_ITEM/_type", "must be a string")

    def test_ancestor_defs_alone_loses_the_parent(self):
        d = self.demo()
        group = self.cls(d, "DEMO_GROUP")
        del group["ancestors"]
        group["ancestor_defs"] = {"DEMO_ITEM": {"_type": "P_BMM_SIMPLE_TYPE", "type": "DEMO_ITEM"}}
        checker = self.check(d)
        self.assertFinding(checker, "ERROR", "/class_definitions/DEMO_GROUP/ancestor_defs", "the parent DEMO_ITEM is lost")
        self.assertFinding(checker, "WARNING", "/class_definitions/DEMO_GROUP/ancestor_defs", "not read by bmm-publisher")

    def test_ancestor_defs_naming_another_parent_loses_it(self):
        d = self.demo()
        self.cls(d, "DEMO_BOX_REF")["ancestor_defs"] = {
            "DEMO_BOX<DEMO_GROUP>": {"_type": "P_BMM_GENERIC_TYPE", "root_type": "DEMO_BOX", "generic_parameters": ["DEMO_GROUP"]}}
        self.assertFinding(self.check(d), "ERROR", "/class_definitions/DEMO_BOX_REF/ancestor_defs",
                           "the parent DEMO_BOX is lost")

    def test_ancestor_defs_repeating_the_ancestors_only_warns(self):
        d = self.demo()
        self.cls(d, "DEMO_GROUP")["ancestor_defs"] = {"DEMO_ITEM": {"_type": "P_BMM_SIMPLE_TYPE", "type": "DEMO_ITEM"}}
        self.assertOnly(self.check(d), "WARNING", "/class_definitions/DEMO_GROUP/ancestor_defs", "not read")

    def test_generic_name_in_ancestors(self):
        d = self.demo()
        self.cls(d, "DEMO_GROUP")["ancestors"] = ["DEMO_BOX<DEMO_ITEM>"]
        self.assertFinding(self.check(d), "ERROR", "/class_definitions/DEMO_GROUP/ancestors/0", "root class (DEMO_BOX)")

    def test_unresolved_ancestor(self):
        d = self.demo()
        self.cls(d, "DEMO_BOX")["ancestors"] = ["NOWHERE"]
        self.assertOnly(self.check(d), "WARNING", "/class_definitions/DEMO_BOX/ancestors/0", "NOWHERE is not defined")

    def test_inheritance_cycle(self):
        d = self.demo()
        self.cls(d, "DEMO_ITEM")["ancestors"] = ["DEMO_GROUP"]
        cycles = [f for f in self.check(d).findings if "inheritance cycle" in f[2]]
        self.assertEqual(len(cycles), 1)
        self.assertIn("DEMO_ITEM", cycles[0][2])
        self.assertIn("DEMO_GROUP", cycles[0][2])

    def test_cycle_is_reported_where_the_class_is_defined(self):
        d = self.demo()
        d["primitive_types"] = {"P1": {"name": "P1", "documentation": "x", "ancestors": ["P2"]},
                                "P2": {"name": "P2", "documentation": "x", "ancestors": ["P1"]}}
        self.packages_add(d, "P1")
        self.packages_add(d, "P2")
        cycles = [f for f in self.check(d).findings if "inheritance cycle" in f[2]]
        self.assertEqual(len(cycles), 1)
        self.assertTrue(cycles[0][1].startswith("/primitive_types/"), cycles)

    def test_enumeration_checks(self):
        cases = [
            ("item_documentations", lambda s: s["item_documentations"].pop(), "one text per item name (3)"),
            ("item_values", lambda s: s.update(item_values=["a", "b"]), "one value per item name (3)"),
            ("item_values", lambda s: s.update(item_values=[1, 2, 3]), "must be strings"),
            ("item_names", lambda s: s.update(item_names=[]), "non-empty list"),
        ]
        for key, change, text in cases:
            with self.subTest(change=text):
                d = self.demo()
                change(self.cls(d, "DEMO_STATUS"))
                self.assertFinding(self.check(d), "ERROR", "/class_definitions/DEMO_STATUS/" + key, text)

    def integer_enumeration(self, d, **extra):
        status = self.cls(d, "DEMO_STATUS")
        status.update(_type="P_BMM_ENUMERATION_INTEGER", ancestors=["Integer"], item_values=[0, 1, 2])
        status.update(extra)
        return status

    def test_integer_enumeration_is_clean(self):
        d = self.demo()
        self.integer_enumeration(d)
        self.assertEqual(self.check(d).findings, [])

    def test_integer_values_print_only_with_integer_ancestor(self):
        d = self.demo()
        self.integer_enumeration(d, ancestors=["Any"])
        self.assertOnly(self.check(d), "WARNING", "/class_definitions/DEMO_STATUS/ancestors", "only when Integer")

    def test_class_keys_are_lost_on_enumerations_and_interfaces(self):
        cases = [("P_BMM_ENUMERATION_STRING", "invariants", {"Inv": "True"}),
                 ("P_BMM_ENUMERATION_STRING", "properties", {}),
                 ("P_BMM_INTERFACE", "ancestors", ["Any"])]
        for kind, key, value in cases:
            with self.subTest(kind=kind, key=key):
                d = self.demo()
                status = self.cls(d, "DEMO_STATUS")
                if kind == "P_BMM_INTERFACE":
                    status.clear()
                    status.update(_type=kind, name="DEMO_STATUS", documentation="x")
                status[key] = value
                self.assertFinding(self.check(d), "ERROR", "/class_definitions/DEMO_STATUS/" + key, "so it is lost")

    def test_constant_checks(self):
        cases = [(lambda c: c.pop("type"), "ERROR", "", "needs a \"type\""),
                 (lambda c: c.update(name="Max"), "ERROR", "", "key and \"name\""),
                 (lambda c: c.update(type="Integr"), "WARNING", "/type", "did you mean Integer")]
        for change, level, suffix, text in cases:
            with self.subTest(text=text):
                d = self.demo()
                change(self.cls(d, "DEMO_ITEM")["constants"]["Max_tags"])
                self.assertFinding(self.check(d), level, "/class_definitions/DEMO_ITEM/constants/Max_tags" + suffix, text)

    def test_invariants_map_tags_to_strings(self):
        d = self.demo()
        self.cls(d, "DEMO_ITEM")["invariants"] = ["not name.is_empty()"]
        self.assertOnly(self.check(d), "ERROR", "/class_definitions/DEMO_ITEM/invariants", "tag to an expression")

    def test_flags_must_be_booleans(self):
        cases = [("/class_definitions/DEMO_ITEM/is_abstract", lambda d: self.cls(d, "DEMO_ITEM").update(is_abstract="true")),
                 ("/class_definitions/DEMO_ITEM/properties/uid/is_mandatory",
                  lambda d: self.props(d, "DEMO_ITEM")["uid"].update(is_mandatory="true")),
                 ("/class_definitions/DEMO_GROUP/functions/first_tagged/is_nullable",
                  lambda d: self.fn(d, "DEMO_GROUP", "first_tagged").update(is_nullable=1)),
                 ("/class_definitions/DEMO_ITEM/functions/is_tagged/parameters/a_tag/is_nullable",
                  lambda d: self.fn(d)["parameters"]["a_tag"].update(is_nullable="no"))]
        for path, change in cases:
            with self.subTest(path=path):
                d = self.demo()
                change(d)
                self.assertOnly(self.check(d), "ERROR", path, "must be true or false")

    def test_generic_parameter_needs_its_name(self):
        d = self.demo()
        self.cls(d, "DEMO_BOX")["generic_parameter_defs"]["T"]["name"] = "U"
        self.assertFinding(self.check(d), "ERROR", "/class_definitions/DEMO_BOX/generic_parameter_defs/T", "equal to its key")


class PropertyTest(Base):
    P = "/class_definitions/DEMO_GROUP/properties/"

    def test_wrong_type_markers(self):
        cases = [
            ("items", lambda p: p.update(_type="P_BMM_CONTAINER_PROPRETY"), "items", "unknown _type P_BMM_CONTAINER_PROPRETY"),
            ("items", lambda p: p.pop("_type"), "items", "defaults to Any"),
            ("items", lambda p: p.update(_type=7), "items/_type", "must be a string"),
            ("items", lambda p: p["type_def"].update(_type="P_BMM_GENERIC_TYPE"), "items/type_def", "is ignored here"),
            ("index", lambda p: p.update(_type="P_BMM_INDEXED_CONTAINER_PROPERTY"), "index", "root_type Hash"),
        ]
        for prop, change, path, text in cases:
            with self.subTest(text=text):
                d = self.demo()
                change(self.props(d)[prop])
                self.assertFinding(self.check(d), "ERROR", self.P + path, text)

    def test_unknown_property_type_still_checks_its_content(self):
        d = self.demo()
        items = self.props(d)["items"]
        items["_type"] = "P_BMM_CONTAINER_PROPRETY"
        items["is_mandantory"] = items.pop("is_mandatory")
        checker = self.check(d)
        self.assertFinding(checker, "ERROR", self.P + "items", "checked below as P_BMM_CONTAINER_PROPERTY")
        self.assertFinding(checker, "ERROR", self.P + "items/is_mandantory", "misspelling of is_mandatory")

    def test_property_key_and_name_differ(self):
        d = self.demo()
        self.props(d)["items"]["name"] = "item"
        self.assertOnly(self.check(d), "ERROR", self.P + "items", "key and \"name\" (item) differ")

    def test_value_set_constraint_loses_the_type(self):
        d = self.demo()
        self.props(d, "DEMO_ITEM")["name"] = {"_type": "P_BMM_SINGLE_PROPERTY", "name": "name", "documentation": "x",
                                              "type_ref": {"type": "String", "value_constraint": "openEHR::languages"}}
        self.assertFinding(self.check(d), "ERROR", "/class_definitions/DEMO_ITEM/properties/name", "read as type Any")

    def test_cardinality_checks(self):
        cases = [(lambda c: c.pop("upper_unbounded"), "", "\"upper_unbounded\": false"),
                 (lambda c: c.update(upper=1), "", "upper is below lower"),
                 (lambda c: c.pop("upper"), "", "needs an \"upper\" limit"),
                 (lambda c: c.update(lower=-1), "/lower", "non-negative integer"),
                 (lambda c: c.update(upper_unbounded="no"), "/upper_unbounded", "must be true or false")]
        for change, suffix, text in cases:
            with self.subTest(text=text):
                d = self.demo()
                change(self.props(d)["ranks"]["cardinality"])
                self.assertFinding(self.check(d), "ERROR", self.P + "ranks/cardinality" + suffix, text)

    def test_hash_is_not_a_container_type(self):
        d = self.demo()
        self.props(d)["items"]["type_def"]["container_type"] = "Hash"
        self.assertOnly(self.check(d), "ERROR", self.P + "items/type_def/container_type", "Hash takes 2")

    def test_container_needs_an_element_type(self):
        d = self.demo()
        del self.props(d)["items"]["type_def"]["type"]
        self.assertOnly(self.check(d), "ERROR", self.P + "items/type_def", "read as Any")

    def test_simple_element_type_in_type_def_renders_any(self):
        d = self.demo()
        td = self.props(d)["items"]["type_def"]
        td["type_def"] = {"_type": "P_BMM_SIMPLE_TYPE", "type": td.pop("type")}
        self.assertOnly(self.check(d), "ERROR", self.P + "items/type_def/type_def", "goes in \"type\"")

    def test_generic_parameter_count(self):
        d = self.demo()
        self.props(d)["index"]["type_def"]["generic_parameters"] = ["String"]
        self.assertOnly(self.check(d), "ERROR", self.P + "index/type_def", "Hash takes 2 generic parameters, 1 given")

    def test_generic_type_needs_parameters(self):
        d = self.demo()
        del self.props(d)["index"]["type_def"]["generic_parameters"]
        self.assertOnly(self.check(d), "ERROR", self.P + "index/type_def", "needs generic_parameters or generic_parameter_defs")

    def test_mixed_generic_parameter_forms(self):
        d = self.demo()
        self.props(d)["index"]["type_def"]["generic_parameter_defs"] = {"V": {"_type": "P_BMM_SIMPLE_TYPE", "type": "DEMO_GROUP"}}
        self.assertOnly(self.check(d), "ERROR", self.P + "index/type_def", "ignores generic_parameter_defs")

    def test_type_object_in_generic_parameters(self):
        d = self.demo()
        self.props(d)["index"]["type_def"]["generic_parameters"][1] = {"_type": "P_BMM_SIMPLE_TYPE", "type": "DEMO_ITEM"}
        self.assertOnly(self.check(d), "ERROR", self.P + "index/type_def/generic_parameters/1", "stops with a type error")

    def test_generic_type_object_in_generic_parameters(self):
        d = self.demo()
        self.props(d, "DEMO_BOX_REF")["target"]["type_def"]["generic_parameters"] = [
            {"_type": "P_BMM_GENERIC_TYPE", "root_type": "DEMO_BOX", "generic_parameters": ["DEMO_GROUP"]}]
        path = "/class_definitions/DEMO_BOX_REF/properties/target/type_def/generic_parameters/0"
        self.assertOnly(self.check(d), "ERROR", path, "DEMO_BOX does not conform to DEMO_ITEM")

    def test_container_type_in_generic_parameter_defs_prints_nothing(self):
        d = self.demo()
        td = self.props(d)["index"]["type_def"]
        del td["generic_parameters"]
        td["generic_parameter_defs"] = {"K": {"_type": "P_BMM_SIMPLE_TYPE", "type": "String"},
                                        "V": {"_type": "P_BMM_CONTAINER_TYPE", "container_type": "List", "type": "DEMO_ITEM"}}
        self.assertOnly(self.check(d), "ERROR", self.P + "index/type_def/generic_parameter_defs/V", "prints nothing")

    def test_nested_type_needs_its_type_marker(self):
        d = self.demo()
        del self.props(d, "DEMO_BOX_REF")["replaced"]["type_def"]["type_def"]["_type"]
        self.assertFinding(self.check(d), "ERROR", "/class_definitions/DEMO_BOX_REF/properties/replaced/type_def/type_def",
                           "no _type")

    def test_single_property_without_type_marker(self):
        d = self.demo()
        del self.props(d, "DEMO_ITEM")["uid"]["_type"]
        self.assertOnly(self.check(d), "WARNING", "/class_definitions/DEMO_ITEM/properties/uid", "published schemas always set it")

    def test_undeclared_single_letter_type(self):
        d = self.demo()
        self.props(d, "DEMO_ITEM")["uid"]["type"] = "T"
        self.assertOnly(self.check(d), "WARNING", "/class_definitions/DEMO_ITEM/properties/uid/type", "T is not a generic parameter")

    def test_lower_unbounded_cardinality(self):
        d = self.demo()
        self.props(d)["items"]["cardinality"]["lower_unbounded"] = True
        self.assertOnly(self.check(d), "WARNING", self.P + "items/cardinality/lower_unbounded", "lower limit")

    def test_open_property_needs_a_declared_parameter(self):
        d = self.demo()
        self.props(d, "DEMO_BOX")["content"]["type"] = "U"
        self.assertOnly(self.check(d), "ERROR", "/class_definitions/DEMO_BOX/properties/content/type", "U is not a generic parameter")

    def test_generic_parameter_as_single_property_type(self):
        d = self.demo()
        self.props(d, "DEMO_BOX")["content"]["_type"] = "P_BMM_SINGLE_PROPERTY"
        self.assertOnly(self.check(d), "WARNING", "/class_definitions/DEMO_BOX/properties/content", "use P_BMM_SINGLE_PROPERTY_OPEN")

    def test_generic_names_where_class_names_belong(self):
        cases = [("DEMO_ITEM", "uid", lambda p: p.update(type="List<String>"), "uid/type"),
                 ("DEMO_ITEM", "tags", lambda p: p["type_def"].update(type="List<String>"), "tags/type_def/type"),
                 ("DEMO_GROUP", "index", lambda p: p["type_def"]["generic_parameters"].__setitem__(1, "List<X>"),
                  "index/type_def/generic_parameters/1")]
        for cls, prop, change, path in cases:
            with self.subTest(path=path):
                d = self.demo()
                change(self.props(d, cls)[prop])
                self.assertFinding(self.check(d), "ERROR", "/class_definitions/%s/properties/%s" % (cls, path), "name")

    def test_misspelt_key_is_an_error(self):
        d = self.demo()
        uid = self.props(d, "DEMO_ITEM")["uid"]
        uid["is_mandantory"] = uid.pop("is_mandatory")
        self.assertOnly(self.check(d), "ERROR", "/class_definitions/DEMO_ITEM/properties/uid/is_mandantory",
                        "misspelling of is_mandatory")

    def test_unknown_key_that_resembles_nothing_is_a_warning(self):
        d = self.demo()
        self.props(d, "DEMO_ITEM")["uid"]["colour"] = "blue"
        self.assertOnly(self.check(d), "WARNING", "/class_definitions/DEMO_ITEM/properties/uid/colour", "unknown key")

    def test_unresolved_type_name(self):
        d = self.demo()
        self.props(d, "DEMO_ITEM")["uid"]["type"] = "NO_SUCH_CLASS"
        self.assertOnly(self.check(d), "WARNING", "/class_definitions/DEMO_ITEM/properties/uid/type", "NO_SUCH_CLASS is not defined")

    def test_misspelt_class_name_is_caught_even_without_dependencies(self):
        d = self.demo()
        self.props(d, "DEMO_ITEM")["status"]["type"] = "DEMO_STATS"
        checker = self.check(d, deps=False)
        self.assertFinding(checker, "WARNING", "/class_definitions/DEMO_ITEM/properties/status/type", "did you mean DEMO_STATUS")
        self.assertNotIn("DEMO_STATS", checker.unchecked)

    def test_attribute_reference_in_documentation(self):
        d = self.demo()
        self.props(d, "DEMO_ITEM")["uid"]["documentation"] = "See {base_release} for details."
        self.assertOnly(self.check(d), "WARNING", "/class_definitions/DEMO_ITEM/properties/uid/documentation", "{base_release}")

    def test_braces_that_are_not_attribute_references(self):
        for text in ("Cardinality {1..1}.", "A {TypeName} placeholder.", "Range {x-y}."):
            with self.subTest(text=text):
                d = self.demo()
                self.props(d, "DEMO_ITEM")["uid"]["documentation"] = text
                self.assertEqual(self.check(d).findings, [])

    def test_missing_documentation(self):
        d = self.demo()
        del self.props(d, "DEMO_ITEM")["uid"]["documentation"]
        self.assertOnly(self.check(d), "WARNING", "/class_definitions/DEMO_ITEM/properties/uid", "no documentation")


class ConformanceTest(Base):
    def generic(self, d, cls, prop):
        return self.props(d, cls)[prop]["type_def"]

    def test_argument_must_conform(self):
        d = self.demo()
        self.generic(d, "DEMO_BOX_REF", "target")["generic_parameters"] = ["String"]
        self.assertOnly(self.check(d), "ERROR", "/class_definitions/DEMO_BOX_REF/properties/target/type_def/generic_parameters/0",
                        "String does not conform to DEMO_ITEM, the constraint on parameter T of DEMO_BOX")

    def test_descendant_conforms(self):
        d = self.demo()
        self.generic(d, "DEMO_BOX_REF", "target")["generic_parameters"] = ["DEMO_GROUP"]
        self.assertEqual(self.check(d).findings, [])

    def test_conformance_through_several_levels_of_base(self):
        d = self.demo()
        self.props(d, "DEMO_ITEM")["window"] = {"_type": "P_BMM_GENERIC_PROPERTY", "name": "window", "documentation": "x",
                                                "type_def": {"root_type": "Interval", "generic_parameters": ["Integer"]}}
        self.assertEqual(self.check(d).findings, [])

    def test_hash_key_must_be_ordered(self):
        d = self.demo()
        self.generic(d, "DEMO_GROUP", "index")["generic_parameters"] = ["DEMO_ITEM", "String"]
        self.assertOnly(self.check(d), "ERROR", "/class_definitions/DEMO_GROUP/properties/index/type_def/generic_parameters/0",
                        "DEMO_ITEM does not conform to Ordered")

    def test_nested_argument_must_conform(self):
        d = self.demo()
        self.generic(d, "DEMO_BOX_REF", "replaced")["type_def"]["generic_parameters"] = ["Integer"]
        self.assertOnly(self.check(d), "ERROR",
                        "/class_definitions/DEMO_BOX_REF/properties/replaced/type_def/type_def/generic_parameters/0",
                        "Integer does not conform to DEMO_ITEM")

    def test_generic_parameter_defs_bind_by_position(self):
        d = self.demo()
        td = self.generic(d, "DEMO_GROUP", "index")
        del td["generic_parameters"]
        td["generic_parameter_defs"] = {"V": {"_type": "P_BMM_SIMPLE_TYPE", "type": "DEMO_ITEM"},
                                        "K": {"_type": "P_BMM_SIMPLE_TYPE", "type": "String"}}
        checker = self.check(d)
        path = "/class_definitions/DEMO_GROUP/properties/index/type_def/generic_parameter_defs/"
        self.assertFinding(checker, "WARNING", path + "V", "entry 1 is parameter K of Hash")
        self.assertFinding(checker, "ERROR", path + "V", "DEMO_ITEM does not conform to Ordered")

    def test_enclosing_parameter_conforms_through_its_constraint(self):
        d = self.demo()
        wrap = {"name": "DEMO_WRAP", "documentation": "x", "generic_parameter_defs": {"U": {"name": "U"}},
                "properties": {"box": {"_type": "P_BMM_GENERIC_PROPERTY", "name": "box", "documentation": "x",
                                       "type_def": {"root_type": "DEMO_BOX", "generic_parameters": ["U"]}}}}
        d["class_definitions"]["DEMO_WRAP"] = wrap
        d["packages"]["org.openehr.demo.inventory"]["packages"]["box"]["classes"].append("DEMO_WRAP")
        path = "/class_definitions/DEMO_WRAP/properties/box/type_def/generic_parameters/0"
        self.assertOnly(self.check(d), "ERROR", path, "U (constrained to Any) does not conform to DEMO_ITEM")
        wrap["generic_parameter_defs"]["U"]["conforms_to_type"] = "DEMO_GROUP"
        self.assertEqual(self.check(d).findings, [])

    def test_undecidable_conformance_is_not_an_error(self):
        d = self.demo()
        self.generic(d, "DEMO_BOX_REF", "target")["generic_parameters"] = ["HIER_OBJECT_ID"]
        checker = self.check(d, deps=False)
        self.assertNoFinding(checker)
        self.assertIn("HIER_OBJECT_ID", checker.unchecked)


class FunctionTest(Base):
    F = "/class_definitions/DEMO_ITEM/functions/is_tagged"

    def param(self, d):
        return self.fn(d)["parameters"]["a_tag"]

    def test_container_parameter_cardinality_is_optional(self):
        d = self.demo()
        self.fn(d)["parameters"]["a_tag"] = {"_type": "P_BMM_CONTAINER_FUNCTION_PARAMETER", "name": "a_tag",
                                             "type_def": {"container_type": "List", "type": "String"}}
        self.assertEqual(self.check(d).findings, [])

    def test_container_parameter_cardinality_is_checked(self):
        d = self.demo()
        self.fn(d)["parameters"]["a_tag"] = {"_type": "P_BMM_CONTAINER_FUNCTION_PARAMETER", "name": "a_tag",
                                             "type_def": {"container_type": "List", "type": "String"},
                                             "cardinality": {"lower": 0, "upper": 3}}
        self.assertOnly(self.check(d), "ERROR", self.F + "/parameters/a_tag/cardinality", "\"upper_unbounded\": false")

    def test_wrong_parameter_markers(self):
        cases = [(lambda p: p.update(_type="P_BMM_SINGLE_FUNCTION_PARAMETR"), "", "unknown _type"),
                 (lambda p: p.update(_type="P_BMM_CONTAINER_FUNCTION_PARAMETER"), "", "needs a \"type_def\""),
                 (lambda p: (p.pop("type"), p.pop("_type"), p.update(type_def={"container_type": "List", "type": "String"})),
                  "", "no _type"),
                 (lambda p: p.update(_type="P_BMM_SINGLE_FUNCTION_PARAMETER_OPEN"), "/type", "not a generic parameter"),
                 (lambda p: p.update(name="tag"), "", "key and \"name\"")]
        for change, suffix, text in cases:
            with self.subTest(text=text):
                d = self.demo()
                change(self.param(d))
                self.assertFinding(self.check(d), "ERROR", self.F + "/parameters/a_tag" + suffix, text)

    def test_result_markers(self):
        cases = [({"type": "Boolean"}, "WARNING", "published schemas always set it"),
                 ({"container_type": "List", "type": "String"}, "ERROR", "no _type"),
                 ({"_type": "P_BMM_CONTAINER_TYP", "container_type": "List", "type": "String"}, "ERROR", "unknown _type"),
                 ({"_type": "P_BMM_INDEXED_CONTAINER_TYPE", "container_type": "Hash"}, "ERROR", "does not read"),
                 ({"_type": "P_BMM_OPEN_TYPE", "type": "Boolean"}, "WARNING", "read as P_BMM_SIMPLE_TYPE")]
        for result, level, text in cases:
            with self.subTest(text=text):
                d = self.demo()
                self.fn(d)["result"] = result
                self.assertFinding(self.check(d), level, self.F + "/result", text)

    def test_void_is_a_procedure_result_only(self):
        d = self.demo()
        self.fn(d)["result"] = {"_type": "P_BMM_SIMPLE_TYPE", "type": "void"}
        self.assertEqual(self.check(d).findings, [])
        self.props(d, "DEMO_ITEM")["uid"]["type"] = "void"
        self.assertOnly(self.check(d), "WARNING", "/class_definitions/DEMO_ITEM/properties/uid/type", "only the result type")

    def test_function_without_result(self):
        d = self.demo()
        del self.fn(d)["result"]
        self.assertOnly(self.check(d), "WARNING", self.F, "empty result type")

    def test_conditions_and_aliases(self):
        cases = [(lambda f: f.update(pre_conditions={"Pre_tag_valid": True}), "/pre_conditions", "tag to an expression"),
                 (lambda f: f.update(post_conditions=["Result"]), "/post_conditions", "tag to an expression"),
                 (lambda f: f.update(aliases="has_tag"), "/aliases", "list of names")]
        for change, suffix, text in cases:
            with self.subTest(text=text):
                d = self.demo()
                change(self.fn(d))
                self.assertOnly(self.check(d), "ERROR", self.F + suffix, text)


class DependencyTest(Base):
    def test_schema_passed_as_its_own_dependency_is_ignored(self):
        path = self.write("openehr_demo_0.1.0.bmm.json", self.demo())
        checker = check_bmm.Checker(path, [self.base, path]).run()
        self.assertEqual([m for _, _, m in checker.findings], ["-d %s is the schema being checked; it is ignored" % path])

    def test_dependencies_with_the_same_id_are_merged(self):
        half = copy.deepcopy(BASE)
        half["class_definitions"] = {k: v for k, v in BASE["class_definitions"].items() if k != "HIER_OBJECT_ID"}
        rest = copy.deepcopy(BASE)
        rest["class_definitions"] = {"HIER_OBJECT_ID": BASE["class_definitions"]["HIER_OBJECT_ID"]}
        a, b = self.write("half.bmm.json", half), self.write("rest.bmm.json", rest)
        path = self.write("openehr_demo_0.1.0.bmm.json", self.demo())
        checker = check_bmm.Checker(path, [a, b]).run()
        self.assertEqual([lvl for lvl, _, _ in checker.findings], ["WARNING"], self.listing(checker))
        self.assertIn("same schema id", checker.findings[0][2])

    def test_dependency_that_is_not_a_schema(self):
        for content in ("[]", "{\"name\": \"x\"}"):
            with self.subTest(content=content):
                dep = self.root / "dep.json"
                dep.write_text(content, encoding="utf-8")
                path = self.write("openehr_demo_0.1.0.bmm.json", self.demo())
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                    check_bmm.Checker(path, [dep])
                self.assertEqual(raised.exception.code, 2)


def nodes(value, path=()):
    """Every (path, value) in a JSON document, the root included."""
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from nodes(child, path + (key,))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from nodes(child, path + (i,))


class RobustnessTest(Base):
    """A checker mostly sees broken files: no input may end in a traceback."""

    REPLACEMENTS = [[], 7, {}, "x", None, True, [{}], {"x": []}]

    def test_no_traceback_for_any_wrongly_typed_value(self):
        for path, _ in nodes(EXAMPLE):
            if not path:
                continue
            for replacement in self.REPLACEMENTS:
                d = self.demo()
                target = d
                for step in path[:-1]:
                    target = target[step]
                target[path[-1]] = replacement
                with self.subTest(path="/".join(map(str, path)), value=replacement):
                    try:
                        self.check(d)
                    except Exception as exc:  # name the input that broke it, not just the traceback
                        self.fail("%s: %s" % (type(exc).__name__, exc))

    def test_every_wrongly_typed_value_is_reported(self):
        # JSON null reads as an absent key, and a constant's value may be a string or a number.
        free = {("class_definitions", "DEMO_ITEM", "constants", "Max_tags", "value")}
        for path, original in nodes(EXAMPLE):
            if not path or path in free:
                continue
            for replacement in self.REPLACEMENTS:
                if replacement is None or type(replacement) is type(original):
                    continue
                d = self.demo()
                target = d
                for step in path[:-1]:
                    target = target[step]
                target[path[-1]] = replacement
                with self.subTest(path="/".join(map(str, path)), value=replacement):
                    checker = self.check(d)
                    self.assertTrue([f for f in checker.findings if f[0] in ("ERROR", "WARNING")], "nothing reported")

    def test_shape_errors_are_reported_where_they_occur(self):
        P = "/packages/org.openehr.demo.inventory/packages/box"
        G = "/class_definitions/DEMO_GROUP/properties/"
        cases = [
            (lambda d: d.update(includes=[]), "/includes", "keyed by schema id"),
            (lambda d: d.update(class_definitions=[]), "/class_definitions", "keyed by class name"),
            (lambda d: d["class_definitions"].update(DEMO_ITEM=[]), "/class_definitions/DEMO_ITEM", "must be an object"),
            (lambda d: d["class_definitions"]["DEMO_ITEM"].pop("name"), "/class_definitions/DEMO_ITEM", "has no \"name\""),
            (lambda d: d["packages"]["org.openehr.demo.inventory"]["packages"].update(box=[]), P, "a package must be an object"),
            (lambda d: d["packages"]["org.openehr.demo.inventory"]["packages"]["box"].update(classes="x"), P + "/classes",
             "list of class names"),
            (lambda d: d["packages"]["org.openehr.demo.inventory"]["packages"]["box"].update(packages=[]), P + "/packages",
             "keyed by package name"),
            (lambda d: d["class_definitions"]["DEMO_BOX"].update(generic_parameter_defs=[]),
             "/class_definitions/DEMO_BOX/generic_parameter_defs", "keyed by parameter name"),
            (lambda d: d["class_definitions"]["DEMO_GROUP"]["properties"]["index"]["type_def"].update(generic_parameters="x"),
             G + "index/type_def/generic_parameters", "list of class or parameter names"),
            (lambda d: d["class_definitions"]["DEMO_GROUP"]["properties"]["index"]["type_def"].update(generic_parameter_defs=[]),
             G + "index/type_def/generic_parameter_defs", "object of nested types"),
            (lambda d: d["class_definitions"]["DEMO_GROUP"].update(ancestors=[""]),
             "/class_definitions/DEMO_GROUP/ancestors/0", "non-empty class name"),
            (lambda d: d["class_definitions"]["DEMO_GROUP"]["functions"]["item_count"].update(
                result={"_type": "P_BMM_SIMPLE_TYPE", "type": "List<Integer>"}),
             "/class_definitions/DEMO_GROUP/functions/item_count/result/type", "not a class name"),
            (lambda d: d["class_definitions"]["DEMO_GROUP"]["properties"]["items"]["type_def"].update(index_type="String"),
             G + "items/type_def/index_type", "the index is dropped"),
        ]
        for change, path, text in cases:
            with self.subTest(path=path, text=text):
                d = self.demo()
                change(d)
                self.assertFinding(self.check(d), "ERROR", path, text)

    def test_whole_document_of_the_wrong_type(self):
        for value in ([], "x", 3, None):
            with self.subTest(value=value):
                self.assertFinding(self.check(value), "ERROR", "/", "must be a JSON object")


class CommandLineTest(Base):
    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                code = check_bmm.main([str(a) for a in args])
            except SystemExit as exc:
                code = exc.code
        return code, out.getvalue(), err.getvalue()

    def test_clean_file_exits_zero(self):
        path = self.write("openehr_demo_0.1.0.bmm.json", self.demo())
        code, out, _ = self.run_main(path, "-d", self.base)
        self.assertEqual(code, 0)
        self.assertIn("5 class(es), 0 error(s), 0 warning(s), 0 name(s) not checked", out)

    def test_errors_exit_one(self):
        d = self.demo()
        del d["class_definitions"]["DEMO_ITEM"]["properties"]["uid"]["type"]
        code, out, _ = self.run_main(self.write("openehr_demo_0.1.0.bmm.json", d), "-d", self.base)
        self.assertEqual(code, 1)
        self.assertIn("ERROR", out)

    def test_strict_fails_on_warnings(self):
        path = self.write("demo.bmm.json", self.demo())
        self.assertEqual(self.run_main(path, "-d", self.base)[0], 0)
        self.assertEqual(self.run_main(path, "-d", self.base, "--strict")[0], 1)

    def test_unloaded_include_makes_the_check_incomplete(self):
        path = self.write("openehr_demo_0.1.0.bmm.json", self.demo())
        for extra in ((), ("--strict",)):
            with self.subTest(args=extra):
                code, out, err = self.run_main(path, *extra)
                self.assertEqual(code, 3)
                self.assertIn("name(s) not checked", out)
                self.assertIn("incomplete", err)

    def test_errors_outrank_an_incomplete_check(self):
        d = self.demo()
        del d["class_definitions"]["DEMO_ITEM"]["properties"]["uid"]["type"]
        self.assertEqual(self.run_main(self.write("openehr_demo_0.1.0.bmm.json", d))[0], 1)

    def test_unreadable_input_exits_two(self):
        broken = self.root / "broken.bmm.json"
        broken.write_text("{\"bmm_version\": ", encoding="utf-8")
        latin = self.root / "latin.bmm.json"
        latin.write_bytes("{\"schema_author\": \"Jos\xe9\"}".encode("latin-1"))
        good = self.write("openehr_demo_0.1.0.bmm.json", self.demo())
        cases = [((broken,), "not valid JSON"), ((latin,), "not UTF-8"), ((self.root / "absent.bmm.json",), "cannot read"),
                 ((good, "-d", self.root / "absent.bmm.json"), "cannot read"), ((good, "-d", latin), "not UTF-8")]
        for args, text in cases:
            with self.subTest(text=text):
                code, _, err = self.run_main(*args)
                self.assertEqual(code, 2)
                self.assertIn(text, err)


if __name__ == "__main__":
    unittest.main()
