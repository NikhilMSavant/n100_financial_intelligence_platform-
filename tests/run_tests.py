"""
run_tests.py — pytest is unavailable in this offline sandbox (no pip network
access), so this is a tiny drop-in collector/runner for any test_*.py file
under tests/, executing every top-level function named test_*.
Usage: python3 tests/run_tests.py [tests/etl] [tests/kpi]
"""
import glob
import importlib.util
import os
import sys
import traceback

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load_module(path):
    spec = importlib.util.spec_from_file_location(os.path.basename(path)[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_dir(d):
    passed, failed, skipped = 0, 0, 0
    fails = []
    for path in sorted(glob.glob(os.path.join(d, "test_*.py"))):
        try:
            mod = load_module(path)
        except Exception as e:
            print(f"COLLECT ERROR {path}: {e}")
            failed += 1
            continue
        skip_marker = getattr(mod, "pytestmark", None)
        fixtures = {}
        for name in dir(mod):
            if name.startswith("test_"):
                fn = getattr(mod, name)
                try:
                    import inspect
                    params = inspect.signature(fn).parameters
                    args = []
                    for p in params:
                        if p not in fixtures:
                            fixture_fn = getattr(mod, p, None)
                            if fixture_fn is None:
                                raise RuntimeError(f"no fixture '{p}'")
                            gen = fixture_fn()
                            val = next(gen)
                            fixtures[p] = (gen, val)
                        args.append(fixtures[p][1])
                    fn(*args)
                    passed += 1
                except Exception as e:
                    failed += 1
                    fails.append((path, name, "".join(traceback.format_exception_only(type(e), e)).strip()))
        for gen, _ in fixtures.values():
            try:
                next(gen)
            except StopIteration:
                pass
    return passed, failed, fails


if __name__ == "__main__":
    dirs = sys.argv[1:] or ["tests/etl", "tests/kpi"]
    total_p = total_f = 0
    all_fails = []
    for d in dirs:
        p, f, fails = run_dir(os.path.join(ROOT, d))
        total_p += p
        total_f += f
        all_fails += fails
        print(f"{d}: {p} passed, {f} failed")
    print(f"\nTOTAL: {total_p} passed, {total_f} failed")
    for path, name, msg in all_fails:
        print(f"  FAIL {path}::{name} -> {msg}")
    sys.exit(1 if total_f else 0)
