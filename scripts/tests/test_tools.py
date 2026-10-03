import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import json
import os
import subprocess
import sys
import tempfile


SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RegistryParserTests(unittest.TestCase):
    def test_arguments_stop_at_the_registration_call(self):
        parser = load_script("extract_registry")
        arguments = parser.split_args('{dark: nested("a,b", .5), light: "#fff"}, "description");other(1,2)', 0)
        self.assertEqual(arguments, ['{dark: nested("a,b", .5), light: "#fff"}', '"description"'])

    def test_escaped_quotes_and_nested_arrays(self):
        parser = load_script("extract_registry")
        self.assertEqual(parser.split_args(r'"a\",b", [foo(1,2), {light:"#fff"}])tail', 0),
                         [r'"a\",b"', '[foo(1,2), {light:"#fff"}]'])

    def test_named_alpha_is_preserved_for_hex_and_references(self):
        parser = load_script("derive_colors")
        parser.NUM["opacity"] = 0.25
        parser.VAR2ID["base"] = "editor.foreground"
        self.assertEqual(parser.resolve('$e.white.transparent(opacity)'), ("hex", (255, 255, 255, 0.25)))
        self.assertEqual(parser.resolve('Ci(base, opacity)'), ("id", "editor.foreground", 0.25))

    def test_light_anchors_do_not_reuse_dark_defaults(self):
        parser = load_script("derive_colors")
        parser.REG = {"editor.background": {"dark": '"#000000"', "light": '"#ffffff"'}}
        self.assertNotEqual(parser.build_anchors("dark"), parser.build_anchors("light"))


class ContrastTests(unittest.TestCase):
    def setUp(self):
        self.checker = load_script("check_contrast")
        self.theme = json.loads((ROOT / "themes/sakura-macaron-light.json").read_text(encoding="utf-8"))

    def test_black_white_and_alpha_compositing(self):
        self.assertEqual(self.checker.contrast("#000000", "#ffffff"), 21)
        self.assertEqual(self.checker.composite("#ffffff80", "#000000"), "#808080")
        self.assertEqual(self.checker.parse_hex("#1234"), (17, 34, 51, 68))

    def test_diff_text_is_composited_over_diff_line(self):
        colors = self.theme["colors"]
        surfaces = self.checker.syntax_surfaces(colors)
        line = self.checker.composite(colors["diffEditor.removedLineBackground"], colors["editor.background"])
        expected = self.checker.composite(colors["diffEditor.removedTextBackground"], line)
        self.assertEqual(surfaces["diff.removed.text"], expected)

    def test_textmate_and_semantic_low_contrast_are_failures(self):
        self.theme["tokenColors"][0]["settings"]["foreground"] = self.theme["colors"]["editor.background"]
        self.theme["semanticTokenColors"]["variable"] = self.theme["colors"]["editor.background"]
        report = self.checker.audit(self.theme)
        self.assertTrue(any(row["category"] == "textmate" for row in report["failures"]))
        self.assertTrue(any(row["category"] == "semantic" for row in report["failures"]))

    def test_missing_pairs_are_reported(self):
        del self.theme["colors"]["button.foreground"]
        report = self.checker.audit(self.theme)
        self.assertTrue(any("button.foreground" in row.get("missing", []) for row in report["skipped"]))

    def test_missing_base_is_reported_without_crashing(self):
        del self.theme["colors"]["editor.background"]
        report = self.checker.audit(self.theme)
        self.assertTrue(any("editor.background" in row.get("missing", []) for row in report["skipped"]))

    def test_style_only_semantic_rules_are_explicitly_unmeasured(self):
        self.theme["semanticTokenColors"]["*.readonly"] = {"bold": True}
        report = self.checker.audit(self.theme)
        self.assertTrue(any("*.readonly" in row["label"] for row in report["skipped"]))

    def test_both_current_themes_have_full_audit_coverage(self):
        for kind in ("dark", "light"):
            theme = json.loads((ROOT / f"themes/sakura-macaron-{kind}.json").read_text(encoding="utf-8"))
            report = self.checker.audit(theme)
            self.assertEqual(report["failures"], [])
            self.assertEqual(report["skipped"], [])
            self.assertEqual(report["checked"]["ui"], len(self.checker.PAIRS))
            self.assertEqual(report["checked"]["textmate"], len(theme["tokenColors"]) * 6)
            self.assertEqual(report["checked"]["semantic"], len(theme["semanticTokenColors"]) * 6)


class DarkDesignTests(unittest.TestCase):
    def setUp(self):
        self.checker = load_script("check_contrast")
        self.theme = json.loads((ROOT / "themes/sakura-macaron-dark.json").read_text(encoding="utf-8"))
        self.colors = self.theme["colors"]

    def test_surface_layers_and_modern_variants_stay_consistent(self):
        for key in ("editorGutter.background", "tab.activeBackground", "modernEditorTab.activeBackground", "modernTab.activeBackground"):
            self.assertEqual(self.colors[key], self.colors["editor.background"], key)
        self.assertEqual(self.colors["modernUI.shellBackground"], self.colors["titleBar.activeBackground"])
        self.assertEqual(self.colors["modernUI.inactiveShellBackground"], self.colors["titleBar.inactiveBackground"])
        self.assertEqual(self.colors["modernActivityBar.inactiveBackground"], self.colors["activityBar.background"])
        for key in ("editor.background", "sideBar.background", "activityBar.background", "statusBar.background"):
            red, green, blue, alpha = self.checker.parse_hex(self.colors[key])
            self.assertGreater(red, green, key)
            self.assertGreater(blue, green, key)
            self.assertEqual(alpha, 255, key)

    def test_all_six_bracket_colors_are_visible_on_syntax_surfaces(self):
        for index in range(1, 7):
            key = f"editorBracketHighlight.foreground{index}"
            foreground = self.colors[key]
            self.assertEqual(self.checker.parse_hex(foreground)[3], 255, key)
            for background in self.checker.syntax_surfaces(self.colors).values():
                self.assertGreaterEqual(self.checker.contrast(foreground, background), 4.5, key)

    def test_status_and_button_interaction_text_remains_readable(self):
        for key, background in self.colors.items():
            if not key.startswith("statusBarItem.") or not key.endswith("Background"):
                continue
            foreground = self.colors.get(key.removesuffix("Background") + "Foreground", self.colors["statusBar.foreground"])
            surface = self.checker.over_base(background, self.colors["statusBar.background"])
            self.assertGreaterEqual(self.checker.contrast(self.checker.over_base(foreground, surface), surface), 4.5, key)
        for foreground, background in (("button.foreground", "button.hoverBackground"),
                                      ("button.secondaryForeground", "button.secondaryHoverBackground")):
            self.assertGreaterEqual(self.checker.contrast(self.colors[foreground], self.colors[background]), 4.5, background)

    def test_terminal_ansi_roles_are_not_collapsed_to_pink(self):
        ansi = {key: value for key, value in self.colors.items() if key.startswith("terminal.ansi")}
        self.assertEqual(len(set(ansi.values())), 16)
        for key in ("terminal.ansiBlue", "terminal.ansiBrightBlue"):
            red, green, blue, alpha = self.checker.parse_hex(ansi[key])
            self.assertGreater(blue, red, key)
        for key in ("terminal.ansiGreen", "terminal.ansiBrightGreen", "terminal.ansiCyan", "terminal.ansiBrightCyan"):
            red, green, blue, alpha = self.checker.parse_hex(ansi[key])
            self.assertGreater(green, red, key)


class RegistryUpdateTests(unittest.TestCase):
    def test_failed_anchor_update_preserves_both_snapshots(self):
        updater = load_script("update_registry")
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            for filename in ("registry.json", "anchors.json"):
                (output / filename).write_bytes(b"original")
            with patch.object(updater.subprocess, "run", side_effect=[None, subprocess.CalledProcessError(2, "derive")]):
                with self.assertRaises(subprocess.CalledProcessError):
                    updater.update(output_dir=output)
            for filename in ("registry.json", "anchors.json"):
                self.assertEqual((output / filename).read_bytes(), b"original")


class BuildTests(unittest.TestCase):
    def run_builder(self, directory, *arguments):
        return subprocess.run([sys.executable, str(SCRIPTS / "build_themes.py"), "--output-dir", str(directory), *arguments],
                              capture_output=True, text=True, encoding="utf-8",
                              env={**os.environ, "VSCODE_PATH": "/not-installed", "PYTHONIOENCODING": "utf-8"})

    def test_clean_build_and_stale_output_detection(self):
        with tempfile.TemporaryDirectory(prefix="sakura build 空格 ") as temporary:
            output = Path(temporary)
            missing = self.run_builder(output, "--check")
            self.assertEqual(missing.returncode, 1, missing.stdout + missing.stderr)
            built = self.run_builder(output)
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            for kind in ("dark", "light"):
                filename = f"sakura-macaron-{kind}.json"
                self.assertEqual((output / filename).read_bytes(), (ROOT / "themes" / filename).read_bytes())
            self.assertEqual(self.run_builder(output, "--check").returncode, 0)
            target = output / "sakura-macaron-dark.json"
            theme = json.loads(target.read_text(encoding="utf-8"))
            theme["colors"]["editor.background"] = "#000000"
            target.write_text(json.dumps(theme), encoding="utf-8")
            self.assertEqual(self.run_builder(output, "--check").returncode, 1)
            self.assertEqual(self.run_builder(output).returncode, 0)
            self.assertEqual(self.run_builder(output, "--check").returncode, 0)


if __name__ == "__main__":
    unittest.main()
