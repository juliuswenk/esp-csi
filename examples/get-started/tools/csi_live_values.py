#!/usr/bin/env python3

import argparse
import ast
import csv
import json
import math
import sys
import time


def parse_csi_line(line):
    start = line.find("CSI_DATA")
    if start < 0:
        return None

    row = next(csv.reader([line[start:].strip()]))
    values = ast.literal_eval(row[-1])
    amps = [
        math.hypot(values[i + 1], values[i])
        for i in range(0, len(values) - 1, 2)
    ]
    if not amps:
        return None

    return {
        "id": int(row[1]),
        "mac": row[2],
        "rssi": int(row[3]),
        "timestamp": int(row[18]),
        "mean_amp": sum(amps) / len(amps),
        "amps": amps,
    }


def line_source(args):
    if args.input_file:
        with open(args.input_file, "r") as handle:
            for line in handle:
                yield line
        return

    import serial

    with serial.Serial(args.port, args.baud, timeout=1) as stream:
        while True:
            yield stream.readline().decode("utf-8", "replace")


def load_baseline(path, frame_limit):
    frames = []
    with open(path, "r") as handle:
        for line in handle:
            parsed = parse_csi_line(line)
            if not parsed:
                continue
            frames.append(parsed["amps"])
            if len(frames) >= frame_limit:
                break

    if not frames:
        raise ValueError(f"No CSI_DATA rows found in baseline file: {path}")

    width = min(len(frame) for frame in frames)
    return [
        sum(frame[i] for frame in frames) / len(frames)
        for i in range(width)
    ], len(frames), width


def vector_distance(a, b):
    count = min(len(a), len(b))
    if count == 0:
        return 0.0
    return sum(abs(a[i] - b[i]) for i in range(count)) / count


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def main():
    parser = argparse.ArgumentParser(
        description="Convert esp-csi CSI_DATA rows into simple live sensing values."
    )
    parser.add_argument("-p", "--port", default="/dev/cu.usbmodem2101")
    parser.add_argument("--baud", type=int, default=921600)
    parser.add_argument("--input-file")
    parser.add_argument("--baseline-file")
    parser.add_argument("--calibration-frames", type=int, default=250)
    parser.add_argument("--emit-every", type=float, default=0.2)
    parser.add_argument("--emit-frames", type=int, default=15)
    parser.add_argument("--motion-scale", type=float, default=18.0)
    parser.add_argument("--presence-scale", type=float, default=16.0)
    args = parser.parse_args()

    baseline_frames = []
    baseline = None
    previous = None
    motion_smooth = 0.0
    presence_smooth = 0.0
    last_emit = 0.0
    frame_count = 0

    if args.baseline_file:
        baseline, frames, width = load_baseline(args.baseline_file, args.calibration_frames)
        print(
            json.dumps(
                {
                    "event": "calibrated",
                    "source": args.baseline_file,
                    "frames": frames,
                    "subcarriers": width,
                }
            ),
            flush=True,
        )

    for raw_line in line_source(args):
        parsed = parse_csi_line(raw_line)
        if not parsed:
            continue

        frame_count += 1
        amps = parsed["amps"]

        if baseline is None:
            baseline_frames.append(amps)
            if len(baseline_frames) >= args.calibration_frames:
                width = min(len(frame) for frame in baseline_frames)
                baseline = [
                    sum(frame[i] for frame in baseline_frames) / len(baseline_frames)
                    for i in range(width)
                ]
                print(
                    json.dumps(
                        {
                            "event": "calibrated",
                            "frames": len(baseline_frames),
                            "subcarriers": width,
                        }
                    ),
                    flush=True,
                )
            continue

        motion_raw = vector_distance(amps, previous) if previous else 0.0
        presence_raw = vector_distance(amps, baseline)
        previous = amps

        motion = clamp(motion_raw / args.motion_scale)
        presence = clamp(presence_raw / args.presence_scale)

        motion_smooth = 0.75 * motion_smooth + 0.25 * motion
        presence_smooth = 0.9 * presence_smooth + 0.1 * presence

        should_emit = False
        if args.input_file:
            should_emit = frame_count % args.emit_frames == 0
        else:
            now = time.monotonic()
            should_emit = now - last_emit >= args.emit_every
            if should_emit:
                last_emit = now

        if should_emit:
            print(
                json.dumps(
                    {
                        "frame": frame_count,
                        "rssi": parsed["rssi"],
                        "mean_amp": round(parsed["mean_amp"], 3),
                        "motion_energy": round(motion_smooth, 3),
                        "presence_confidence": round(presence_smooth, 3),
                        "motion_raw": round(motion_raw, 3),
                        "presence_raw": round(presence_raw, 3),
                    }
                ),
                flush=True,
            )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
