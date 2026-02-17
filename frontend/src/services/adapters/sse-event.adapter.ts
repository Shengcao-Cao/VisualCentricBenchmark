export function toolLabel(tool: string): string {
  if (tool === "classify_diagram") return "Classify prompt and choose backend";
  if (tool === "render_tikz") return "Render with TikZ";
  if (tool === "render_matplotlib") return "Render with Matplotlib";
  if (tool === "render_graphviz") return "Render with Graphviz";
  if (tool === "validate_visual") return "Validate and score output";
  if (tool === "save_diagram") return "Save final output";
  return tool;
}

export function backendFromTool(tool: string): "tikz" | "matplotlib" | "graphviz" | "unknown" {
  if (tool === "render_tikz") return "tikz";
  if (tool === "render_matplotlib") return "matplotlib";
  if (tool === "render_graphviz") return "graphviz";
  return "unknown";
}

