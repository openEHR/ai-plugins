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

# The BASE types the example uses, as a minimal stand-in for openehr_base_1.3.0.bmm.json.
BASE = {
    "bmm_version": "2.4", "rm_publisher": "openehr", "schema_name": "base", "rm_release": "1.3.0",
    "schema_revision": "1.3.0.2", "schema_lifecycle_state": "stable", "schema_description": "stub",
    "schema_author": "test",
    "packages": {"org.openehr.base.foundation_types": {
        "name": "org.openehr.base.foundation_types",
        "classes": ["Any", "Boolean", "Integer", "String", "Iso8601_date_time", "List", "Hash", "HIER_OBJECT_ID"]}},
    "primitive_types": {
        "Any": {"name": "Any", "is_abstract": True},
        "Boolean": {"name": "Boolean"},
        "Integer": {"name": "Integer"},
        "String": {"name": "String"},
        "Iso8601_date_time": {"name": "Iso8601_date_time"},
        "List": {"name": "List", "generic_parameter_defs": {"T": {"name": "T"}}},
        "Hash": {"name": "Hash", "generic_parameter_defs": {"K": {"name": "K"}, "V": {"name": "V"}}},
    },
    "class_definitions": {"HIER_OBJECT_ID": {"name": "HIER_OBJECT_ID"}},
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

    def messages(self, checker, level):
        return ["%s: %s" % (p, m) for lvl, p, m in checker.findings if lvl == level]

    def assertFinding(self, checker, level, path, text):
        hits = [m for m in self.messages(checker, level) if m.startswith(path + ":") and text in m]
        self.assertTrue(hits, "no %s at %s containing %r in:\n%s"
                        % (level, path, text, "\n".join(lvl + " " + p + ": " + m for lvl, p, m in checker.findings)))


class ExampleTest(Base):
    def test_example_is_clean_with_its_dependency(self):
        checker = self.check(self.demo())
        self.assertEqual(checker.findings, [])

    def test_without_dependency_base_types_are_listed_as_unchecked(self):
        checker = self.check(self.demo(), deps=False)
        self.assertEqual([lvl for lvl, _, _ in checker.findings], ["INFO"])
        self.assertIn("HIER_OBJECT_ID", checker.findings[0][2])


class HeaderTest(Base):
    def test_missing_required_field(self):
        d = self.demo()
        del d["schema_author"]
        self.assertFinding(self.check(d), "ERROR", "/schema_author", "required header field")

    def test_file_name_must_match_schema_id(self):
        self.assertFinding(self.check(self.demo(), name="demo.bmm.json"), "WARNING", "/", "expected openehr_demo_0.1.0.bmm.json")

    def test_revision_follows_release(self):
        d = self.demo()
        d["schema_revision"] = "7"
        self.assertFinding(self.check(d), "WARNING", "/schema_revision", "<rm_release>.<build>")

    def test_spec_only_header_key_is_reported_as_ignored(self):
        d = self.demo()
        d["archetype_parent_class"] = "DEMO_ITEM"
        self.assertFinding(self.check(d), "WARNING", "/archetype_parent_class", "not read by bmm-publisher")

    def test_schema_passed_as_its_own_dependency_is_ignored(self):
        path = self.write("openehr_demo_0.1.0.bmm.json", self.demo())
        checker = check_bmm.Checker(path, [self.base, path]).run()
        self.assertEqual([m for lvl, _, m in checker.findings], ["-d %s is the schema being checked; it is ignored" % path])

    def test_dependency_not_included(self):
        d = self.demo()
        del d["includes"]
        self.assertFinding(self.check(d), "WARNING", "/includes", "loaded with -d but is not included")


class PackageTest(Base):
    def test_class_not_in_any_package_gets_no_table(self):
        d = self.demo()
        d["packages"]["org.openehr.demo.inventory"]["packages"]["box"]["classes"].remove("DEMO_BOX_REF")
        self.assertFinding(self.check(d), "ERROR", "/class_definitions/DEMO_BOX_REF", "not listed in any package")

    def test_listed_class_must_be_defined(self):
        d = self.demo()
        d["packages"]["org.openehr.demo.inventory"]["packages"]["box"]["classes"].append("DEMO_GHOST")
        self.assertFinding(self.check(d), "ERROR", "/packages/org.openehr.demo.inventory/packages/box/classes", "DEMO_GHOST is not defined")

    def test_only_top_level_names_contain_dots(self):
        d = self.demo()
        pkgs = d["packages"]["org.openehr.demo.inventory"]["packages"]
        pkgs["a.b"] = dict(pkgs.pop("box"), name="a.b")
        self.assertFinding(self.check(d), "ERROR", "/packages/org.openehr.demo.inventory/packages/a.b", "only top-level")

    def test_top_level_package_name_drives_table_file_names(self):
        d = self.demo()
        d["packages"] = {"demo": dict(d["packages"]["org.openehr.demo.inventory"], name="demo")}
        self.assertFinding(self.check(d), "WARNING", "/packages/demo", "org.openehr.demo.<package>")

    def test_classes_directly_in_the_component_root_package(self):
        d = self.demo()
        classes = [c for p in d["packages"]["org.openehr.demo.inventory"]["packages"].values() for c in p["classes"]]
        d["packages"] = {"org.openehr.demo": {"name": "org.openehr.demo", "classes": classes}}
        self.assertFinding(self.check(d), "WARNING", "/packages/org.openehr.demo/classes", "org.openehr.demo.org.<class>.adoc")

    def test_package_holding_only_sub_packages_is_accepted(self):
        d = self.demo()
        d["packages"] = {"org.openehr.demo": dict(d["packages"]["org.openehr.demo.inventory"], name="org.openehr.demo")}
        self.assertEqual(self.check(d).findings, [])


class ClassTest(Base):
    def test_key_and_name_differ(self):
        d = self.demo()
        d["class_definitions"]["DEMO_ITEM"]["name"] = "DEMO_THING"
        self.assertFinding(self.check(d), "ERROR", "/class_definitions/DEMO_ITEM", "key and \"name\"")

    def test_unknown_class_type(self):
        d = self.demo()
        d["class_definitions"]["DEMO_STATUS"]["_type"] = "P_BMM_ENUMERATION"
        self.assertFinding(self.check(d), "ERROR", "/class_definitions/DEMO_STATUS", "unknown _type P_BMM_ENUMERATION")

    def test_ancestor_defs_alone_loses_the_parent(self):
        d = self.demo()
        group = d["class_definitions"]["DEMO_GROUP"]
        del group["ancestors"]
        group["ancestor_defs"] = {"DEMO_ITEM": {"_type": "P_BMM_SIMPLE_TYPE", "type": "DEMO_ITEM"}}
        checker = self.check(d)
        self.assertFinding(checker, "ERROR", "/class_definitions/DEMO_GROUP", "has no parent")
        self.assertFinding(checker, "WARNING", "/class_definitions/DEMO_GROUP/ancestor_defs", "not read by bmm-publisher")

    def test_generic_name_in_ancestors(self):
        d = self.demo()
        d["class_definitions"]["DEMO_GROUP"]["ancestors"] = ["DEMO_BOX<DEMO_ITEM>"]
        self.assertFinding(self.check(d), "ERROR", "/class_definitions/DEMO_GROUP/ancestors/0", "root class (DEMO_BOX)")

    def test_inheritance_cycle(self):
        d = self.demo()
        d["class_definitions"]["DEMO_ITEM"]["ancestors"] = ["DEMO_GROUP"]
        self.assertFinding(self.check(d), "ERROR", "/class_definitions/DEMO_GROUP",
                           "inheritance cycle: DEMO_ITEM -> DEMO_GROUP -> DEMO_ITEM")

    def test_enumeration_lists_must_line_up(self):
        d = self.demo()
        d["class_definitions"]["DEMO_STATUS"]["item_documentations"].pop()
        self.assertFinding(self.check(d), "ERROR", "/class_definitions/DEMO_STATUS/item_documentations", "one text per item name (3)")

    def test_enumeration_value_kind(self):
        d = self.demo()
        d["class_definitions"]["DEMO_STATUS"]["item_values"] = [1, 2, 3]
        self.assertFinding(self.check(d), "ERROR", "/class_definitions/DEMO_STATUS/item_values", "must be Strings")

    def test_constant_needs_a_type(self):
        d = self.demo()
        del d["class_definitions"]["DEMO_ITEM"]["constants"]["Max_tags"]["type"]
        self.assertFinding(self.check(d), "ERROR", "/class_definitions/DEMO_ITEM/constants/Max_tags", "needs a \"type\"")

    def test_invariants_map_tags_to_strings(self):
        d = self.demo()
        d["class_definitions"]["DEMO_ITEM"]["invariants"] = ["not name.is_empty()"]
        self.assertFinding(self.check(d), "ERROR", "/class_definitions/DEMO_ITEM/invariants", "tag to an expression")


class PropertyTest(Base):
    P = "/class_definitions/DEMO_GROUP/properties/"

    def props(self, d, cls="DEMO_GROUP"):
        return d["class_definitions"][cls]["properties"]

    def test_misspelt_property_type_falls_back(self):
        d = self.demo()
        self.props(d)["items"]["_type"] = "P_BMM_CONTAINER_PROPRETY"
        self.assertFinding(self.check(d), "ERROR", self.P + "items", "read as P_BMM_SINGLE_PROPERTY")

    def test_container_without_type_becomes_any(self):
        d = self.demo()
        del self.props(d)["items"]["_type"]
        self.assertFinding(self.check(d), "ERROR", self.P + "items", "defaults to Any")

    def test_indexed_container_is_not_read(self):
        d = self.demo()
        self.props(d)["index"] = {"_type": "P_BMM_INDEXED_CONTAINER_PROPERTY", "name": "index", "documentation": "x",
                                  "type_def": {"container_type": "Hash", "index_type": "String", "type": "DEMO_ITEM"}}
        self.assertFinding(self.check(d), "ERROR", self.P + "index", "root_type Hash")

    def test_value_set_constraint_loses_the_type(self):
        d = self.demo()
        self.props(d, "DEMO_ITEM")["name"] = {"_type": "P_BMM_SINGLE_PROPERTY", "name": "name", "documentation": "x",
                                              "type_ref": {"type": "String", "value_constraint": "openEHR::languages"}}
        self.assertFinding(self.check(d), "ERROR", "/class_definitions/DEMO_ITEM/properties/name", "read as type Any")

    def test_bounded_upper_needs_upper_unbounded_false(self):
        d = self.demo()
        del self.props(d)["ranks"]["cardinality"]["upper_unbounded"]
        self.assertFinding(self.check(d), "ERROR", self.P + "ranks/cardinality", "\"upper_unbounded\": false")

    def test_upper_below_lower(self):
        d = self.demo()
        self.props(d)["ranks"]["cardinality"]["upper"] = 1
        self.assertFinding(self.check(d), "ERROR", self.P + "ranks/cardinality", "upper is below lower")

    def test_hash_is_not_a_container_type(self):
        d = self.demo()
        self.props(d)["items"]["type_def"]["container_type"] = "Hash"
        self.assertFinding(self.check(d), "ERROR", self.P + "items/type_def/container_type", "Hash takes 2")

    def test_container_needs_an_element_type(self):
        d = self.demo()
        del self.props(d)["items"]["type_def"]["type"]
        self.assertFinding(self.check(d), "ERROR", self.P + "items/type_def", "read as Any")

    def test_generic_parameter_count(self):
        d = self.demo()
        self.props(d)["index"]["type_def"]["generic_parameters"] = ["String"]
        self.assertFinding(self.check(d), "ERROR", self.P + "index/type_def", "Hash takes 2 generic parameters, 1 given")

    def test_nested_type_needs_its_type(self):
        d = self.demo()
        del self.props(d, "DEMO_BOX_REF")["replaced"]["type_def"]["type_def"]["_type"]
        self.assertFinding(self.check(d), "ERROR", "/class_definitions/DEMO_BOX_REF/properties/replaced/type_def/type_def", "no _type")

    def test_open_property_needs_a_declared_parameter(self):
        d = self.demo()
        self.props(d, "DEMO_BOX")["content"]["type"] = "U"
        self.assertFinding(self.check(d), "ERROR", "/class_definitions/DEMO_BOX/properties/content/type", "U is not a generic parameter")

    def test_generic_name_in_type(self):
        d = self.demo()
        self.props(d, "DEMO_ITEM")["uid"]["type"] = "List<String>"
        self.assertFinding(self.check(d), "ERROR", "/class_definitions/DEMO_ITEM/properties/uid/type", "not a class name")

    def test_misspelt_key_is_reported(self):
        d = self.demo()
        uid = self.props(d, "DEMO_ITEM")["uid"]
        uid["is_mandantory"] = uid.pop("is_mandatory")
        self.assertFinding(self.check(d), "ERROR", "/class_definitions/DEMO_ITEM/properties/uid/is_mandantory",
                           "misspelling of is_mandatory")

    def test_unknown_key_that_resembles_nothing_is_a_warning(self):
        d = self.demo()
        self.props(d, "DEMO_ITEM")["uid"]["colour"] = "blue"
        self.assertFinding(self.check(d), "WARNING", "/class_definitions/DEMO_ITEM/properties/uid/colour", "unknown key")

    def test_generic_argument_must_conform(self):
        d = self.demo()
        self.props(d, "DEMO_BOX_REF")["target"]["type_def"]["generic_parameters"] = ["String"]
        self.assertFinding(self.check(d), "ERROR", "/class_definitions/DEMO_BOX_REF/properties/target/type_def/generic_parameters/0",
                           "String does not conform to DEMO_ITEM, the constraint on parameter T of DEMO_BOX")

    def test_nested_generic_argument_must_conform(self):
        d = self.demo()
        nested = self.props(d, "DEMO_BOX_REF")["replaced"]["type_def"]["type_def"]
        nested["generic_parameters"] = ["Integer"]
        self.assertFinding(self.check(d), "ERROR", "/class_definitions/DEMO_BOX_REF/properties/replaced/type_def/type_def/generic_parameters/0",
                           "Integer does not conform to DEMO_ITEM")

    def test_conformance_through_a_descendant(self):
        d = self.demo()
        self.props(d, "DEMO_BOX_REF")["target"]["type_def"]["generic_parameters"] = ["DEMO_ITEM"]
        self.assertEqual(self.check(d).findings, [])

    def test_unresolved_type_name(self):
        d = self.demo()
        self.props(d, "DEMO_ITEM")["uid"]["type"] = "HIER_OBJECT_IDX"
        self.assertFinding(self.check(d), "WARNING", "/class_definitions/DEMO_ITEM/properties/uid/type", "HIER_OBJECT_IDX is not defined")

    def test_attribute_reference_in_documentation(self):
        d = self.demo()
        self.props(d, "DEMO_ITEM")["uid"]["documentation"] = "See {base_release} for details; {1..1} stays literal."
        checker = self.check(d)
        self.assertFinding(checker, "WARNING", "/class_definitions/DEMO_ITEM/properties/uid/documentation", "{base_release}")
        self.assertEqual(len(self.messages(checker, "WARNING")), 1)


class FunctionTest(Base):
    F = "/class_definitions/DEMO_ITEM/functions/is_tagged"

    def fn(self, d):
        return d["class_definitions"]["DEMO_ITEM"]["functions"]["is_tagged"]

    def test_container_parameter_needs_cardinality(self):
        d = self.demo()
        self.fn(d)["parameters"]["a_tag"] = {"_type": "P_BMM_CONTAINER_FUNCTION_PARAMETER", "name": "a_tag",
                                             "type_def": {"container_type": "List", "type": "String"}}
        self.assertFinding(self.check(d), "ERROR", self.F + "/parameters/a_tag", "needs a \"cardinality\"")

    def test_result_needs_its_type(self):
        d = self.demo()
        self.fn(d)["result"] = {"container_type": "List", "type": "String"}
        self.assertFinding(self.check(d), "ERROR", self.F + "/result", "no _type")

    def test_simple_result_without_type_marker(self):
        d = self.demo()
        self.fn(d)["result"] = {"type": "Boolean"}
        self.assertFinding(self.check(d), "WARNING", self.F + "/result", "published schemas always set it")

    def test_void_result_is_accepted(self):
        d = self.demo()
        self.fn(d)["result"] = {"_type": "P_BMM_SIMPLE_TYPE", "type": "void"}
        self.assertEqual(self.check(d).findings, [])

    def test_conditions_map_tags_to_strings(self):
        d = self.demo()
        self.fn(d)["pre_conditions"] = {"Pre_tag_valid": True}
        self.assertFinding(self.check(d), "ERROR", self.F + "/pre_conditions", "tag to an expression")


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
        self.assertIn("0 error(s), 0 warning(s)", out)

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

    def test_invalid_json_exits_two(self):
        path = self.root / "broken.bmm.json"
        path.write_text("{\"bmm_version\": ", encoding="utf-8")
        code, _, err = self.run_main(path)
        self.assertEqual(code, 2)
        self.assertIn("not valid JSON", err)

    def test_missing_file_exits_two(self):
        self.assertEqual(self.run_main(self.root / "absent.bmm.json")[0], 2)


if __name__ == "__main__":
    unittest.main()
