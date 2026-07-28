#!/usr/bin/env python3
"""固定48kHz/50MHz ASRC比較CSVの正弦波振幅を解析する。"""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path


CLOCK_HZ = 50_000_000.0
SAMPLE_WIDTH = 32
FULL_SCALE = (1 << (SAMPLE_WIDTH - 1)) - 1
TONE_HZ = {
    0: 1_000.0,
    1: 10_000.0,
    2: 18_000.0,
    3: 20_000.0,
}
REQUIRED_COLUMNS = {
    "case",
    "cycle",
    "direct_active",
    "direct_sample_bits",
    "four_active",
    "four_sample_bits",
    "direct_underflow",
    "four_underflow",
}


def decode_twos_complement(value: str, width: int) -> int:
    """Verylが16進数で書いた固定幅の符号付き値を復号する。"""
    raw = int(value, 16)
    mask = (1 << width) - 1
    if raw & ~mask:
        raise ValueError(f"値 {value!r} は{width}bitに収まらない")
    if raw & (1 << (width - 1)):
        return raw - (1 << width)
    return raw


def read_rows(path: Path) -> list[dict[str, int]]:
    """CSVを読み、サンプルを符号付き整数へ変換する。"""
    rows: list[dict[str, int]] = []
    with path.open(newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        columns = set(reader.fieldnames or ())
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError(f"CSVの列が不足している: {', '.join(sorted(missing))}")

        for line_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    {
                        "case": int(row["case"]),
                        "cycle": int(row["cycle"]),
                        "direct_active": int(row["direct_active"]),
                        "direct": decode_twos_complement(
                            row["direct_sample_bits"], SAMPLE_WIDTH
                        ),
                        "four_active": int(row["four_active"]),
                        "four": decode_twos_complement(
                            row["four_sample_bits"], SAMPLE_WIDTH
                        ),
                        "direct_underflow": int(row["direct_underflow"]),
                        "four_underflow": int(row["four_underflow"]),
                    }
                )
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(f"CSV {line_number}行目を解釈できない: {error}") from error

    if not rows:
        raise ValueError("CSVにデータ行がない")
    return rows


def solve_3x3(matrix: list[list[float]], vector: list[float]) -> list[float]:
    """ガウス消去で3元連立方程式を解く。"""
    augmented = [row[:] + [value] for row, value in zip(matrix, vector)]
    for pivot in range(3):
        pivot_row = max(range(pivot, 3), key=lambda row: abs(augmented[row][pivot]))
        if abs(augmented[pivot_row][pivot]) < 1.0e-18:
            raise ValueError("正弦波回帰の行列が特異")
        augmented[pivot], augmented[pivot_row] = augmented[pivot_row], augmented[pivot]
        divisor = augmented[pivot][pivot]
        augmented[pivot] = [value / divisor for value in augmented[pivot]]
        for row in range(3):
            if row == pivot:
                continue
            factor = augmented[row][pivot]
            augmented[row] = [
                left - factor * right
                for left, right in zip(augmented[row], augmented[pivot])
            ]
    return [augmented[index][3] for index in range(3)]


def fit_sine(rows: list[dict[str, int]], signal: str, frequency_hz: float) -> dict[str, float | int]:
    """既知周波数の正弦波へDCを含む最小二乗フィットを行う。"""
    selected = [row for row in rows if row[f"{signal}_active"]]
    if not selected:
        raise ValueError(f"case {rows[0]['case']} の{signal}に有効な出力がない")

    matrix = [[0.0] * 3 for _ in range(3)]
    vector = [0.0] * 3
    samples: list[tuple[float, float]] = []
    for row in selected:
        angle = 2.0 * math.pi * frequency_hz * row["cycle"] / CLOCK_HZ
        basis = [1.0, math.sin(angle), math.cos(angle)]
        value = float(row[signal])
        samples.append((value, angle))
        for left in range(3):
            vector[left] += basis[left] * value
            for right in range(3):
                matrix[left][right] += basis[left] * basis[right]

    offset, sine_coefficient, cosine_coefficient = solve_3x3(matrix, vector)
    amplitude = math.hypot(sine_coefficient, cosine_coefficient)
    residual_sum = 0.0
    for value, angle in samples:
        estimate = (
            offset
            + sine_coefficient * math.sin(angle)
            + cosine_coefficient * math.cos(angle)
        )
        residual_sum += (value - estimate) ** 2

    return {
        "rows": len(selected),
        "offset_lsb": offset,
        "amplitude_lsb": amplitude,
        "amplitude_dbfs": 20.0 * math.log10(amplitude / FULL_SCALE),
        "rms_error_lsb": math.sqrt(residual_sum / len(samples)),
    }


def analyze(path: Path, discard_cycles: int) -> list[dict[str, object]]:
    rows = read_rows(path)
    grouped: dict[int, list[dict[str, int]]] = defaultdict(list)
    for row in rows:
        grouped[row["case"]].append(row)

    summaries: list[dict[str, object]] = []
    for case, case_rows in sorted(grouped.items()):
        usable = [row for row in case_rows if row["cycle"] >= discard_cycles]
        frequency_hz = TONE_HZ.get(case)
        if frequency_hz is None:
            raise ValueError(f"未定義のcase番号: {case}")
        summary: dict[str, object] = {
            "case": case,
            "frequency_hz": frequency_hz,
            "discard_cycles": discard_cycles,
            "underflow": {
                "direct": max(row["direct_underflow"] for row in case_rows),
                "four_x_hbf": max(row["four_underflow"] for row in case_rows),
            },
        }
        direct_result = fit_sine(usable, "direct", frequency_hz)
        four_result = fit_sine(usable, "four", frequency_hz)
        summary["direct"] = direct_result
        summary["four_x_hbf"] = four_result
        direct_amplitude = direct_result["amplitude_lsb"]
        four_amplitude = four_result["amplitude_lsb"]
        summary["four_minus_direct_gain_db"] = 20.0 * math.log10(
            four_amplitude / direct_amplitude
        )
        summaries.append(summary)
    return summaries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "csv_path",
        nargs="?",
        type=Path,
        default=Path("target/fixed_rate_asrc_benchmark.csv"),
    )
    parser.add_argument(
        "--discard-cycles",
        type=int,
        default=100_000,
        help="起動過渡を除外する50MHzクロック数（既定: %(default)s）",
    )
    args = parser.parse_args()
    if args.discard_cycles < 0:
        parser.error("--discard-cyclesは0以上で指定する")

    print(f"csv={args.csv_path}")
    for summary in analyze(args.csv_path, args.discard_cycles):
        print(
            f"case={summary['case']} frequency_hz={summary['frequency_hz']:.0f} "
            f"underflow={summary['underflow']} "
            f"four_minus_direct_gain_db={summary['four_minus_direct_gain_db']:.6f}"
        )
        for label in ("direct", "four_x_hbf"):
            result = summary[label]
            print(
                f"  {label}: rows={result['rows']} "
                f"amplitude_dbfs={result['amplitude_dbfs']:.6f} "
                f"rms_error_lsb={result['rms_error_lsb']:.3f}"
            )


if __name__ == "__main__":
    main()
