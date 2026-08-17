"""Minimal test runner: discovers test_*.py files under tests/, imports them,
and runs every top-level function named test_*. Used because pytest cannot be
installed in this offline sandbox. Produces reports/pytest_report.html in a
similar spirit to pytest's --html report.
"""
import importlib.util
import pathlib
import sys
import time
import traceback

ROOT = pathlib.Path(__file__).resolve().parent.parent


def discover_and_run(test_dirs):
    results = []
    t_start = time.time()
    for d in test_dirs:
        for path in sorted((ROOT / d).glob("test_*.py")):
            modname = f"{d.replace('/', '_')}_{path.stem}"
            spec = importlib.util.spec_from_file_location(modname, path)
            mod = importlib.util.module_from_spec(spec)
            sys.path.insert(0, str(ROOT))
            try:
                spec.loader.exec_module(mod)
            except Exception as e:
                results.append((str(path), "<module load>", "ERROR", str(e)))
                continue
            for name in dir(mod):
                if name.startswith("test_") and callable(getattr(mod, name)):
                    fn = getattr(mod, name)
                    try:
                        fn()
                        results.append((str(path), name, "PASS", ""))
                    except AssertionError as e:
                        results.append((str(path), name, "FAIL", str(e)))
                    except Exception as e:
                        results.append((str(path), name, "ERROR", "".join(traceback.format_exception_only(type(e), e))))
    runtime = time.time() - t_start
    return results, runtime


def write_html_report(results, runtime, out_path):
    n_pass = sum(1 for r in results if r[2] == "PASS")
    n_fail = sum(1 for r in results if r[2] in ("FAIL", "ERROR"))
    rows = "\n".join(
        f"<tr style='background:{'#e6ffe6' if r[2]=='PASS' else '#ffe6e6'}'>"
        f"<td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td></tr>"
        for r in results
    )
    html = f"""<html><head><title>Test Report</title></head><body>
    <h2>Nifty 100 Platform — Test Report</h2>
    <p>Collected: {len(results)} | Passed: {n_pass} | Failed/Errors: {n_fail} | Runtime: {runtime:.2f}s</p>
    <table border=1 cellpadding=4 cellspacing=0>
    <tr><th>File</th><th>Test</th><th>Result</th><th>Detail</th></tr>
    {rows}
    </table></body></html>"""
    pathlib.Path(out_path).write_text(html)
    return n_pass, n_fail


if __name__ == "__main__":
    test_dirs = sys.argv[1:] if len(sys.argv) > 1 else ["tests/etl", "tests/kpi", "tests/dq", "tests/api"]
    results, runtime = discover_and_run(test_dirs)
    n_pass, n_fail = write_html_report(results, runtime, "reports/pytest_report.html")
    print(f"Collected {len(results)} tests in {runtime:.2f}s")
    print(f"PASSED: {n_pass}  FAILED/ERROR: {n_fail}")
    for r in results:
        if r[2] != "PASS":
            print(f"  {r[2]}: {r[0]}::{r[1]} -> {r[3]}")
    sys.exit(0 if n_fail == 0 else 1)
