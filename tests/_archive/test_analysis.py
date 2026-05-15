"""Characterization tests for codemonkeys/core/analysis/__init__.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from codemonkeys.core.analysis import (
    ClassInfo,
    FileAnalysis,
    FunctionInfo,
    _extract_classes,
    _extract_functions,
    _extract_imports,
    _format_class,
    _format_function,
    _format_imports,
    analyze_file,
    analyze_files,
    format_analysis,
)


# ---------------------------------------------------------------------------
# analyze_file — success cases
# ---------------------------------------------------------------------------


def test_analyze_file_simple_python(tmp_path: Path) -> None:
    f = tmp_path / "simple.py"
    f.write_text("x = 1\n")
    result = analyze_file(str(f))
    assert result.error is None
    assert result.file == str(f)
    assert result.imports == []
    assert result.functions == []
    assert result.classes == []


def test_analyze_file_extracts_function(tmp_path: Path) -> None:
    code = "def greet(name: str) -> str:\n    return name\n"
    f = tmp_path / "fn.py"
    f.write_text(code)
    result = analyze_file(str(f))
    assert result.error is None
    assert len(result.functions) == 1
    fn = result.functions[0]
    assert fn.name == "greet"
    assert fn.is_async is False
    assert fn.return_type == "str"
    assert len(fn.args) == 1
    assert fn.args[0]["name"] == "name"
    assert fn.args[0]["type"] == "str"


def test_analyze_file_extracts_async_function(tmp_path: Path) -> None:
    code = "async def run() -> None:\n    pass\n"
    f = tmp_path / "async_fn.py"
    f.write_text(code)
    result = analyze_file(str(f))
    assert result.error is None
    assert len(result.functions) == 1
    assert result.functions[0].is_async is True
    assert result.functions[0].name == "run"
    assert result.functions[0].return_type == "None"


def test_analyze_file_extracts_decorated_function(tmp_path: Path) -> None:
    code = "@staticmethod\ndef foo() -> int:\n    return 1\n"
    f = tmp_path / "deco.py"
    f.write_text(code)
    result = analyze_file(str(f))
    assert len(result.functions) == 1
    assert "staticmethod" in result.functions[0].decorators


def test_analyze_file_extracts_class(tmp_path: Path) -> None:
    code = "class MyClass(object):\n    def __init__(self, x: int) -> None:\n        self.x = x\n"
    f = tmp_path / "cls.py"
    f.write_text(code)
    result = analyze_file(str(f))
    assert len(result.classes) == 1
    cls = result.classes[0]
    assert cls.name == "MyClass"
    assert cls.bases == ["object"]
    assert len(cls.methods) == 1
    assert cls.methods[0].name == "__init__"


def test_analyze_file_extracts_import(tmp_path: Path) -> None:
    code = "import os\nfrom pathlib import Path\n"
    f = tmp_path / "imp.py"
    f.write_text(code)
    result = analyze_file(str(f))
    assert len(result.imports) == 2
    # import os → module="os", names=None
    os_import = next(i for i in result.imports if i.get("module") == "os")
    assert os_import["names"] is None
    # from pathlib import Path → module="pathlib", names=["Path"]
    path_import = next(i for i in result.imports if i.get("module") == "pathlib")
    assert path_import["names"] == ["Path"]


def test_analyze_file_with_root(tmp_path: Path) -> None:
    f = tmp_path / "myfile.py"
    f.write_text("y = 2\n")
    result = analyze_file("myfile.py", root=tmp_path)
    assert result.error is None
    assert result.file == "myfile.py"


# ---------------------------------------------------------------------------
# analyze_file — error cases
# ---------------------------------------------------------------------------


def test_analyze_file_syntax_error(tmp_path: Path) -> None:
    f = tmp_path / "broken.py"
    f.write_text("def (this is broken:\n")
    result = analyze_file(str(f))
    assert result.error is not None
    assert result.imports == []
    assert result.file == str(f)


def test_analyze_file_oserror_missing_file() -> None:
    result = analyze_file("/nonexistent/path/does_not_exist.py")
    assert result.error is not None
    assert result.imports == []


# ---------------------------------------------------------------------------
# analyze_files — batch
# ---------------------------------------------------------------------------


def test_analyze_files_batch(tmp_path: Path) -> None:
    a = tmp_path / "a.py"
    b = tmp_path / "b.py"
    a.write_text("x = 1\n")
    b.write_text("y = 2\n")
    results = analyze_files([str(a), str(b)])
    assert len(results) == 2
    assert all(r.error is None for r in results)


def test_analyze_files_tolerates_error(tmp_path: Path) -> None:
    good = tmp_path / "good.py"
    bad = tmp_path / "bad.py"
    good.write_text("x = 1\n")
    bad.write_text("def (\n")
    results = analyze_files([str(good), str(bad)])
    assert len(results) == 2
    good_r = next(r for r in results if r.file == str(good))
    bad_r = next(r for r in results if r.file == str(bad))
    assert good_r.error is None
    assert bad_r.error is not None


def test_analyze_files_empty() -> None:
    results = analyze_files([])
    assert results == []


# ---------------------------------------------------------------------------
# format_analysis
# ---------------------------------------------------------------------------


def test_format_analysis_empty_list() -> None:
    result = format_analysis([])
    assert result == ""


def test_format_analysis_with_error_file() -> None:
    analyses = [FileAnalysis(file="bad.py", imports=[], error="SyntaxError: bad syntax")]
    result = format_analysis(analyses)
    assert "bad.py" in result
    assert "Parse error" in result


def test_format_analysis_with_function(tmp_path: Path) -> None:
    code = "def foo(x: int) -> str:\n    return str(x)\n"
    f = tmp_path / "test.py"
    f.write_text(code)
    analyses = analyze_files([str(f)])
    result = format_analysis(analyses)
    assert "foo" in result
    assert "x: int" in result
    assert "-> str" in result


def test_format_analysis_async_function(tmp_path: Path) -> None:
    code = "async def run() -> None:\n    pass\n"
    f = tmp_path / "async.py"
    f.write_text(code)
    analyses = analyze_files([str(f)])
    result = format_analysis(analyses)
    assert "async run" in result


def test_format_analysis_with_class(tmp_path: Path) -> None:
    code = (
        "class MyClass:\n"
        "    def __init__(self, x: int) -> None:\n"
        "        self.x = x\n"
        "    def method(self) -> int:\n"
        "        return self.x\n"
    )
    f = tmp_path / "cls.py"
    f.write_text(code)
    analyses = analyze_files([str(f)])
    result = format_analysis(analyses)
    assert "class MyClass" in result
    assert "__init__" in result
    assert "method" in result


def test_format_analysis_decorated_class(tmp_path: Path) -> None:
    code = "@dataclass\nclass Point:\n    x: int\n    y: int\n"
    f = tmp_path / "point.py"
    f.write_text(code)
    analyses = analyze_files([str(f)])
    result = format_analysis(analyses)
    assert "dataclass" in result
    assert "class Point" in result


def test_format_analysis_internal_imports(tmp_path: Path) -> None:
    code = "from codemonkeys.core import something\nimport os\n"
    f = tmp_path / "imports.py"
    f.write_text(code)
    analyses = analyze_files([str(f)])
    result = format_analysis(analyses)
    assert "Internal imports" in result
    assert "External imports" in result


def test_format_analysis_external_only_imports(tmp_path: Path) -> None:
    code = "import sys\nimport os\n"
    f = tmp_path / "ext.py"
    f.write_text(code)
    analyses = analyze_files([str(f)])
    result = format_analysis(analyses)
    assert "External imports" in result


def test_format_analysis_multiple_files(tmp_path: Path) -> None:
    a = tmp_path / "a.py"
    b = tmp_path / "b.py"
    a.write_text("def func_a(): pass\n")
    b.write_text("def func_b(): pass\n")
    analyses = analyze_files([str(a), str(b)])
    result = format_analysis(analyses)
    assert "func_a" in result
    assert "func_b" in result


# ---------------------------------------------------------------------------
# _format_imports — internal helper
# ---------------------------------------------------------------------------


def test_format_imports_internal_module() -> None:
    imports = [{"module": "codemonkeys.core.types", "names": ["AgentDefinition"]}]
    lines = _format_imports(imports)
    assert any("Internal imports" in line for line in lines)
    assert not any("External imports" in line for line in lines)


def test_format_imports_external_module() -> None:
    imports = [{"module": "os", "names": None}]
    lines = _format_imports(imports)
    assert any("External imports" in line for line in lines)
    assert not any("Internal imports" in line for line in lines)


def test_format_imports_os_dot_module_is_external() -> None:
    # os.path has a dot but starts with os. → external
    imports = [{"module": "os.path", "names": ["join"]}]
    lines = _format_imports(imports)
    assert any("External imports" in line for line in lines)
    assert not any("Internal imports" in line for line in lines)


def test_format_imports_with_names_list() -> None:
    imports = [{"module": "pathlib", "names": ["Path", "PurePath"]}]
    lines = _format_imports(imports)
    combined = "\n".join(lines)
    assert "Path, PurePath" in combined


def test_format_imports_empty() -> None:
    lines = _format_imports([])
    assert lines == []


def test_format_imports_both_internal_and_external() -> None:
    imports = [
        {"module": "os", "names": None},
        {"module": "mypackage.sub", "names": ["Thing"]},
    ]
    lines = _format_imports(imports)
    combined = "\n".join(lines)
    assert "Internal imports" in combined
    assert "External imports" in combined


# ---------------------------------------------------------------------------
# _format_function — internal helper
# ---------------------------------------------------------------------------


def test_format_function_sync_no_args() -> None:
    fn = FunctionInfo(name="foo", is_async=False, args=[], return_type=None, decorators=[])
    result = _format_function(fn, indent="  ")
    assert result == "  foo()"


def test_format_function_async() -> None:
    fn = FunctionInfo(name="bar", is_async=True, args=[], return_type="None", decorators=[])
    result = _format_function(fn, indent="")
    assert result == "async bar() -> None"


def test_format_function_with_args_and_return() -> None:
    fn = FunctionInfo(
        name="greet",
        is_async=False,
        args=[{"name": "name", "type": "str"}, {"name": "count", "type": "int"}],
        return_type="str",
        decorators=[],
    )
    result = _format_function(fn, indent="  ")
    assert "greet(name: str, count: int) -> str" in result


def test_format_function_skips_self_arg() -> None:
    fn = FunctionInfo(
        name="method",
        is_async=False,
        args=[{"name": "self", "type": None}, {"name": "x", "type": "int"}],
        return_type=None,
        decorators=[],
    )
    result = _format_function(fn, indent="    ")
    assert "self" not in result
    assert "x: int" in result


def test_format_function_arg_without_type() -> None:
    fn = FunctionInfo(
        name="func",
        is_async=False,
        args=[{"name": "val", "type": None}],
        return_type=None,
        decorators=[],
    )
    result = _format_function(fn, indent="")
    assert "val" in result
    assert ":" not in result


def test_format_function_with_decorator() -> None:
    fn = FunctionInfo(
        name="prop",
        is_async=False,
        args=[],
        return_type="int",
        decorators=["property"],
    )
    result = _format_function(fn, indent="")
    assert "@property" in result


# ---------------------------------------------------------------------------
# _format_class — internal helper
# ---------------------------------------------------------------------------


def test_format_class_simple() -> None:
    cls = ClassInfo(name="MyClass", bases=[], decorators=[], methods=[])
    lines = _format_class(cls)
    assert any("class MyClass" in line for line in lines)


def test_format_class_with_bases() -> None:
    cls = ClassInfo(name="Child", bases=["Parent", "Mixin"], decorators=[], methods=[])
    lines = _format_class(cls)
    assert any("class Child(Parent, Mixin)" in line for line in lines)


def test_format_class_with_decorator() -> None:
    cls = ClassInfo(name="Foo", bases=[], decorators=["dataclass"], methods=[])
    lines = _format_class(cls)
    assert any("@dataclass" in line for line in lines)


def test_format_class_init_method_formatted_specially() -> None:
    init = FunctionInfo(
        name="__init__",
        is_async=False,
        args=[{"name": "self", "type": None}, {"name": "x", "type": "int"}],
        return_type=None,
        decorators=[],
    )
    cls = ClassInfo(name="Box", bases=[], decorators=[], methods=[init])
    lines = _format_class(cls)
    combined = "\n".join(lines)
    assert "__init__(x: int)" in combined


def test_format_class_non_init_method() -> None:
    method = FunctionInfo(
        name="run",
        is_async=False,
        args=[{"name": "self", "type": None}],
        return_type="None",
        decorators=[],
    )
    cls = ClassInfo(name="Runner", bases=[], decorators=[], methods=[method])
    lines = _format_class(cls)
    combined = "\n".join(lines)
    assert "run()" in combined
    assert "-> None" in combined


