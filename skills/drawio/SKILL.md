---
name: drawio
description: 当用户要求创建、生成、绘制或设计任何图表时使用 — 包括流程图、架构图、ER图、时序图、类图、网络拓扑图、思维导图、线框图、原型图、UI草图、BPMN、云架构图、UML图、组织架构图、甘特图，以及任何可视化/图形化图表。当用户提到 draw.io、drawio、drawoi、.drawio 文件，或要求导出为 PNG/SVG/PDF 格式时也应使用。
---

# Draw.io Diagram Skill (Windows)

Generate draw.io diagrams as native `.drawio` files on Windows. Requires [draw.io Desktop](https://github.com/jgraph/drawio-desktop/releases) for opening files and PNG/SVG/PDF export.

## Workflow

1. **Understand** what diagram the user wants — type, content, layout direction, labels
2. **Read the XML reference** from `references/xml-reference.md` for proper draw.io XML format, styles, containers, edges, and layout rules. Also read `references/style-reference.md` for the complete style properties catalog
3. **Generate draw.io XML** in mxGraphModel format for the requested diagram. Follow the reasoning budget and rigid grid from `references/xml-reference.md`
4. **Write the XML** to a `.drawio` file using the Write tool
5. **Open the result** — if the user requested export format, export via draw.io CLI then open the exported file. Otherwise open the `.drawio` file directly
6. If the open command fails, print the file path so the user can open it manually

## Output format

Check the user's request for format preference:

- `/drawio create a flowchart` → `flowchart.drawio` (opens in draw.io Desktop)
- `/drawio png flowchart for login` → `login-flow.drawio.png` (export + embed XML)
- `/drawio svg: ER diagram` → `er-diagram.drawio.svg`
- `/drawio pdf architecture overview` → `architecture-overview.drawio.pdf`

If no format is mentioned, just write the `.drawio` file and open it. The user can always ask to export later.

## File naming

- Use descriptive lowercase names with hyphens: `login-flow.drawio`, `database-schema.drawio`
- For export: `name.drawio.png`, `name.drawio.svg`, `name.drawio.pdf` (double extension signals embedded XML)
- After successful export, DELETE the intermediate `.drawio` file — the exported file contains the full diagram XML

## draw.io Desktop on Windows

### Opening .drawio files

```powershell
Start-Process "<file>"
```

If `start` fails (e.g., no file association), tell the user to open the file manually — print the full path.

### CLI for export

The draw.io Desktop app includes a command-line interface. Locate it in this order:

1. `where.exe draw.io` — check if on PATH first
2. `"C:\Program Files\draw.io\draw.io.exe"` — per-machine install
3. `"$env:LOCALAPPDATA\Programs\draw.io\draw.io.exe"` — per-user install

### Export command

```powershell
& "<drawio-exe>" -x -f <format> -e -b 10 -o <output> <input.drawio>
```

Key flags:
- `-x` / `--export`: export mode
- `-f` / `--format`: output format (png, svg, pdf, jpg)
- `-e` / `--embed-diagram`: embed diagram XML in the output (PNG, SVG, PDF only)
- `-o` / `--output`: output file path
- `-b` / `--border`: border width (default 0)
- `-t` / `--transparent`: transparent background (PNG only)
- `-s` / `--scale`: scale factor

### If CLI is not found

Keep the `.drawio` file and tell the user they can install draw.io Desktop from https://github.com/jgraph/drawio-desktop/releases to enable export, or open the `.drawio` file directly in draw.io Desktop.

## XML format

A `.drawio` file is native mxGraphModel XML. Generate XML directly — Mermaid and CSV require server-side conversion and cannot be saved as native `.drawio` files.

### Basic structure

```xml
<mxGraphModel adaptiveColors="auto">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <!-- Diagram cells go here with parent="1" -->
  </root>
</mxGraphModel>
```

- Cell `id="0"` is the root layer
- Cell `id="1"` is the default parent layer
- All diagram elements use `parent="1"` unless using multiple layers

## XML generation reference

Read the complete reference at `references/xml-reference.md` for:
- Common styles (rounded rectangles, diamonds, arrows, labeled arrows)
- HTML labels with `html=1`
- Edge rules (CRITICAL: every edge must have `<mxGeometry relative="1" as="geometry"/>`)
- Containers and groups (swimlanes, invisible groups, nested architecture)
- Layers and tags
- Dark mode colors
- XML well-formedness rules

For the full style property catalog (all shapes, colors, perimeters, edge styles, UML shapes, stencils), read `references/style-reference.md`.

## CRITICAL: XML well-formedness

- NEVER include XML comments (`<!-- -->`) in the output — they are strictly forbidden
- Escape special characters in attribute values: `&amp;`, `&lt;`, `&gt;`, `&quot;`
- Always use unique `id` values for each `mxCell`
- Every edge cell MUST have a `<mxGeometry relative="1" as="geometry"/>` child element (self-closing edges fail)
- Do NOT add `<Array as="points">` waypoints — edges are routed automatically
- Do NOT set `exitX`/`exitY`/`entryX`/`entryY` unless you have specific geometric intent

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| File won't open | No .drawio file association | Print the full file path for manual opening |
| Export fails | draw.io Desktop not installed | Keep the .drawio file and suggest installing draw.io Desktop |
| Diagram opens blank | Missing root cells id="0" and id="1" | Ensure the basic mxGraphModel structure is complete |
| Edges not rendering | Edge cell is self-closing | Every edge needs `<mxGeometry relative="1" as="geometry"/>` |
| Layout looks wrong | Incorrect coordinates or missing parent | Use the rigid grid and verify parent="1" on all cells |
