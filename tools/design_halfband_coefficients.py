#!/usr/bin/env python3
"""設計・量子化後の2倍halfband FIR係数を評価する。

外部パッケージを使わず、Kaiser窓付きsincからhalfband係数を生成する。
halfband補間器の係数は2倍補間用にDCゲイン2へ正規化する。
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass


def bessel_i0(x: float) -> float:
    """Kaiser窓用の第一種変形Bessel関数I0を級数で求める。"""

    value = 1.0
    term = 1.0
    x_half = x / 2.0
    for k in range(1, 80):
        term *= (x_half / k) ** 2
        value += term
        if abs(term) < abs(value) * 1.0e-15:
            break
    return value


def round_away_from_zero(value: float) -> int:
    if value >= 0.0:
        return math.floor(value + 0.5)
    return math.ceil(value - 0.5)


def kaiser_window(index: int, taps: int, beta: float) -> float:
    position = 2.0 * index / (taps - 1) - 1.0
    argument = beta * math.sqrt(max(0.0, 1.0 - position * position))
    return bessel_i0(argument) / bessel_i0(beta)


def design_halfband(taps: int, beta: float) -> list[float]:
    if taps < 3 or taps % 4 != 3:
        raise ValueError("taps must be 4k+3 for a symmetric halfband filter")

    center = taps // 2
    coefficients: list[float] = []
    for index in range(taps):
        distance = index - center
        ideal = 0.5 * (1.0 if distance == 0 else math.sin(math.pi * 0.5 * distance) / (math.pi * 0.5 * distance))
        coefficient = 2.0 * ideal * kaiser_window(index, taps, beta)

        # halfbandの偶数オフセットは理想値が0であり、係数量子化後も0に固定する。
        if distance != 0 and distance % 2 == 0:
            coefficient = 0.0
        coefficients.append(coefficient)

    # 中心係数を1に固定する。もう一つのpolyphaseは遅延した入力の
    # そのままの値になるため、ここを量子化誤差で変化させない。
    center_value = coefficients[center]
    non_center_sum = sum(coefficients) - center_value
    scale = 1.0 / non_center_sum
    return [
        coefficient * scale if index != center else 1.0
        for index, coefficient in enumerate(coefficients)
    ]


def quantize(coefficients: list[float], width: int) -> list[int]:
    # 18bit係数はGroundlessのFixedPoint::q2_16と揃える。
    # Q2.(width-2)なら+1.0を正確に表現できる。
    scale = 1 << (width - 2)
    limit = (1 << (width - 1)) - 1
    minimum = -(1 << (width - 1))
    return [max(minimum, min(limit, round_away_from_zero(value * scale))) for value in coefficients]


def response_db(coefficients: list[float], frequency: float) -> float:
    real = 0.0
    imag = 0.0
    for index, coefficient in enumerate(coefficients):
        angle = -2.0 * math.pi * frequency * index
        real += coefficient * math.cos(angle)
        imag += coefficient * math.sin(angle)
    magnitude = math.hypot(real, imag)
    if magnitude <= 1.0e-15:
        return -300.0
    return 20.0 * math.log10(magnitude)


@dataclass(frozen=True)
class Metrics:
    passband_ripple_db: float
    stopband_max_db: float


def measure(
    coefficients: list[int],
    coefficient_width: int,
    sample_rate: float,
    passband_hz: float,
    stopband_hz: float,
    points: int = 2001,
) -> Metrics:
    scale = float(1 << (coefficient_width - 2))
    normalized = [coefficient / scale for coefficient in coefficients]
    passband = [
        response_db(normalized, passband_hz / sample_rate * index / (points - 1))
        for index in range(points)
    ]
    stopband = [
        response_db(
            normalized,
            (stopband_hz / sample_rate)
            + (0.5 - stopband_hz / sample_rate) * index / (points - 1),
        )
        for index in range(points)
    ]
    return Metrics(
        passband_ripple_db=max(passband) - min(passband),
        stopband_max_db=max(stopband),
    )


def find_taps(
    coefficient_width: int,
    sample_rate: float,
    passband_hz: float,
    stopband_hz: float,
    stopband_limit_db: float,
    passband_limit_db: float,
    beta: float,
) -> tuple[int, list[int], Metrics]:
    for taps in range(7, 128, 4):
        floating = design_halfband(taps, beta)
        integer = quantize(floating, coefficient_width)
        metrics = measure(integer, coefficient_width, sample_rate, passband_hz, stopband_hz)
        if metrics.passband_ripple_db <= passband_limit_db and metrics.stopband_max_db <= -stopband_limit_db:
            return taps, integer, metrics
    raise RuntimeError("no tap count met the requested response")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample-rate", type=float, default=96_000.0)
    parser.add_argument("--passband", type=float, default=20_000.0)
    parser.add_argument("--stopband", type=float, default=28_000.0)
    parser.add_argument("--coefficient-width", type=int, default=18)
    parser.add_argument("--stopband-limit", type=float, default=80.0)
    parser.add_argument("--passband-limit", type=float, default=0.05)
    parser.add_argument("--beta", type=float, default=7.86)
    parser.add_argument("--taps", type=int)
    args = parser.parse_args()

    if args.taps is None:
        taps, coefficients, metrics = find_taps(
            args.coefficient_width,
            args.sample_rate,
            args.passband,
            args.stopband,
            args.stopband_limit,
            args.passband_limit,
            args.beta,
        )
    else:
        taps = args.taps
        floating = design_halfband(taps, args.beta)
        coefficients = quantize(floating, args.coefficient_width)
        metrics = measure(
            coefficients,
            args.coefficient_width,
            args.sample_rate,
            args.passband,
            args.stopband,
        )

    print(f"taps={taps}")
    print(f"coefficient_width={args.coefficient_width}")
    print(f"passband_ripple_db={metrics.passband_ripple_db:.6f}")
    print(f"stopband_max_db={metrics.stopband_max_db:.6f}")
    print("coefficients=")
    print(", ".join(str(coefficient) for coefficient in coefficients))


if __name__ == "__main__":
    main()
