import math
import random

random.seed(42)  # For reproducible look


def rough_line(x1, y1, x2, y2, stroke_width=2, color="#000"):
    dx1, dy1 = random.uniform(-1, 1), random.uniform(-1, 1)
    dx2, dy2 = random.uniform(-1, 1), random.uniform(-1, 1)
    dx3, dy3 = random.uniform(-1, 1), random.uniform(-1, 1)
    dx4, dy4 = random.uniform(-1, 1), random.uniform(-1, 1)

    path = f"M {x1+dx1} {y1+dy1} L {x2+dx2} {y2+dy2} M {x1+dx3} {y1+dy3} L {x2+dx4} {y2+dy4}"
    return f'<path d="{path}" stroke="{color}" stroke-width="{stroke_width}" fill="none" stroke-linecap="round" />'


def rough_rect(x, y, w, h, fill="none", stroke="#000", stroke_width=2):
    path1 = (
        f"M {x + random.uniform(-2, 2)} {y + random.uniform(-2, 2)} "
        f"L {x + w + random.uniform(-2, 2)} {y + random.uniform(-2, 2)} "
        f"L {x + w + random.uniform(-2, 2)} {y + h + random.uniform(-2, 2)} "
        f"L {x + random.uniform(-2, 2)} {y + h + random.uniform(-2, 2)} Z"
    )
    path2 = (
        f"M {x + random.uniform(-2, 2)} {y + random.uniform(-2, 2)} "
        f"L {x + w + random.uniform(-2, 2)} {y + random.uniform(-2, 2)} "
        f"L {x + w + random.uniform(-2, 2)} {y + h + random.uniform(-2, 2)} "
        f"L {x + random.uniform(-2, 2)} {y + h + random.uniform(-2, 2)} Z"
    )
    return (
        f'<path d="{path1} {path2}" stroke="{stroke}" stroke-width="{stroke_width}" '
        f'fill="{fill}" stroke-linejoin="round" stroke-linecap="round" />'
    )


def curve_arrow(x1, y1, cx, cy, x2, y2, color="#000"):
    path1 = (
        f"M {x1 + random.uniform(-1, 1)} {y1 + random.uniform(-1, 1)} "
        f"Q {cx + random.uniform(-1, 1)} {cy + random.uniform(-1, 1)} "
        f"{x2 + random.uniform(-1, 1)} {y2 + random.uniform(-1, 1)}"
    )
    path2 = (
        f"M {x1 + random.uniform(-1, 1)} {y1 + random.uniform(-1, 1)} "
        f"Q {cx + random.uniform(-1, 1)} {cy + random.uniform(-1, 1)} "
        f"{x2 + random.uniform(-1, 1)} {y2 + random.uniform(-1, 1)}"
    )

    t = 1.0
    dx = 2 * (1 - t) * (cx - x1) + 2 * t * (x2 - cx)
    dy = 2 * (1 - t) * (cy - y1) + 2 * t * (y2 - cy)
    angle = math.atan2(dy, dx)
    head_len = 15
    hx1 = x2 - head_len * math.cos(angle - math.pi / 6)
    hy1 = y2 - head_len * math.sin(angle - math.pi / 6)
    hx2 = x2 - head_len * math.cos(angle + math.pi / 6)
    hy2 = y2 - head_len * math.sin(angle + math.pi / 6)

    head1 = rough_line(x2, y2, hx1, hy1, stroke_width=2, color=color)
    head2 = rough_line(x2, y2, hx2, hy2, stroke_width=2, color=color)

    curve = f'<path d="{path1} {path2}" stroke="{color}" stroke-width="2" fill="none" stroke-linecap="round" />'
    return curve + "\n" + head1 + "\n" + head2


def text(
    x, y, content, font_size=20, font_weight="normal", anchor="start", fill="#1e1e1e"
):
    return (
        f'<text x="{x}" y="{y}" '
        f"font-family=\"'Caveat', 'Virgil', 'Comic Sans MS', cursive\" "
        f'font-size="{font_size}" font-weight="{font_weight}" '
        f'text-anchor="{anchor}" fill="{fill}">{content}</text>'
    )


svg = []
svg.append(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 650" '
    'width="100%" height="100%" style="background-color: #ffffff;">'
)
svg.append(
    '<style>@import url("https://fonts.googleapis.com/css2?family=Caveat:wght@400;600;700&amp;display=swap");</style>'
)

# Title
svg.append(
    text(
        500,
        50,
        "Run LLM on UCLH TRE - Data Flow",
        font_size=36,
        font_weight="700",
        anchor="middle",
    )
)

# Engine Box
svg.append(
    rough_rect(380, 200, 240, 260, fill="#f3e8ff", stroke="#6b21a8", stroke_width=3)
)
svg.append(
    text(
        500,
        250,
        "run.py",
        font_size=32,
        font_weight="700",
        anchor="middle",
        fill="#6b21a8",
    )
)
svg.append(text(500, 285, "(vLLM Batch", font_size=22, anchor="middle", fill="#6b21a8"))
svg.append(text(500, 310, "Inference)", font_size=22, anchor="middle", fill="#6b21a8"))
svg.append(rough_line(400, 330, 600, 330, stroke_width=2, color="#6b21a8"))
svg.append(text(500, 365, "1. Load Config", font_size=20, anchor="middle"))
svg.append(text(500, 395, "2. Format Prompts", font_size=20, anchor="middle"))
svg.append(text(500, 425, "3. Generate Text", font_size=20, anchor="middle"))

# Inputs
svg.append(
    rough_rect(60, 140, 240, 110, fill="#eff6ff", stroke="#1d4ed8", stroke_width=2)
)
svg.append(
    text(
        180,
        180,
        "Input Data",
        font_size=26,
        font_weight="700",
        anchor="middle",
        fill="#1d4ed8",
    )
)
svg.append(text(180, 220, "data/example_input.csv", font_size=20, anchor="middle"))
svg.append(text(180, 240, "(id, text)", font_size=16, anchor="middle"))

svg.append(
    rough_rect(60, 290, 240, 120, fill="#fefce8", stroke="#a16207", stroke_width=2)
)
svg.append(
    text(
        180,
        330,
        "Configuration",
        font_size=26,
        font_weight="700",
        anchor="middle",
        fill="#a16207",
    )
)
svg.append(text(180, 365, "config.yaml", font_size=20, anchor="middle"))
svg.append(text(180, 395, "prompt.py", font_size=20, anchor="middle"))

svg.append(
    rough_rect(60, 450, 240, 100, fill="#fdf2f8", stroke="#be185d", stroke_width=2)
)
svg.append(
    text(
        180,
        490,
        "Local Model",
        font_size=26,
        font_weight="700",
        anchor="middle",
        fill="#be185d",
    )
)
svg.append(text(180, 525, "models/&lt;model_name&gt;", font_size=20, anchor="middle"))

# Arrows
svg.append(curve_arrow(310, 195, 350, 200, 375, 230, color="#1d4ed8"))
svg.append(curve_arrow(310, 350, 340, 350, 375, 330, color="#a16207"))
svg.append(curve_arrow(310, 500, 350, 500, 375, 430, color="#be185d"))

# Outputs
svg.append(
    rough_rect(700, 220, 260, 220, fill="#f0fdf4", stroke="#15803d", stroke_width=2)
)
svg.append(
    text(
        830,
        260,
        "Outputs",
        font_size=28,
        font_weight="700",
        anchor="middle",
        fill="#15803d",
    )
)
svg.append(text(830, 295, "outputs/&lt;timestamp&gt;/", font_size=20, anchor="middle"))
svg.append(rough_line(720, 320, 940, 320, stroke_width=2, color="#15803d"))
svg.append(text(720, 360, "📄 output.csv", font_size=22, anchor="start"))
svg.append(text(745, 385, "(id, text, prompt, output)", font_size=16, anchor="start"))
svg.append(text(720, 415, "⚙️ config.yaml", font_size=22, anchor="start"))

svg.append(curve_arrow(630, 330, 660, 330, 690, 330, color="#15803d"))

svg.append("</svg>")

with open("data_flow.svg", "w") as f:
    f.write("\n".join(svg))
