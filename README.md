# Vexy the Vertex

**An Animated Educational Cartoon for the Graphics Pipeline**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/Pygame-2.x-green.svg)](https://www.pygame.org/)
[![OpenGL](https://img.shields.io/badge/OpenGL-Fixed%20Function-orange.svg)](https://www.opengl.org/)
[![License](https://img.shields.io/badge/License-Educational-lightgrey.svg)](#)

> *Before I was a character, I was just... three points.*

**Vexy the Vertex** is an interactive educational cartoon that teaches the classic computer graphics pipeline through a friendly triangular character named Vexy. Using real-time OpenGL rendering, the application walks learners through vertices, transformations, color interpolation, rasterization, depth testing, lighting, and projection — with live code snippets shown alongside every animation.

---

## Features

- **6 sequential animated chapters** covering the core graphics pipeline
- **Live code panel** showing the exact OpenGL calls being demonstrated
- **Cartoon character “Vexy”** with expressive face, walk cycle, mood changes, and speech bubbles
- **Smooth easing animations**, title cards, captions, and progress bar
- **Keyboard controls** for pause, chapter navigation, code toggle, and restart
- **Self-contained** — no external assets beyond system fonts
- **Educational focus** — designed for Computer Graphics lab courses

---

## Chapters

| # | Chapter | Core Concept |
|---|---------|--------------|
| 1 | **Vertices & Primitives** | A vertex is a point. Three vertices make a triangle. Vexy is born. |
| 2 | **Transformations** | Translate, rotate, scale. Matrix order matters (spin-in-place vs. orbit). |
| 3 | **Colors & Interpolation** | `GL_FLAT` vs `GL_SMOOTH`. Barycentric weights and per-vertex color blending. |
| 4 | **Rasterization** | Edge-function pixel tests. Scanline visualization of which pixels a triangle covers. |
| 5 | **Depth, Light & Projection** | Depth buffer, surface normals, lighting, perspective vs orthographic projection. |
| Finale | **The Graphics Pipeline** | End-to-end assembly-line visualization of all stages working together. |

---

## Screenshots

| Chapter 1 – Vertices | Chapter 2 – Transformations |
|:--------------------:|:----------------------------:|
| Vexy born from three points | Translate / Rotate / Scale demos |

| Chapter 3 – Colors | Chapter 4 – Rasterization |
|:------------------:|:-------------------------:|
| Flat vs Smooth shading | Pixel coverage via edge tests |

| Chapter 5 – 3D | Finale – Pipeline |
|:--------------:|:-----------------:|
| Depth, lighting & projection | Assembly-line of the whole pipeline |

---

## Requirements

- Python 3.8 or newer
- A desktop environment with OpenGL support (Windows / Linux / macOS)
- Graphics driver that provides a fixed-function OpenGL context

### Dependencies

```bash
python -m pip install pygame PyOpenGL
```

---

## How to Run

```bash
python graphics_cartoon.py
```

The application opens a **1280 × 720** window and starts from Chapter 1.

---

## Controls

| Key | Action |
|-----|--------|
| `SPACE` | Pause / Resume |
| `←` / `→` | Previous / Next chapter |
| `C` | Toggle live code panel |
| `R` | Restart from Chapter 1 |
| `ESC` | Quit |

---

## Learning Outcomes

After exploring the application, a student should be able to:

1. Explain what a vertex is and why triangles are the fundamental primitive.
2. Reason about the effect of `glTranslatef` / `glRotatef` / `glScalef` and why call order matters.
3. Contrast flat vs. smooth shading and compute a color via barycentric interpolation.
4. Describe the edge-function test used in rasterization and why pixel centers are tested.
5. State the purpose of the depth buffer and surface normals in lighting calculations.
6. Distinguish perspective from orthographic projection and when each is appropriate.

---

## Project Structure

```
.
├── graphics_cartoon.py   # Complete application (single file)
└── README.md             # This file
```

The entire application lives in one well-commented Python module for easy reading and modification.

### Architecture Overview

- **`Scene` base class** — shared metadata, captions, code panel, and drawing interface
- **Chapter classes** (`Chapter1` … `Chapter5` + `Finale`) — scene-specific animation and logic
- **`Player`** — manages scene list, timing, pause state, progress bar, and input
- **Drawing helpers** — 2D primitives, text cache, 3D cube/sphere/lighting utilities
- **Animation utilities** — `clamp`, `lerp`, `smoothstep`, `ease_out_back`, etc.

---

## Technology Stack

| Technology | Role |
|------------|------|
| **Python 3** | Application logic and animation timing |
| **Pygame** | Window management, event loop, font rendering |
| **PyOpenGL (OpenGL.GL)** | Immediate-mode geometry, color, matrices, depth, lighting |
| **PyOpenGL (OpenGL.GLU)** | Perspective, camera, sphere rendering |
| **Standard library** | `math`, `random`, `sys` |

---

## Suggested Experiments (“Try It Yourself”)

The source is designed as a playground. Try these modifications:

- Change Vexy’s `BODY` vertices and observe the effect
- Add a mirrored transformation using negative scale
- Extend the color lesson with `GL_QUADS` or `GL_TRIANGLE_FAN`
- Enable face culling (`GL_CULL_FACE`) in Chapter 5
- Implement a simple texture-mapping chapter (scaffolding is already commented)
- Port one chapter to modern OpenGL (VBOs + GLSL shaders)

---

## Current Limitations

- Uses legacy fixed-function OpenGL and immediate mode (intentionally simple for teaching)
- Window size, world coordinates, and layout constants are hard-coded
- Rasterization demo is educational, not a full hardware rasterizer
- Single-file delivery — no separate config, installer, or automated test suite
- No audio narration or interactive vertex editor (yet)

---

## Future Ideas

- Chapter 6 — Texture Mapping
- Modern OpenGL (VBO / VAO / GLSL) port while keeping the narrative structure
- Back-face culling demonstration
- Multi-sample anti-aliased rasterization comparison
- Interactive vertex editor (drag Vexy’s points in real time)
- WebGL / video export version for classroom projection

---

## Author

**MD. Osiur Rahman Rahif**  
ID: 23300149  

Course: Computer Graphics Lab (`0613-CSE-4013`)  
Submitted to: Tanjina Akter, Assistant Professor, CSE, RPSU  

---

## License

This project is released for **educational purposes**.  
Feel free to use, modify, and extend it for learning and teaching computer graphics.

---

<p align="center">
  <b>Thanks for watching!</b><br>
  Now it’s <i>your</i> turn to play with the code.
</p>
