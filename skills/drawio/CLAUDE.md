# Draw.io Skill — Implementation Notes

Standalone Claude Code skill for generating native `.drawio` files on Windows, with optional export to PNG/SVG/PDF (with embedded XML) using the draw.io desktop CLI. No MCP server required.

## Key Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Claude Code skill file (copy this to `.claude/skills/drawio/` for installation) |
| `references/xml-reference.md` | Draw.io XML generation reference (local copy from `shared/`, single source of truth) |
| `references/style-reference.md` | Complete draw.io style property catalog (local copy from `shared/`) |

## How It Works

1. User invokes `/drawio` or Claude detects a diagram request
2. Claude reads `references/xml-reference.md` and `references/style-reference.md` for proper XML format and styles
3. Claude generates mxGraphModel XML for the requested diagram
4. The XML is written to a `.drawio` file in the working directory via the Write tool
5. If the user requested an export format (png, svg, pdf), the draw.io CLI exports with `--embed-diagram`, then deletes the source `.drawio` file
6. The result is opened via `start <file>` (Windows)

Default output is `.drawio` (no export). The user requests export by mentioning a format: `/drawio png ...`, `/drawio svg: ...`, etc.

## Draw.io CLI Locations (Windows)

Try in order:
1. `where.exe draw.io` (on PATH)
2. `"C:\Program Files\draw.io\draw.io.exe"` (per-machine install)
3. `"$env:LOCALAPPDATA\Programs\draw.io\draw.io.exe"` (per-user install)

Export command:
```powershell
& "<drawio-exe>" -x -f <format> -e -b 10 -o <output> <input.drawio>
```

## Why XML Only?

A `.drawio` file is native mxGraphModel XML. Mermaid and CSV formats require draw.io's server-side conversion and cannot be saved as native files. The skill generates XML directly for all diagram types.

## Shared References (Single Source of Truth)

Two canonical reference files live in `shared/` at the repo root and feed every delivery mechanism in this project:

- **`shared/xml-reference.md`** — draw.io XML generation reference: styles, edge routing, containers, layers, tags, metadata, dark mode, well-formedness rules.
- **`shared/style-reference.md`** — draw.io style property catalog: all shapes, colors, perimeters, edge styles, UML shapes, stencils.

This skill bundles local copies in `references/` for offline use. When updating diagram-generation guidance, edit the originals in `shared/` — changes propagate to all consumers automatically.

## Coding Conventions

- **Allman brace style**: Opening braces go on their own line for all control structures, functions, objects, and callbacks.

  ```js
  function example()
  {
    if (condition)
    {
      doSomething();
    }
    else
    {
      doOther();
    }
  }
  ```

- Prefer `function()` expressions over arrow functions for callbacks.

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| XML comments in output | `<!-- -->` comments found in generated XML | Remove all XML comments — they are strictly forbidden |
| Blank diagram | Missing root cells `id="0"` and `id="1"` | Ensure the basic mxGraphModel structure is complete |
| Edges not rendering | Edge mxCell is self-closing | Every edge must have `<mxGeometry relative="1" as="geometry"/>` |
| File won't open | No .drawio file association | Print the full file path so the user can open manually |
| Export fails | draw.io Desktop not installed | Keep the `.drawio` file, suggest installing draw.io Desktop |
