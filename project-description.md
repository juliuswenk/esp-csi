## Project description

I am building a **camera-free through-wall sensing prototype** using **two Arduino Nano ESP32 boards (ESP32-S3)** and the **Espressif `esp-csi` repo** as the main technical base. The goal is not full human pose estimation, but a **working installation prototype** that detects a person moving behind a wall and converts that signal into a live visual, ideally an amorphous blob drifting from left to right across the screen as the person moves.[1][2][3][4]

The system should use **real CSI data**, not simulated input. One ESP32 should act as **transmitter/sender**, one as **receiver**, and a host computer should log/process the CSI stream and output simplified motion values for visualization. The sensing setup should start simple and reliable, prioritizing **presence detection**, **motion intensity**, and if possible **coarse left/center/right localization**, rather than full pose or identity.[2][5][6][7][1]

This is an **art/installation prototype**, so the visual output should embrace uncertainty rather than pretending to be an accurate camera-like reconstruction. The desired result is a soft, unstable, machine-perception aesthetic: a probabilistic blob, pressure field, or drifting disturbance that reflects human movement behind architecture.[3][7][2]

## Hardware context

- 2x **Arduino Nano ESP32** boards on hand; these use **ESP32-S3**, which is supported by Espressif CSI tooling.[4][1]
- Setup assumption: **separate transmitter and receiver**.[1]
- Host computer available for logging, preprocessing, and sending data to a visual system.[5]

## Main repo to build from

### Primary base
- **`espressif/esp-csi`**: official Espressif CSI framework; includes `get-started` examples such as `csi_send`, `csi_recv`, `csi_recv_router`, parsing tools, and `esp-radar` examples for human activity detection.[1]

### Secondary references
- **`thu4n/ESP32-WiFi-Sensing`**: useful reference for a full two-ESP32 sensing pipeline; includes collected datasets, trained models, notebooks, and real-time inference code that publishes predictions after inference.[8][5]
- **`StevenMHernandez/ESP32-CSI-Tool` / ESP32 CSI Toolkit**: useful reference for online CSI extraction and lightweight CSI workflows without complicated firmware hacks.[6]
- **`euaziel/WiFi-CSI-Human-Pose-Detection`**: interesting as a high-ambition reference for pose estimation / through-wall sensing, but likely too complex for the current prototype and should not be the main implementation path.[9][3]

## Technical goal

Please help me turn `esp-csi` into a **minimal working sensing pipeline** for my hardware and project. The ideal development sequence is:

1. Confirm both Nano ESP32 boards can be flashed and used with the repo.[4][1]
2. Configure one board as CSI sender and one as receiver.[1]
3. Stream or log CSI data on the host computer.[6][1]
4. Build the simplest possible live analysis layer that outputs:
   - `presence_confidence`
   - `motion_energy`
   - optionally `left_confidence`, `center_confidence`, `right_confidence`.[7][2]
5. Prefer simple heuristics or lightweight classification first; do **not** start with deep pose estimation or a heavy ML stack unless absolutely necessary.[3][5]
6. Make the system robust enough for a quick installation prototype, even if localization is rough.[2][7]

## Spatial / sensing assumption

The intended staging is: a person moves behind a wall from side to side, while the transmitter and receiver stay fixed on the sensing side. The system only needs to detect **coarse spatial movement** and translate it into a probabilistic visual output. If continuous tracking is too hard, a fallback of **3 broad zones** (left / center / right) is acceptable and preferred over an unstable fake-precise position estimate.[7][2]

## Basic visual goals

These are the minimum success criteria for the prototype:

- Detect **presence vs no presence** behind a wall.[2][7]
- Detect **movement intensity** behind a wall.[2]
- Output one or a few live values that can drive a visual system.[6][1]
- Visual output should be a **single amorphous blob** or soft pressure field that appears when a person is present and changes when they move.
- The blob does **not** need to resemble a body.[10]

## Stretch visual goals

If the sensing is stable enough, the stretch goals are:

- Blob shifts **left / center / right** as a person moves laterally behind the wall.[7]
- Blob size / brightness / instability responds to movement energy.[2]
- Visual uncertainty is preserved through flicker, trail, drift, or splitting rather than hidden.
- If possible, multiple confidence zones feed a more fluid TouchDesigner visual, but this is secondary to getting a reliable sensing signal first.[11][12]

## Important constraints

- Time is short; prioritize **working sensing** over elegant architecture.[1]
- Do not optimize for full pose estimation.[3]
- Do not assume pre-trained models from other repos will generalize to my wall or room.[5]
- Favor a small, debuggable pipeline over a research-grade feature set.[6][1]

## Preferred implementation attitude

I want the project to succeed as an **installation prototype**, not as a benchmark demo. Please bias decisions toward:
- fastest path to real data,
- easy debugging,
- coarse but stable outputs,
- and values that can directly drive an external visual system such as TouchDesigner.[12][11]
