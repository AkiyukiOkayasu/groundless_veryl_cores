#!/usr/bin/env python3
"""補間器ベンチマークCSVの統計量、正弦波誤差、周波数応答を計算する。"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path


SAMPLE_WIDTH = 32
SAMPLE_FRACTION_BITS = 31
DIFFERENCE_WIDTH = SAMPLE_WIDTH + 1
DEFAULT_IMPULSE_CASE = 4
SINE_SIGNAL_KIND = 2
REFERENCE_AMPLITUDE = (1 << SAMPLE_FRACTION_BITS) - 1
DEFAULT_FREQUENCIES = (0.0, 0.1, 0.2, 0.3, 0.4, 0.45, 0.49)
REQUIRED_COLUMNS = {
    "case",
    "signal_kind",
    "frequency_milli_fs",
    "sample_index",
    "phase",
    "sample0_bits",
    "sample1_bits",
    "zero_order_hold_bits",
    "linear_bits",
    "difference_bits",
}


def decode_twos_complement(value: str, width: int) -> int:
    """16進数で出力された符号付き固定幅値を整数へ戻す。"""
    raw = int(value, 16)
    mask = (1 << width) - 1
    if raw & ~mask:
        raise ValueError(f"値 {value!r} は{width}bitに収まらない")
    if raw & (1 << (width - 1)):
        return raw - (1 << width)
    return raw


def read_rows(path: Path) -> list[dict[str, int]]:
    """Veryl Native testのCSVを読み、固定小数点値を符号付き整数へ変換する。"""
    rows: list[dict[str, int]] = []
    with path.open(newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        columns = set(reader.fieldnames or ())
        missing = REQUIRED_COLUMNS - columns
        if missing:
            names = ", ".join(sorted(missing))
            raise ValueError(f"CSVの列が不足している: {names}")

        for line_number, row in enumerate(reader, start=2):
            try:
                parsed = {
                    "case": int(row["case"]),
                    "signal_kind": int(row["signal_kind"]),
                    "frequency_milli_fs": int(row["frequency_milli_fs"]),
                    "sample_index": int(row["sample_index"]),
                    "phase": int(row["phase"]),
                    "sample0": decode_twos_complement(row["sample0_bits"], SAMPLE_WIDTH),
                    "sample1": decode_twos_complement(row["sample1_bits"], SAMPLE_WIDTH),
                    "hold": decode_twos_complement(
                        row["zero_order_hold_bits"], SAMPLE_WIDTH
                    ),
                    "linear": decode_twos_complement(row["linear_bits"], SAMPLE_WIDTH),
                    "difference": decode_twos_complement(
                        row["difference_bits"], DIFFERENCE_WIDTH
                    ),
                }
                if parsed["difference"] != parsed["linear"] - parsed["hold"]:
                    raise ValueError("difference_bitsがlinear_bits - zero_order_hold_bitsと不一致")
                rows.append(parsed)
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(f"CSV {line_number}行目を解釈できない: {error}") from error

    if not rows:
        raise ValueError("CSVにデータ行がない")
    return rows


def group_rows(rows: list[dict[str, int]]) -> tuple[dict[int, list[dict[str, int]]], int]:
    """caseごとに並べ替え、phase列の欠落や重複を検証する。"""
    grouped: dict[int, list[dict[str, int]]] = defaultdict(list)
    for row in rows:
        grouped[row["case"]].append(row)

    phase_steps: int | None = None
    for case, case_rows in grouped.items():
        phases = sorted({row["phase"] for row in case_rows})
        if not phases or phases != list(range(phases[-1] + 1)):
            raise ValueError(f"case {case} のphase列が0から連続していない")
        if phase_steps is None:
            phase_steps = phases[-1] + 1
        elif phase_steps != phases[-1] + 1:
            raise ValueError("caseごとにphase数が異なる")

        seen = {(row["sample_index"], row["phase"]) for row in case_rows}
        if len(seen) != len(case_rows):
            raise ValueError(f"case {case} に重複したsample_index/phaseがある")
        kinds = {row["signal_kind"] for row in case_rows}
        frequencies = {row["frequency_milli_fs"] for row in case_rows}
        if len(kinds) != 1 or len(frequencies) != 1:
            raise ValueError(f"case {case} の信号種別または周波数が途中で変化している")
        if next(iter(kinds)) == SINE_SIGNAL_KIND and next(iter(frequencies)) <= 0:
            raise ValueError(f"case {case} の正弦波周波数が0以下")
        case_rows.sort(key=lambda row: (row["sample_index"], row["phase"]))

    assert phase_steps is not None
    return dict(sorted(grouped.items())), phase_steps


def rms(values: list[int]) -> float:
    return math.sqrt(sum(value * value for value in values) / len(values))


def difference_summary(case: int, rows: list[dict[str, int]]) -> dict[str, int | float]:
    """0次ホールドとの差をLSBとQ1.31の両方で集計する。"""
    differences = [row["difference"] for row in rows]
    absolute = [abs(value) for value in differences]
    scale = 1 << SAMPLE_FRACTION_BITS
    return {
        "case": case,
        "signal_kind": rows[0]["signal_kind"],
        "frequency_milli_fs": rows[0]["frequency_milli_fs"],
        "rows": len(rows),
        "max_abs_difference_lsb": max(absolute),
        "mean_abs_difference_lsb": sum(absolute) / len(absolute),
        "rms_difference_lsb": rms(differences),
        "max_abs_difference_q1_31": max(absolute) / scale,
        "rms_difference_q1_31": rms(differences) / scale,
    }


def sine_projection(
    values: list[int], rows: list[dict[str, int]], frequency: float, phase_steps: int
) -> tuple[float, float, float]:
    """正弦波への射影から振幅、ゲイン、位相を求める。"""
    cosine_projection = 0.0
    sine_projection_value = 0.0
    for value, row in zip(values, rows):
        time = row["sample_index"] + row["phase"] / phase_steps
        angle = 2.0 * math.pi * frequency * time
        cosine_projection += value * math.cos(angle)
        sine_projection_value += value * math.sin(angle)

    amplitude = 2.0 / len(values) * math.hypot(cosine_projection, sine_projection_value)
    gain = amplitude / REFERENCE_AMPLITUDE
    phase = math.degrees(math.atan2(cosine_projection, sine_projection_value))
    return amplitude, gain, phase


def sine_summary(case: int, rows: list[dict[str, int]], phase_steps: int) -> dict[str, object]:
    """正弦波を理想的な連続正弦波と比較する。"""
    frequency = rows[0]["frequency_milli_fs"] / 1000.0
    result: dict[str, object] = {
        "case": case,
        "frequency_fs": frequency,
        "rows": len(rows),
    }

    for name in ("hold", "linear"):
        values = [row[name] for row in rows]
        expected = [
            int(
                REFERENCE_AMPLITUDE
                * math.sin(
                    2.0
                    * math.pi
                    * frequency
                    * (row["sample_index"] + row["phase"] / phase_steps)
                )
            )
            for row in rows
        ]
        errors = [value - reference for value, reference in zip(values, expected)]
        amplitude, gain, phase = sine_projection(values, rows, frequency, phase_steps)
        result[name] = {
            "max_abs_error_lsb": max(abs(error) for error in errors),
            "mean_abs_error_lsb": sum(abs(error) for error in errors) / len(errors),
            "rms_error_lsb": rms(errors),
            "rms_error_q1_31": rms(errors) / (1 << SAMPLE_FRACTION_BITS),
            "projected_amplitude_lsb": amplitude,
            "projected_gain": gain,
            "projected_phase_deg": phase,
        }
    return result


def dft_magnitude(values: list[int], frequency: float, phase_steps: int) -> float:
    """入力サンプルレート基準の周波数で、インパルス列のDFT振幅を求める。"""
    if frequency == 0.0:
        return abs(float(sum(values)))

    angle_step = 2.0 * math.pi * frequency / phase_steps
    real = 0.0
    imag = 0.0
    for index, value in enumerate(values):
        angle = angle_step * index
        real += value * math.cos(angle)
        imag -= value * math.sin(angle)
    return math.hypot(real, imag)


def response_db(magnitude: float, dc_magnitude: float) -> float | None:
    if magnitude == 0.0 or dc_magnitude == 0.0:
        return None
    return 20.0 * math.log10(magnitude / dc_magnitude)


def impulse_summary(
    case: int,
    rows: list[dict[str, int]],
    phase_steps: int,
    frequencies: tuple[float, ...],
) -> dict[str, object]:
    """インパルス列のDCゲイン、ピーク、周波数特性を比較する。"""
    impulse_amplitude = max(abs(row["sample0"]) for row in rows)
    if impulse_amplitude == 0:
        raise ValueError("インパルスcaseの入力振幅が0")
    implementations: dict[str, object] = {}
    responses: dict[str, dict[str, float | None]] = {}

    for name in ("hold", "linear"):
        values = [row[name] for row in rows]
        dc_magnitude = dft_magnitude(values, 0.0, phase_steps)
        implementations[name] = {
            "rows": len(values),
            "dc_gain_relative_to_input": sum(values) / impulse_amplitude,
            "peak_abs_lsb": max(abs(value) for value in values),
            "rms_lsb": rms(values),
        }
        responses[name] = {
            f"{frequency:.2f}": response_db(
                dft_magnitude(values, frequency, phase_steps), dc_magnitude
            )
            for frequency in frequencies
        }

    return {
        "case": case,
        "phase_steps": phase_steps,
        "input_amplitude_lsb": impulse_amplitude,
        "implementations": implementations,
        "frequency_response_db_relative_to_dc": responses,
    }


def analyze(
    path: Path, impulse_case: int, frequencies: tuple[float, ...]
) -> dict[str, object]:
    rows = read_rows(path)
    grouped, phase_steps = group_rows(rows)
    summaries = [difference_summary(case, case_rows) for case, case_rows in grouped.items()]
    result: dict[str, object] = {
        "csv": str(path),
        "phase_steps": phase_steps,
        "difference_summary": summaries,
    }

    sine_cases = {
        case: case_rows
        for case, case_rows in grouped.items()
        if case_rows[0]["signal_kind"] == SINE_SIGNAL_KIND
    }
    if sine_cases:
        result["sine_summary"] = [
            sine_summary(case, case_rows, phase_steps)
            for case, case_rows in sine_cases.items()
        ]

    impulse_rows = grouped.get(impulse_case)
    if impulse_rows is not None:
        result["impulse_summary"] = impulse_summary(
            impulse_case, impulse_rows, phase_steps, frequencies
        )
    return result


def print_text(result: dict[str, object]) -> None:
    print(f"CSV: {result['csv']}")
    print(f"phase steps: {result['phase_steps']}")
    print("\nDifference from zero-order hold:")
    print("case kind freq_milli_fs rows max_abs_lsb mean_abs_lsb rms_lsb max_abs_q1.31 rms_q1.31")
    for summary in result["difference_summary"]:  # type: ignore[union-attr]
        print(
            f"{summary['case']} {summary['signal_kind']} {summary['frequency_milli_fs']} "
            f"{summary['rows']} "
            f"{summary['max_abs_difference_lsb']} "
            f"{summary['mean_abs_difference_lsb']:.3f} "
            f"{summary['rms_difference_lsb']:.3f} "
            f"{summary['max_abs_difference_q1_31']:.9f} "
            f"{summary['rms_difference_q1_31']:.9f}"
        )

    sine = result.get("sine_summary")
    if sine is not None:
        print("\nSine wave error against an ideal continuous sine:")
        print(
            "case frequency_fs rows implementation max_abs_error_lsb "
            "mean_abs_error_lsb rms_error_lsb projected_gain projected_phase_deg"
        )
        for summary in sine:  # type: ignore[union-attr]
            for name in ("hold", "linear"):
                implementation = summary[name]
                print(
                    f"{summary['case']} {summary['frequency_fs']:.3f} {summary['rows']} "
                    f"{name} {implementation['max_abs_error_lsb']} "
                    f"{implementation['mean_abs_error_lsb']:.3f} "
                    f"{implementation['rms_error_lsb']:.3f} "
                    f"{implementation['projected_gain']:.9f} "
                    f"{implementation['projected_phase_deg']:.6f}"
                )

    impulse = result.get("impulse_summary")
    if impulse is None:
        return

    print("\nImpulse response:")
    print("implementation rows dc_gain_relative_to_input peak_abs_lsb rms_lsb")
    for name, summary in impulse["implementations"].items():  # type: ignore[union-attr]
        print(
            f"{name} {summary['rows']} "
            f"{summary['dc_gain_relative_to_input']:.9f} "
            f"{summary['peak_abs_lsb']} {summary['rms_lsb']:.3f}"
        )

    print("\nImpulse frequency response, dB relative to each implementation's DC:")
    print("frequency_input_fs hold_db linear_db linear_minus_hold_db")
    hold_response = impulse["frequency_response_db_relative_to_dc"]["hold"]  # type: ignore[index]
    linear_response = impulse["frequency_response_db_relative_to_dc"]["linear"]  # type: ignore[index]
    for frequency in hold_response:
        hold_db = hold_response[frequency]
        linear_db = linear_response[frequency]
        delta = None if hold_db is None or linear_db is None else linear_db - hold_db
        print(
            f"{frequency} "
            f"{hold_db if hold_db is not None else 'n/a'} "
            f"{linear_db if linear_db is not None else 'n/a'} "
            f"{delta if delta is not None else 'n/a'}"
        )


def parse_frequencies(value: str) -> tuple[float, ...]:
    try:
        frequencies = tuple(float(item) for item in value.split(","))
    except ValueError as error:
        raise argparse.ArgumentTypeError("周波数はカンマ区切りの数値で指定する") from error
    if any(frequency < 0.0 or frequency >= 0.5 for frequency in frequencies):
        raise argparse.ArgumentTypeError("周波数は入力サンプルレートの0以上0.5未満で指定する")
    return frequencies


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "csv_path",
        nargs="?",
        type=Path,
        default=Path("target/interpolator_benchmark.csv"),
        help="Veryl Native testが生成したCSV",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="出力形式。jsonは機械処理向け",
    )
    parser.add_argument(
        "--impulse-case",
        type=int,
        default=DEFAULT_IMPULSE_CASE,
        help="インパルス応答として解析するcase番号",
    )
    parser.add_argument(
        "--frequencies",
        type=parse_frequencies,
        default=DEFAULT_FREQUENCIES,
        help="入力サンプルレート基準の周波数をカンマ区切りで指定する",
    )
    args = parser.parse_args()

    try:
        result = analyze(args.csv_path, args.impulse_case, args.frequencies)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_text(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
