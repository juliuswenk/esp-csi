#!/usr/bin/env python3

import argparse
import ast
import csv
import json
import math
import os
import statistics as stats
import threading
import time
from pathlib import Path


DEFAULT_RECEIVERS = {
    "left": "/dev/cu.usbmodem1101",
    "center": "/dev/cu.usbmodem2101",
    "right": "/dev/cu.usbmodem101",
}


def parse_csi(line):
    start = line.find("CSI_DATA")
    if start < 0:
        return None
    try:
        row = next(csv.reader([line[start:].strip()]))
        values = ast.literal_eval(row[-1])
        amps = [
            math.hypot(values[i + 1], values[i])
            for i in range(0, len(values) - 1, 2)
        ]
        return {
            "rssi": int(row[3]),
            "timestamp": int(row[18]),
            "mean_amp": sum(amps) / len(amps),
            "amps": amps,
        }
    except Exception:
        return None


def capture_port(label, port, baud, duration, output_path, result):
    import serial

    lines = []
    valid = 0
    started = time.time()
    try:
        with serial.Serial(port, baud, timeout=0.2) as stream:
            while time.time() - started < duration:
                line = stream.readline().decode("utf-8", "replace").strip()
                if not line:
                    continue
                lines.append(line)
                if parse_csi(line):
                    valid += 1
        output_path.write_text("\n".join(lines) + "\n")
        result[label] = {"ok": True, "lines": len(lines), "valid": valid}
    except Exception as exc:
        result[label] = {"ok": False, "error": str(exc)}


def load_frames(path):
    frames = []
    for line in path.read_text().splitlines():
        parsed = parse_csi(line)
        if parsed:
            frames.append(parsed)
    return frames


def average_vector(frames):
    if not frames:
        return []
    width = min(len(frame["amps"]) for frame in frames)
    return [
        sum(frame["amps"][i] for frame in frames) / len(frames)
        for i in range(width)
    ]


def vector_distance(a, b):
    width = min(len(a), len(b))
    if width == 0:
        return 0.0
    return sum(abs(a[i] - b[i]) for i in range(width)) / width


def capture(args):
    receivers = dict(DEFAULT_RECEIVERS)
    if args.receiver:
        for item in args.receiver:
            label, port = item.split("=", 1)
            receivers[label] = port

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"{args.phase} starts in {args.delay}s", flush=True)
    time.sleep(args.delay)
    print(f"recording {args.phase} for {args.duration}s", flush=True)

    result = {}
    threads = []
    for label, port in receivers.items():
        output_path = outdir / f"{args.phase}_{label}.csv"
        thread = threading.Thread(
            target=capture_port,
            args=(label, port, args.baud, args.duration, output_path, result),
            daemon=True,
        )
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    summary_path = outdir / f"{args.phase}_summary.json"
    summary_path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)


def analyze(args):
    outdir = Path(args.outdir)
    receivers = list(DEFAULT_RECEIVERS.keys())
    baseline = {}
    for label in receivers:
        frames = load_frames(outdir / f"{args.baseline}_{label}.csv")
        baseline[label] = average_vector(frames)

    rows = []
    for phase in args.phase:
        scores = {}
        for label in receivers:
            frames = load_frames(outdir / f"{phase}_{label}.csv")
            avg = average_vector(frames)
            distances = [
                vector_distance(frame["amps"], baseline[label])
                for frame in frames
            ]
            scores[label] = {
                "rows": len(frames),
                "presence_mean": vector_distance(avg, baseline[label]),
                "presence_p95": sorted(distances)[int(0.95 * len(distances))]
                if distances
                else 0.0,
                "rssi_mean": stats.mean(frame["rssi"] for frame in frames)
                if frames
                else 0.0,
            }
        total = sum(item["presence_mean"] for item in scores.values()) or 1.0
        confidence = {
            label: scores[label]["presence_mean"] / total
            for label in receivers
        }
        winner = max(confidence, key=confidence.get)
        rows.append({"phase": phase, "winner": winner, "confidence": confidence, "scores": scores})

    print(json.dumps(rows, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    capture_parser = sub.add_parser("capture")
    capture_parser.add_argument("--phase", required=True)
    capture_parser.add_argument("--duration", type=float, default=12)
    capture_parser.add_argument("--delay", type=float, default=5)
    capture_parser.add_argument("--baud", type=int, default=921600)
    capture_parser.add_argument("--outdir", default="captures/multi_zone_test")
    capture_parser.add_argument("--receiver", action="append")
    capture_parser.set_defaults(func=capture)

    analyze_parser = sub.add_parser("analyze")
    analyze_parser.add_argument("--outdir", default="captures/multi_zone_test")
    analyze_parser.add_argument("--baseline", default="baseline")
    analyze_parser.add_argument("--phase", action="append", required=True)
    analyze_parser.set_defaults(func=analyze)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
