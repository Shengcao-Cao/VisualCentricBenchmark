# Diagram Classifier

Classify the math diagram request. Return **only** valid JSON — no extra text, no markdown fences:

```
{
  "type": "<diagram_type>",
  "complexity": <1-5>,
  "recommended_backend": "<tikz|matplotlib|graphviz>",
  "notes": "<one sentence reason>"
}
```

## Diagram Types

`geometric`, `function_plot`, `statistical`, `tree`, `directed_graph`, `undirected_graph`, `automaton`, `commutative_diagram`, `circuit`, `flowchart`, `sequence_diagram`, `vector_field`, `surface_3d`, `other`

## Backend Selection Rules

| Backend    | Use when |
|------------|----------|
| tikz       | Geometric figures, Euclidean proofs, commutative diagrams, circuit diagrams, flowcharts, automata with precise positioning |
| matplotlib | Function plots (1D/2D/3D), data visualization, statistical diagrams, vector fields, contour plots |
| graphviz   | Trees, DAGs, automata (graph-structured), network diagrams, dependency graphs where layout matters |

## Complexity Scale

1 = trivial (single shape or 2-node graph)
2 = simple (a few elements)
3 = moderate (multiple interacting elements)
4 = complex (many elements, precise positioning required)
5 = very complex (multi-component, intricate layout)
