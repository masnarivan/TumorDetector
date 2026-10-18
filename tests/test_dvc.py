"""dvc.yaml agrees with the code: each stage depends on exactly the code it runs and the config it reads,
and no stage can delete outputs it cannot rebuild.

The code a stage runs is the import closure of its task module (tumordetector/tasks/<task>.py), found
statically; the config it reads is every `cfg.<key>` in the task code it runs (only task modules see the root config).
"""
import ast
import re
from pathlib import Path

import pytest
import yaml
from hydra import compose, initialize_config_dir
from omegaconf import DictConfig

from tumordetector.cli import CONF_DIR

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

# Config read by a stage that does not change what it writes.
UNTRACKED = {
    "task": "the stage's command",
    "backbone.name": "in the stage's command and output paths",
    "paths.out": "where the outputs go: the stage's outs",
    "data.raw_dir": "where the local .tif are; each is checked against the manifest md5",
    "data.keep_slides": "whether the downloaded .tif is kept after embedding",
    "embed.device": "speed (rounding at most, below the float16 the embeddings are stored in)",
    "embed.batch_size": "speed, as embed.device",
    "embed.threads": "speed, as embed.device",
    "mlflow": "run tracking",
    "vectordb": "the database the index is loaded into (url recorded in data/index/<backbone>.json)",
    "mil.workers": "seeds trained in parallel: each seed runs the same as alone (mil.threads is fixed)",
    "mil.experiment": "MLflow experiment name",
    "mil.register": "model registry, outside the stage's outputs",
    "mil.report_dir": "for experiments, which write outside the stage's outputs",
    "mil.overwrite_splits": "read by task=splits only",
    "head.overwrite": "read by task=cohort only",
    "paths.heads": "where the cohort files are: the stage's deps",
}
# Stages whose input is not on disk (slides downloaded and deleted): DVC must never delete their outputs.
REMOTE_INPUT = {"stream"}
DEV_ONLY = {"tile", "embed"}   # need the .tif: they cannot rebuild a full dataset's outputs


def load_dvc():
    text = (ROOT / "dvc.yaml").read_text()
    variables = {k: v for d in yaml.safe_load(text)["vars"] for k, v in d.items()}
    text = re.sub(r"\$\{(\w+)\}", lambda m: str(variables[m.group(1)]), text)
    return yaml.safe_load(text)["stages"], variables


STAGES, VARS = load_dvc()


def entries(items) -> dict[str, dict]:
    """dvc.yaml list of `path` or `{path: options}` -> {path: options}."""
    return {k: v or {} for i in items for k, v in (i.items() if isinstance(i, dict) else [(i, {})])}


def task_of(stage: dict) -> str:
    return re.search(r"\btask=(\w+)", stage["cmd"]).group(1)


def module_file(name: str) -> Path | None:
    base = SRC / Path(*name.split("."))
    for p in (base.with_suffix(".py"), base / "__init__.py"):
        if p.exists():
            return p
    return None


def imported_modules(tree: ast.Module) -> set[str]:
    """tumordetector modules imported anywhere in a file (also inside functions), except type-only ones."""
    found = set()

    def visit(node):
        if isinstance(node, ast.If) and getattr(node.test, "id", None) == "TYPE_CHECKING":
            return
        if isinstance(node, ast.Import):
            found.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
            found.update(f"{node.module}.{a.name}" for a in node.names)   # `from pkg import module`
        for child in ast.iter_child_nodes(node):
            visit(child)

    visit(tree)
    return {m for m in found if m.split(".")[0] == "tumordetector" and module_file(m)}


def closure(task: str) -> set[Path]:
    todo, seen = [f"tumordetector.tasks.{task}"], set()
    while todo:
        path = module_file(todo.pop())
        if path in seen:
            continue
        seen.add(path)
        todo += imported_modules(ast.parse(path.read_text()))
    return {p for p in seen if p.stat().st_size > 0}   # empty package __init__ files carry no code


def used_code(task: str, files: set[Path]) -> list[ast.AST]:
    """Syntax trees the stage runs in the task modules (which hold the root config): all of its own
    module; of another task module only the functions and classes it imports, and those they call."""
    own = module_file(f"tumordetector.tasks.{task}")
    imported: dict[Path, set[str]] = {}
    for path in files:
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("tumordetector.tasks."):
                imported.setdefault(module_file(node.module), set()).update(a.name for a in node.names)
    trees = [ast.parse(own.read_text())]
    for path, names in imported.items():
        if path == own:
            continue
        defs = {n.name: n for n in ast.parse(path.read_text()).body
                if isinstance(n, ast.FunctionDef | ast.ClassDef)}
        todo, seen = [n for n in names if n in defs], set()
        while todo:
            if (name := todo.pop()) in seen:
                continue
            seen.add(name)
            todo += [n.id for n in ast.walk(defs[name]) if isinstance(n, ast.Name) and n.id in defs]
        trees += [defs[n] for n in seen]
    return trees


def config_reads(trees: list[ast.AST], cfg: DictConfig) -> set[str]:
    """Config leaves read through `cfg.a.b` (or `self.cfg.a.b`); a whole section read counts as all its leaves."""
    def chain(node):
        parts = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name) and node.id == "cfg":
            return parts[::-1]
        if parts and isinstance(node, ast.Name) and node.id == "self" and parts[-1] == "cfg":
            return parts[-2::-1]
        return None

    def leaves(node, prefix):
        if not isinstance(node, DictConfig):
            return {prefix}
        return {leaf for k in node for leaf in leaves(node[k], f"{prefix}.{k}" if prefix else k)}

    reads = set()
    for tree in trees:
        nodes = list(ast.walk(tree))
        inner = {id(n.value) for n in nodes if isinstance(n, ast.Attribute)}   # `cfg.a` inside `cfg.a.b`
        for node in nodes:
            if isinstance(node, ast.Attribute) and id(node) not in inner and (keys := chain(node)) is not None:
                value, used = cfg, []
                for k in keys:                 # stop at the first name that is not a key (.items(), ...)
                    if not isinstance(value, DictConfig) or k not in value:
                        break
                    value, used = value[k], [*used, k]
                if used:
                    reads |= leaves(value, ".".join(used))
    return reads


@pytest.fixture(scope="module")
def cfg():
    with initialize_config_dir(str(CONF_DIR), version_base=None):
        return compose("config", overrides=[f"backbone={VARS['backbone']}", "task=stream"])


def covered(key: str, prefixes) -> bool:
    return any(key == p or key.startswith(p + ".") for p in prefixes)


@pytest.mark.parametrize("name", sorted(STAGES))
def test_stage_depends_on_exactly_the_code_it_runs(name):
    stage = STAGES[name]
    code = closure(task_of(stage))
    deps = [ROOT / d for d in entries(stage["deps"]) if d.startswith("src/")]
    files = {f for d in deps for f in ([d] if d.is_file() else d.rglob("*.py")) if f.stat().st_size > 0}
    rel = lambda paths: sorted(str(p.relative_to(ROOT)) for p in paths)  # noqa: E731
    assert rel(code - files) == [], "code the stage runs but does not depend on"
    assert rel(files - code) == [], "code the stage depends on but does not run"


@pytest.mark.parametrize("name", sorted(STAGES))
def test_stage_params_are_the_config_it_reads(name, cfg):
    stage = STAGES[name]
    deps = entries(stage["deps"])
    params = set()
    for item in stage.get("params", []):
        for file, keys in item.items():
            prefix = ("data." if file == "conf/data/camelyon16.yaml"
                      else "head." if file.startswith("conf/head/") else "")
            params |= {prefix + k for k in keys}
    task = task_of(stage)
    reads = config_reads(used_code(task, closure(task)), cfg)
    by_file = {"backbone"} if f"conf/backbone/{VARS['backbone']}.yaml" in deps else set()
    by_file |= {"data.manifest"} if cfg.data.manifest in deps else set()
    missing = sorted(k for k in reads if not covered(k, params | by_file | set(UNTRACKED)))
    unused = sorted(p for p in params if not any(covered(k, [p]) for k in reads))
    assert missing == [], "config the stage reads but is not a param (or listed in UNTRACKED)"
    assert unused == [], "params the stage does not read"


def test_no_stage_deletes_what_it_cannot_rebuild():
    for name, stage in STAGES.items():
        assert task_of(stage) not in DEV_ONLY, f"{name}: task={task_of(stage)} is for local slides only"
        if name in REMOTE_INPUT:
            not_persist = [o for o, opt in entries(stage["outs"]).items() if not opt.get("persist")]
            assert not_persist == [], f"{name}: DVC would delete {not_persist} before rerunning"


def test_closure_follows_imports_inside_functions():
    files = {str(p.relative_to(SRC)) for p in closure("stream")}
    assert "tumordetector/data/camelyon16.py" in files            # imported inside download()
    assert "tumordetector/backbones/base.py" in files
    assert "tumordetector/backbones/base.py" not in {str(p.relative_to(SRC)) for p in closure("train")}


def test_dvc_ignores_files_that_change_without_the_code_changing():
    ignored = (ROOT / ".dvcignore").read_text().split()
    assert "__pycache__/" in ignored and "*.pyc" in ignored   # else every Python run changes the src deps
    assert "data/embeddings/*/extract_log.csv" in ignored      # else every stream run reruns index and baseline
