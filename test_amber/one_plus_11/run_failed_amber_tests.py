#!/usr/bin/env python3

import argparse
import csv
import html
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


PASS_MARKER = "1 pass"
FAIL_MARKER = "Buffers have different values."


@dataclass
class TestResult:
    name: str
    simple_status: str
    verbose_status: str
    raw_output: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run extracted failed Amber tests and generate rerun reports."
    )
    parser.add_argument(
        "input_dir",
        nargs="?",
        help="Relative path to the extracted failed test directory. Defaults to the newest failed_tests_extracted_* directory next to this script.",
    )
    parser.add_argument(
        "--output-dir",
        help="Relative path for rerun reports. Defaults to rerun_results/<input-dir>-<timestamp>.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="How many times to run each Amber test. Default: 1.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="Per-iteration timeout in seconds. Default: 15.",
    )
    parser.add_argument(
        "--android",
        action="store_true",
        help="Run via adb on Android using /data/local/tmp/amber_ndk.",
    )
    parser.add_argument(
        "--serial",
        help="adb serial to use when --android is set.",
    )
    parser.add_argument(
        "--device",
        help="Vulkan device ID to pass to Amber with -D.",
    )
    parser.add_argument(
        "--amber-binary",
        default="amber",
        help="Host Amber binary to use when not running on Android. Default: amber.",
    )
    parser.add_argument(
        "--target-env",
        default="spv1.5",
        help="Amber target environment for -t. Default: spv1.5.",
    )
    return parser.parse_args()


def sort_test_name(name: str) -> tuple:
    if name == "reference":
        return (-1, name)
    if name.startswith("variant_"):
        suffix = name.split("_", 1)[1]
        try:
            return (0, int(suffix))
        except ValueError:
            return (0, suffix)
    return (1, name)


def find_default_input_dir(script_dir: Path) -> Path:
    candidates = sorted(
        [
            path
            for path in script_dir.iterdir()
            if path.is_dir() and path.name.startswith("failed_tests_extracted_")
        ]
    )
    if not candidates:
        raise FileNotFoundError(
            "No failed_tests_extracted_* directory found next to the script."
        )
    return candidates[-1]


def resolve_input_dir(script_dir: Path, input_dir_arg: str | None) -> Path:
    if input_dir_arg:
        input_dir = script_dir / input_dir_arg
    else:
        input_dir = find_default_input_dir(script_dir)
    if not input_dir.is_dir():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    return input_dir


def resolve_output_dir(script_dir: Path, input_dir: Path, output_dir_arg: str | None) -> Path:
    if output_dir_arg:
        return script_dir / output_dir_arg
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return script_dir / "rerun_results" / f"{input_dir.name}-{timestamp}"


def ensure_host_amber(binary: str) -> None:
    if shutil.which(binary) is None:
        raise FileNotFoundError(f"Amber binary not found in PATH: {binary}")


def ensure_android_ready(serial: str | None) -> None:
    adb_base = ["adb"]
    if serial:
        adb_base.extend(["-s", serial])

    try:
        subprocess.run(
            adb_base + ["shell", "true"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception as exc:
        raise RuntimeError("adb device check failed") from exc

    try:
        subprocess.run(
            adb_base + ["shell", "test -f /data/local/tmp/amber_ndk"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception as exc:
        raise RuntimeError(
            "amber_ndk was not found at /data/local/tmp/amber_ndk on the Android device"
        ) from exc


def log_print(handle, message: str) -> None:
    handle.write(message + "\n")
    print(message)


def build_host_command(args: argparse.Namespace, amber_file: Path) -> list[str]:
    command = [args.amber_binary, "-d", "-t", args.target_env]
    if args.device:
        command.extend(["-D", args.device])
    command.append(amber_file.name)
    return command


def build_android_command(args: argparse.Namespace, amber_file: Path) -> list[str]:
    adb_base = ["adb"]
    if args.serial:
        adb_base.extend(["-s", args.serial])

    shell_command = f"cd /data/local/tmp ; ./amber_ndk -d -t {args.target_env}"
    if args.device:
        shell_command += f" -D {args.device}"
    shell_command += f" {amber_file.name}"
    return adb_base + ["shell", shell_command]


def push_android_file(args: argparse.Namespace, amber_file: Path) -> None:
    adb_base = ["adb"]
    if args.serial:
        adb_base.extend(["-s", args.serial])
    subprocess.run(
        adb_base + ["push", str(amber_file), "/data/local/tmp/"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )


def remove_android_file(args: argparse.Namespace, amber_file: Path) -> None:
    adb_base = ["adb"]
    if args.serial:
        adb_base.extend(["-s", args.serial])
    subprocess.run(
        adb_base + ["shell", f"rm -f /data/local/tmp/{amber_file.name}"],
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )


def run_single_iteration(
    args: argparse.Namespace,
    amber_file: Path,
) -> tuple[str, str]:
    if args.android:
        command = build_android_command(args, amber_file)
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=args.timeout,
        )
    else:
        command = build_host_command(args, amber_file)
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=args.timeout,
            cwd=amber_file.parent,
        )
    output = result.stdout + result.stderr
    command_string = " ".join(command)
    return command_string, output


def run_test(args: argparse.Namespace, amber_file: Path, log_handle) -> TestResult:
    if args.android:
        push_android_file(args, amber_file)

    command_string = ""
    outputs: list[str] = []
    failure_count = 0
    pass_count = 0

    try:
        for iteration in range(args.iterations):
            command_string, output = run_single_iteration(args, amber_file)
            outputs.append(output)
            log_print(log_handle, f"running test: {amber_file.name} (iteration {iteration + 1}/{args.iterations})")
            log_print(log_handle, command_string)

            failure_count += output.count(FAIL_MARKER)
            pass_count += output.count(PASS_MARKER)

        raw_output = "\n".join(outputs).strip()

        if failure_count == 0 and pass_count == 0:
            log_print(log_handle, "I (ignored error)")
            if raw_output:
                log_print(log_handle, "--- Ignored error output ---")
                log_print(log_handle, raw_output)
                log_print(log_handle, "----------------------------")
            return TestResult(
                name=amber_file.stem,
                simple_status="I",
                verbose_status="I",
                raw_output=raw_output,
            )

        if failure_count > 0:
            log_print(log_handle, "F")
            if raw_output:
                log_print(log_handle, "--- Error output ---")
                log_print(log_handle, raw_output)
                log_print(log_handle, "--------------------")
            return TestResult(
                name=amber_file.stem,
                simple_status="F",
                verbose_status=f"F ({failure_count}/{args.iterations})",
                raw_output=raw_output,
            )

        log_print(log_handle, "P")
        return TestResult(
            name=amber_file.stem,
            simple_status="P",
            verbose_status="P",
            raw_output=raw_output,
        )
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or "") + (exc.stderr or "")
        log_print(log_handle, "I (ignored error)")
        log_print(log_handle, "--- Ignored error output ---")
        log_print(log_handle, f"Command timed out after {args.timeout} seconds.")
        if output.strip():
            log_print(log_handle, output.strip())
        log_print(log_handle, "----------------------------")
        return TestResult(
            name=amber_file.stem,
            simple_status="I",
            verbose_status="I",
            raw_output=output.strip(),
        )
    finally:
        if args.android:
            remove_android_file(args, amber_file)
        log_print(log_handle, "")


def ascii_table(headers: list[str], rows: list[list[str]]) -> str:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(str(cell)))

    def format_row(row: list[str]) -> str:
        return "| " + " | ".join(str(cell).ljust(widths[index]) for index, cell in enumerate(row)) + " |"

    separator = "+-" + "-+-".join("-" * width for width in widths) + "-+"
    lines = [separator, format_row(headers), separator]
    lines.extend(format_row(row) for row in rows)
    lines.append(separator)
    return "\n".join(lines) + "\n"


def write_csv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def write_html(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    lines = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "<style>",
        "table, th, td { border: 1px solid black; border-collapse: collapse; }",
        "th, td { padding: 6px 10px; font-family: monospace; }",
        ".status-P { background: #009900; color: white; }",
        ".status-F { background: #cc0000; color: white; }",
        ".status-I { background: #b8860b; color: white; }",
        "</style>",
        "</head>",
        "<body>",
        "<h1>Amber Rerun Results</h1>",
        "<table>",
        "<tr>" + "".join(f"<th>{html.escape(header)}</th>" for header in headers) + "</tr>",
    ]

    for row in rows:
        rendered = []
        for cell in row:
            cell_text = str(cell)
            css_class = ""
            if cell_text in {"P", "F", "I"}:
                css_class = f' class="status-{cell_text}"'
            rendered.append(f"<td{css_class}>{html.escape(cell_text)}</td>")
        lines.append("<tr>" + "".join(rendered) + "</tr>")

    lines.extend(["</table>", "</body>", "</html>"])
    path.write_text("\n".join(lines) + "\n")


def suite_rows(results: list[TestResult], verbose: bool) -> list[list[str]]:
    rows = []
    failure_total = 0
    for result in results:
        status = result.verbose_status if verbose else result.simple_status
        rows.append([result.name, status])
        if result.simple_status == "F":
            failure_total += 1
    rows.append(["Total failures:", str(failure_total)])
    return rows


def write_suite_reports(suite_output_dir: Path, results: list[TestResult], date_stamp: str) -> tuple[int, int, int]:
    headers = ["Test File Name", "All Passed"]

    simple_rows = suite_rows(results, verbose=False)
    verbose_rows = suite_rows(results, verbose=True)

    write_csv(suite_output_dir / f"simple_final_results-{date_stamp}.csv", headers, simple_rows)
    write_csv(
        suite_output_dir / f"iteration_based_final_results-{date_stamp}.csv",
        headers,
        verbose_rows,
    )

    (suite_output_dir / f"simple_final_results-{date_stamp}.txt").write_text(
        ascii_table(headers, simple_rows)
    )
    (suite_output_dir / f"iteration_based_final_results-{date_stamp}.txt").write_text(
        ascii_table(headers, verbose_rows)
    )
    write_html(suite_output_dir / f"html-colored-table{date_stamp}.html", headers, simple_rows)

    passed = sum(1 for result in results if result.simple_status == "P")
    failed = sum(1 for result in results if result.simple_status == "F")
    ignored = sum(1 for result in results if result.simple_status == "I")
    return passed, failed, ignored


def write_summary(output_dir: Path, summary_rows: list[list[str]]) -> None:
    headers = ["Suite", "Tests", "Passes", "Fails", "Ignored"]
    write_csv(output_dir / "summary.csv", headers, summary_rows)
    (output_dir / "summary.txt").write_text(ascii_table(headers, summary_rows))


def run_suite(args: argparse.Namespace, suite_dir: Path, suite_output_dir: Path, date_stamp: str) -> list[str]:
    suite_output_dir.mkdir(parents=True, exist_ok=True)
    log_path = suite_output_dir / "output_log.txt"

    amber_files = sorted(suite_dir.glob("*.amber"), key=lambda path: sort_test_name(path.stem))
    results: list[TestResult] = []

    with log_path.open("w") as log_handle:
        log_print(log_handle, "Date and Time:")
        log_print(log_handle, datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        log_print(log_handle, "Computer:")
        log_print(log_handle, socket.gethostname())
        log_print(log_handle, "")
        if args.android:
            log_print(log_handle, "No vulkaninfo on Android")
        else:
            vulkaninfo_path = suite_output_dir / "vulkaninfo.txt"
            if shutil.which("vulkaninfo") is None:
                log_print(log_handle, "vulkaninfo not found; skipping host Vulkan info capture")
            else:
                log_print(log_handle, f"storing vulkaninfo to: {vulkaninfo_path.name}")
                log_print(log_handle, "")
                with vulkaninfo_path.open("w") as handle:
                    subprocess.run(
                        ["vulkaninfo"],
                        check=False,
                        stdout=handle,
                        stderr=subprocess.STDOUT,
                        text=True,
                    )

        if not amber_files:
            log_print(log_handle, "No .amber files found in this suite.")
            log_print(log_handle, "")
        else:
            for amber_file in amber_files:
                results.append(run_test(args, amber_file, log_handle))

    passed, failed, ignored = write_suite_reports(suite_output_dir, results, date_stamp)
    return [suite_dir.name, str(len(results)), str(passed), str(failed), str(ignored)]


def main() -> int:
    args = parse_args()
    if args.iterations < 1:
        print("--iterations must be at least 1", file=sys.stderr)
        return 2

    script_dir = Path(__file__).resolve().parent

    try:
        input_dir = resolve_input_dir(script_dir, args.input_dir)
        output_dir = resolve_output_dir(script_dir, input_dir, args.output_dir)

        if args.android:
            ensure_android_ready(args.serial)
        else:
            ensure_host_amber(args.amber_binary)

        output_dir.mkdir(parents=True, exist_ok=True)
        date_stamp = datetime.now().strftime("%Y-%m-%d")

        suite_dirs = sorted([path for path in input_dir.iterdir() if path.is_dir()])
        if not suite_dirs:
            raise FileNotFoundError(f"No suite directories found in {input_dir}")

        summary_rows = []
        for suite_dir in suite_dirs:
            suite_output_dir = output_dir / suite_dir.name
            summary_rows.append(run_suite(args, suite_dir, suite_output_dir, date_stamp))

        write_summary(output_dir, summary_rows)

        total_tests = sum(int(row[1]) for row in summary_rows)
        total_fails = sum(int(row[3]) for row in summary_rows)
        print("")
        print(f"Input directory: {input_dir.relative_to(script_dir)}")
        print(f"Report directory: {output_dir.relative_to(script_dir)}")
        print(f"Rerun summary: {total_fails} failures out of {total_tests} tests")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
