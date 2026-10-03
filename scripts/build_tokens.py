#!/usr/bin/env python3
"""生成 TextMate tokenColors 与 semanticTokenColors。

原主题只有 15 条 token 规则 / 57 个 scope，而成熟主题（GitHub 官方 73 个 scope、
One Dark Pro 303 个 scope）覆盖完整得多，导致 Markdown 预览、正则、diff 元信息、
常量、转义符等位置颜色不对。本脚本按模块补齐，并补全语义高亮的 defaultLibrary 组合
与 modifier（declaration/documentation/static/readonly/...）组合。

用法：python3 scripts/build_tokens.py [--check]
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEMES = os.path.join(HERE, "themes")

# 每套主题的语义色板（与 themes/*.json 的既有取色保持一致）
PALETTE = {
    "dark": {
        "fg": "#CCCCCC",
        "comment": "#9B8A9E",
        "keyword": "#87A3D6",
        "func": "#CBA8B9",
        "string": "#85B59A",
        "regexp": "#A3CBA8",
        "number": "#F2D199",
        "type": "#E27E7E",
        "const": "#D6A461",
        "punctuation": "#9B8A9E",
        "operator": "#A3B1D6",
        "tag": "#87A3D6",
        "attr": "#9B8A9E",
        "invalid": "#C25B5B",
        "heading": "#87A3D6",
        "link": "#87A3D6",
        "quote": "#9B8A9E",
        "added": "#85B59A",
        "removed": "#E27E7E",
        "changed": "#D6A461",
        "untracked": "#85B59A",
        "namespace": "#CBA8B9",
        "decorator": "#F2D199",
        "parameter": "#CBA8B9",
        "property": "#9B8A9E",
        "enumMember": "#F2D199",
        "bracket1": "#F2D199",
        "bracket2": "#C45A6D",
        "bracket3": "#87A3D6",
        "bracket4": "#85B59A",
        "bracket5": "#CBA8B9",
        "bracket6": "#D6A461",
        "label": "#F2D199",
    },
    "light": {
        "fg": "#3A3132",
        "comment": "#6A8A76",
        "keyword": "#C84B5D",
        "func": "#327A85",
        "string": "#6B965C",
        "regexp": "#5B8A4E",
        "number": "#D8823B",
        "type": "#875C96",
        "const": "#C07A3A",
        "punctuation": "#BFA4AE",
        "operator": "#C45A6D",
        "tag": "#C84B5D",
        "attr": "#6A8A76",
        "invalid": "#7E2A3C",
        "heading": "#C45A6D",
        "link": "#C45A6D",
        "quote": "#6A8A76",
        "added": "#6B965C",
        "removed": "#C07A3A",
        "changed": "#C07A3A",
        "untracked": "#6B965C",
        "namespace": "#327A85",
        "decorator": "#D8823B",
        "parameter": "#327A85",
        "property": "#6A8A76",
        "enumMember": "#C07A3A",
        "bracket1": "#C07A3A",
        "bracket2": "#7E2A3C",
        "bracket3": "#C84B5D",
        "bracket4": "#6B965C",
        "bracket5": "#327A85",
        "bracket6": "#875C96",
        "label": "#D8823B",
    },
}

# --------------------------------------------------------------------------
# TextMate tokenColors：按模块分组，顺序即优先级（后面的规则覆盖前面的）
# --------------------------------------------------------------------------
def token_rules(p):
    return [
        # --- 注释 ---
        (["comment", "punctuation.definition.comment"], {"foreground": p["comment"], "fontStyle": "italic"}),
        # --- 关键字 / 存储 ---
        (["keyword", "keyword.control", "keyword.other", "storage", "storage.type",
          "storage.modifier", "keyword.declaration", "keyword.function"], {"foreground": p["keyword"]}),
        (["storage.type.function", "storage.type.class", "storage.type.enum"],
         {"foreground": p["func"]}),
        (["storage.type.primitive", "storage.type.builtin"], {"foreground": p["type"]}),
        # --- 函数 ---
        (["entity.name.function", "support.function", "meta.function-call", "variable.function"],
         {"foreground": p["func"]}),
        # --- 字符串 / 正则 / 转义 ---
        (["string", "string.quoted", "string.template", "punctuation.definition.string"],
         {"foreground": p["string"]}),
        (["string.regexp", "string.regexp.character-class", "constant.character.escape",
          "source.regexp", "constant.other.character-class", "punctuation.definition.character-class"],
         {"foreground": p["regexp"]}),
        (["string.quoted.other.literal", "string.quoted.double", "string.quoted.single"],
         {"foreground": p["string"]}),
        (["string.other.link", "string.other.link.uri", "constant.other.reference.link",
          "markup.underline.link"], {"foreground": p["link"]}),
        (["string.comment", "comment.block.documentation"], {"foreground": p["comment"]}),
        (["string variable", "string interpolation"], {"foreground": p["fg"]}),
        (["punctuation.section.embedded", "punctuation.section.embedded.begin",
          "punctuation.section.embedded.end"], {"foreground": p["keyword"]}),
        # --- 数字 / 常量 ---
        (["constant.numeric", "constant.numeric.integer", "constant.numeric.float"],
         {"foreground": p["number"]}),
        (["constant.language", "constant.other", "support.constant", "variable.language"],
         {"foreground": p["const"]}),
        (["constant", "constant.other.placeholder"], {"foreground": p["const"]}),
        (["variable.other.constant", "variable.other.enummember"],
         {"foreground": p["enumMember"]}),
        (["support.variable", "support.constant.property", "variable.other.property"],
         {"foreground": p["property"]}),
        (["support.type.property-name", "support.type.property-name.json",
          "entity.name.constant", "variable.other.constant.object"], {"foreground": p["property"]}),
        # --- 类型 / 类 ---
        (["entity.name.type", "entity.name.class", "support.type", "support.class",
          "entity.other.inherited-class", "meta.type.cast"], {"foreground": p["type"]}),
        (["entity.name.type.interface", "entity.name.type.enum", "entity.name.type.struct",
          "support.type.interface"], {"foreground": p["type"]}),
        (["entity.name.type.parameter", "entity.name.type.annotation"], {"foreground": p["type"]}),
        # --- 变量 ---
        (["variable", "variable.other", "variable.other.readwrite", "variable.other.object",
          "meta.definition.variable"], {"foreground": p["fg"]}),
        (["variable.parameter", "variable.parameter.function", "meta.parameters"],
         {"foreground": p["parameter"]}),
        (["variable.annotation", "variable.other.property"], {"foreground": p["parameter"]}),
        (["meta.object.member", "meta.object.literal", "meta.field"],
         {"foreground": p["property"]}),
        (["meta.property-name", "punctuation.separator.dot", "meta.separator"],
         {"foreground": p["punctuation"]}),
        # --- 标签 / 属性 ---
        (["entity.name.tag", "meta.tag", "punctuation.definition.tag"], {"foreground": p["tag"]}),
        # semanticTokenColors 不支持 tag（它不是注册的 token 类型），
        # 标签高亮完全由上面的 TextMate entity.name.tag 负责。
        (["entity.name.label", "entity.name.goto-label", "entity.name.lifetime",
          "constant.character.entity"], {"foreground": p["label"]}),
        (["punctuation.quasi.element", "punctuation.definition.constant",
          "punctuation.definition.asciidoc"], {"foreground": p["punctuation"]}),
        (["token.info-token", "token.debug-token", "token.package",
          "constant.other.symbol"], {"foreground": p["string"]}),
        (["log.info", "log.warning", "log.error"], {"foreground": p["comment"]}),
        (["meta.embedded", "meta.method.java", "meta.embedded.block"],
         {"foreground": p["fg"]}),
        (["meta.block.scope.begin", "meta.block.scope.end", "block.scope.begin",
          "block.scope.end"], {"foreground": p["punctuation"]}),
        (["entity.name.section", "entity.other.attribute-name", "entity.other.attribute-name.id",
          "meta.tag.attributes", "meta.tag.structure"], {"foreground": p["attr"]}),
        # --- 运算符 / 标点 ---
        (["keyword.operator", "keyword.operator.logical", "keyword.operator.arithmetic",
          "keyword.operator.assignment"], {"foreground": p["operator"]}),
        (["punctuation", "meta.brace", "meta.delimiter", "punctuation.separator",
          "punctuation.terminator", "meta.block"], {"foreground": p["punctuation"]}),
        (["punctuation.definition.list.begin.markdown", "punctuation.definition.list.end.markdown"],
         {"foreground": p["punctuation"]}),
        # --- 命名空间 / 装饰器 ---
        (["entity.name.namespace", "entity.name.module", "support.namespace", "meta.namespace",
          "entity.name.scope-resolution"], {"foreground": p["namespace"]}),
        (["meta.annotation", "meta.decorator", "storage.type.annotation",
          "meta.decorator.tsx"], {"foreground": p["decorator"]}),
        (["meta.export.default", "meta.module-reference", "meta.import",
          "keyword.control.import", "keyword.control.export"], {"foreground": p["keyword"]}),
        (["storage.modifier.import", "storage.modifier.package", "storage.modifier.export"],
         {"foreground": p["keyword"]}),
        (["meta.embedded.expression", "meta.embedded.line", "meta.template.expression"],
         {"foreground": p["fg"]}),
        (["meta.jsx.children", "meta.jsx.text"], {"foreground": p["fg"]}),
        (["meta.object.member", "support.class.component"], {"foreground": p["property"]}),
        # --- Markdown / 富文本 ---
        (["markup.heading", "markup.heading entity.name", "punctuation.definition.heading",
          "entity.name.section.markdown"], {"foreground": p["heading"], "fontStyle": "bold"}),
        (["markup.bold", "markup.bold.markdown", "punctuation.definition.bold"],
         {"foreground": p["fg"], "fontStyle": "bold"}),
        (["markup.italic", "markup.italic.markdown", "punctuation.definition.italic"],
         {"foreground": p["fg"], "fontStyle": "italic"}),
        (["markup.bold.italic", "markup.bold.italic.markdown"],
         {"foreground": p["fg"], "fontStyle": "bold italic"}),
        (["markup.underline", "markup.underline.markdown", "punctuation.definition.underline"],
         {"foreground": p["fg"], "fontStyle": "underline"}),
        (["markup.strikethrough", "punctuation.definition.strikethrough"],
         {"foreground": p["comment"], "fontStyle": "strikethrough"}),
        (["markup.inline.raw", "markup.inline.raw.string", "markup.fenced_code",
          "markup.code", "markup.code.block"], {"foreground": p["string"]}),
        (["markup.quote", "markup.quote.markdown", "punctuation.definition.quote"],
         {"foreground": p["quote"], "fontStyle": "italic"}),
        (["markup.list", "markup.list.unnumbered", "markup.list.numbered",
          "punctuation.definition.list.begin", "beginning.punctuation.definition.list"],
         {"foreground": p["keyword"]}),
        (["markup.italic.link", "markup.bold.link"], {"foreground": p["link"], "fontStyle": "underline"}),
        (["markup.underline.link.image", "string.other.link.image.title"],
         {"foreground": p["link"]}),
        (["markup.inserted", "punctuation.definition.inserted"], {"foreground": p["added"]}),
        (["markup.deleted", "punctuation.definition.deleted"], {"foreground": p["removed"]}),
        (["markup.changed", "punctuation.definition.changed"], {"foreground": p["changed"]}),
        (["markup.untracked", "markup.untracked.inserted"], {"foreground": p["untracked"]}),
        (["markup.ignored", "punctuation.definition.ignored"], {"foreground": p["comment"]}),
        # --- Diff 元信息 ---
        (["meta.diff.header", "meta.diff.header.from-file", "meta.diff.header.to-file",
          "meta.diff.header.git", "meta.diff.range"], {"foreground": p["comment"], "fontStyle": "italic"}),
        (["meta.diff.index"], {"foreground": p["comment"]}),
        (["punctuation.definition.inserted.diff", "punctuation.definition.changed.diff"],
         {"foreground": p["added"]}),
        (["punctuation.definition.deleted.diff"], {"foreground": p["removed"]}),
        (["meta.output", "meta.output.markdown", "meta.output.stdout", "meta.output.stderr"],
         {"foreground": p["fg"]}),
        # --- 提示信息 ---
        (["message.error", "message.error.line"], {"foreground": p["invalid"]}),
        # --- 括号配对高亮 ---
        (["brackethighlighter.angle", "brackethighlighter.round"], {"foreground": p["bracket1"]}),
        (["brackethighlighter.curly"], {"foreground": p["bracket2"]}),
        (["brackethighlighter.square"], {"foreground": p["bracket3"]}),
        (["brackethighlighter.tag"], {"foreground": p["bracket4"]}),
        (["brackethighlighter.quote"], {"foreground": p["bracket5"]}),
        (["brackethighlighter.unmatched"], {"foreground": p["invalid"], "fontStyle": "underline"}),
        # --- 无效 / 弃用 ---
        (["invalid", "invalid.illegal"], {"foreground": p["invalid"]}),
        (["invalid.broken", "invalid.broken.link"], {"foreground": p["invalid"], "fontStyle": "underline"}),
        (["invalid.deprecated"], {"foreground": p["invalid"], "fontStyle": "strikethrough"}),
        (["invalid.unimplemented"], {"foreground": p["invalid"], "fontStyle": "underline"}),
        (["carriage-return", "invalid.carriage-return"], {"foreground": p["invalid"]}),
        # --- 杂项 ---
        (["support.type.primitive"], {"foreground": p["type"]}),
        (["entity", "entity.name"], {"foreground": p["fg"]}),
        (["support"], {"foreground": p["fg"]}),
    ]


# --------------------------------------------------------------------------
# semanticTokenColors：基础类型 + defaultLibrary 组合 + modifier 组合
# --------------------------------------------------------------------------
def semantic_colors(p):
    base = {
        "namespace": p["namespace"],
        "class": p["type"],
        "enum": p["type"],
        "enumMember": p["enumMember"],
        "function": p["func"],
        "interface": p["type"],
        "struct": p["type"],
        "typeParameter": p["type"],
        "type": p["type"],
        "parameter": p["parameter"],
        "variable": p["fg"],
        "property": p["property"],
        "event": p["type"],
        "method": p["func"],
        "macro": p["const"],
        "label": p["decorator"],
        "comment": p["comment"],
        "string": p["string"],
        "keyword": p["keyword"],
        "number": p["number"],
        "regexp": p["regexp"],
        "operator": p["operator"],
        "decorator": p["decorator"],
        "selfKeyword": p["keyword"],
        "newKeyword": p["keyword"],
        "controlKeyword": p["keyword"],
        "otherKeyword": p["keyword"],
    }
    lib = p["const"]          # 标准库：偏暖金，区别于用户代码
    readonly = p["const"]     # 只读：常量色
    decl = p["fg"]            # 声明处：正文色
    doc = p["comment"]        # 文档注释：注释色
    static = p["type"]        # static 成员：类型色
    deprecated = p["comment"]

    out = dict(base)
    out.update({
        # 扩展注册的自定义 token 类型（官方扩展通过 semanticTokenTypes 扩展点注册）
        # TypeScript/JavaScript
        "selfKeyword": p["keyword"],
        "newKeyword": p["keyword"],
        "controlKeyword": p["keyword"],
        "otherKeyword": p["keyword"],
        # Python (Pylance)
        "intrinsic": lib,
        "magicFunction": lib,
        "builtinConstant": lib,
        "selfParameter": p["parameter"],
        "clsParameter": p["parameter"],
        "typeHint": p["type"],
        "typeHintComment": p["comment"],
        # Rust (rust-analyzer)
        "selfTypeKeyword": p["keyword"],
        "builtinType": p["type"],
        "builtinAttribute": p["decorator"],
        "lifetime": p["number"],
        "toolModule": lib,
        # C/C++ (cpptools)
        "referenceType": p["type"],
        "genericType": p["type"],
        "valueType": p["number"],
        "templateFunction": p["func"],
        "templateType": p["type"],
        "operatorOverload": p["operator"],
        "memberOperatorOverload": p["operator"],
        "customLiteral": p["string"],
        "numberLiteral": p["number"],
        "stringLiteral": p["string"],
    })
    out.update({
        # defaultLibrary 组合
        "variable.defaultLibrary": lib,
        "variable.defaultLibrary.readonly": lib,
        "variable.readonly": readonly,
        "property.defaultLibrary": lib,
        "property.defaultLibrary.readonly": lib,
        "property.readonly": readonly,
        "type.defaultLibrary": lib,
        "class.defaultLibrary": lib,
        "interface.defaultLibrary": lib,
        "function.defaultLibrary": lib,
        "member.defaultLibrary": lib,
        "method.defaultLibrary": lib,
        # modifier 组合
        "variable.declaration": decl,
        "parameter.declaration": decl,
        "property.declaration": decl,
        "property.static": static,
        "property.readonly.declaration": decl,
        "function.declaration": decl,
        "method.declaration": decl,
        "class.declaration": decl,
        "interface.declaration": decl,
        "enum.declaration": decl,
        "enumMember.declaration": decl,
        "struct.declaration": decl,
        "typeParameter.declaration": decl,
        "type.declaration": decl,
        "namespace.declaration": decl,
        "macro.declaration": decl,
        "decorator.declaration": decl,
        "label.declaration": decl,
        "event.declaration": decl,
        # 文档 / 弃用
        "comment.documentation": doc,
        "variable.documentation": doc,
        "function.documentation": doc,
        "property.documentation": doc,
        "variable.deprecated": deprecated,
        "function.deprecated": deprecated,
        "property.deprecated": deprecated,
        "class.deprecated": deprecated,
        "variable.modification": p["changed"],
        "property.modification": p["changed"],
        "variable.abstract": p["type"],
        "class.abstract": p["type"],
        "variable.async": p["func"],
        "function.async": p["func"],
    })
    return out


def build(kind):
    p = PALETTE[kind]
    tokens = [{"scope": s, "settings": st} for s, st in token_rules(p)]
    return tokens, semantic_colors(p)


def main():
    check = "--check" in sys.argv
    HEX = re.compile(r"^#(?:[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$")
    for kind, fname in (("dark", "sakura-macaron-dark.json"), ("light", "sakura-macaron-light.json")):
        path = os.path.join(THEMES, fname)
        theme = json.load(open(path))
        tokens, sem = build(kind)
        bad = [r["scope"] for r in tokens
               if not HEX.match(r["settings"].get("foreground", "#000000"))]
        if bad:
            print(f"{kind}: 非法色值 {bad}")
            sys.exit(1)
        n_scope = sum(len(r["scope"]) for r in tokens)
        print(f"{kind}: tokenColors {len(tokens)} 条规则 / {n_scope} scope，"
              f"semanticTokenColors {len(sem)} 条")
        if check:
            continue
        theme["tokenColors"] = tokens
        theme["semanticTokenColors"] = sem
        with open(path, "w") as f:
            json.dump(theme, f, ensure_ascii=False, indent=2)
            f.write("\n")
    if not check:
        print("已写入 themes/")


if __name__ == "__main__":
    main()
