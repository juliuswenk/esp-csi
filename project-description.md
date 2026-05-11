# General info:

### contributors:

Visuals: Lennard Lev
Installation Design: Lena Eibel
Hardware: Julius Wenk

This project was conceptualized & completed in 5 days as part of the short-term-projects that are port of the Bachelors of Communcation Design at the HTW Berlin.

Its development was made possible by the guidance of Prof. Alexander Müller-Rakow and Christian Pflug.

## Links to videos:

kzp-invisible-waves-doku.mp4: https://vimeo.com/1191205459?share=copy&fl=sv&fe=ci


## Project description

**Invisible Waves** – a camera-free through-wall installation prototype. One ESP32-S3 sender and three ESP32-S3 receivers detect a person moving behind a wall via WiFi CSI, and a p5.js sketch renders the signal as an abstract, glitchy visual.

The goal is not accurate pose estimation but an installation aesthetic: soft, probabilistic, machine-like perception.

# Teaser Text for use in Website:

What happens when walls no longer separate seen from unseen?

Veiled Panopticon turns WiFi signals that already pass through everyday spaces into a camera-free way of sensing human presence. Making the threat of surveillance a palpable through showing that the infrastructure needed already surrounds us.

# Descriptor Text for Website:

Veiled Panopticon uses one ESP32-S3 sender and three ESP32-S3 receivers to read subtle changes in wireless signal behaviour as a person moves behind a wall. The system translates variations in signal strength and channel-state data into a soft, probabilistic sense of presence.

The project explores a form of machine perception that has no need for visible surveillance. It suggests a near future in which sensing is embedded in the infrastructure already around us: routers, devices, and electromagnetic fields become quiet instruments of spatial awareness. In doing so, Veiled Panopticon asks what happens when walls no longer fully separate seen from unseen, and when ordinary environments become readable through signals we usually ignore.

Its implications are both practical and uneasy. Camera-free sensing could enable new forms of accessibility, automation, safety, and spatial interaction, especially where visual monitoring is intrusive or impossible. At the same time, it raises questions about privacy, consent, and public space. If presence can be detected without an image, and even through barriers, then the boundary between observation and invisibility becomes harder to locate.


## Hardware

- **1x sender** (external / standalone power)
- **3x receivers** (left/center/right) plugged into the host Mac over USB serial
- All boards: **Arduino Nano ESP32 (ESP32-S3)**

Firmware is based on Espressif's `esp-csi` `csi_send` / `csi_recv` examples, built with various channel and LED configurations under `examples/get-started/csi_send/build-*/` and `csi_recv/build-*/`.

## Python tools (`examples/get-started/tools/`)

| Tool | Purpose |
|------|---------|
| `rssi_presence_ui.py` | Main GUI. Reads CSI from 3 serial ports, computes amplitude deltas + RSSI, outputs zone confidence (left/center/right), optional SSE server on port 8765 for the p5.js frontend. Uses adaptive baseline, subcarrier weighting, cross-receiver correlation, output smoothing. |
| `csi_feature_viewer.py` | Live feature UI – real-time per-subcarrier amplitude deltas. |
| `csi_zone_visualizer.py` | Zone visualizer with subcarrier-weighted detection, cross-receiver correlation, UDP streaming. |
| `csi_labeled_accuracy_test.py` | Calibration tool: captures labeled baseline + zone recordings, generates `zone_model.json`, `analysis_report.md`. |
| Detection tests | `csi_baseline_test.py`, `csi_doppler_test.py`, `csi_enhanced_spatial_test.py`, `csi_cir_test.py`, `csi_phase_position_test.py`, `csi_rate_of_change_test.py`, `csi_stable_subcarrier_test.py`, `csi_advanced_baseline_test.py` |
| Subcarrier analysis | `csi_subcarrier_quality.py` (quality mask from CSV log), `csi_subcarrier_stability.py` (most stable subcarriers per receiver) |
| `csi_noise_profile.py` | Idle noise floor characterisation. |

## p5.js visualization (`index.html` + `sketch.js`)

The main sketch (`1385 lines`) renders:

- **Figure silhouettes** – loaded from `figur.svg`, animated as up to 2 simultaneous figures slide to left/center/right positions
- **Wave interference** – two layered sine fields with contrast control
- **Room background** – `Background Room.png` overlay with glitch bands and chromatic aberration
- **Ghosts** – drifting silhouettes with per-line noise-based distortion
- **Blobs** – background amoeba-like shapes that spawn, drift, warp
- **CRT scanlines / screen-door effect**
- **Detection bounding boxes** – jittery boxes on head/body
- **Real-time input** – connects to `rssi_presence_ui.py` SSE endpoint for live zone confidence data
- **Keyboard controls** – A/S/D to manually trigger left/center/right figures; Space to switch to alternative view

An alternative minimal visualization is at `examples/visualization/installation-visual.html`.

## How it runs

```bash
# Terminal 1 – CSI backend (opens PyQt5 GUI + SSE server on :8765)
cd examples/get-started/tools
source .venv/bin/activate
python rssi_presence_ui.py --sse-port 8765

# Terminal 2 – HTTP server for p5.js
# (from repo root)
python3 -m http.server 8000

# Browser → http://localhost:8000/index.html
```

## Current state

- **All core goals met**: presence detection, coarse left/center/right localisation, real-time visual output.
- **Stretch goals achieved**: fluid figure animation across zones, glitch/ghost/chromatic aberration aesthetic, SSE streaming to p5.js.
- Detection is driven by per-subcarrier amplitude deltas, adaptive baseline, cross-receiver correlation, and output smoothing.
- Calibration is done once per installation via `csi_labeled_accuracy_test.py` which produces a `zone_model.json`.

## Key docs

- `prototype-commands.md` – full command reference, hardware mapping, build/flash commands, tuning parameters
- `prompt-thread-codex.md` / `prompt-thread-opencode.md` – development history
