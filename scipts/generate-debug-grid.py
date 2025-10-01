# Grid + border with major and dotted minor lines in ONE Dialogue line.
# Inset: 620x480 at \pos(170,30). Major: every 60px (rows) / 40px (cols).
# Minor (half-step): every 30px (rows) / 20px (cols), dotted and thinner.

# ---- Tunables ----
W, H = 620, 480
POS_X, POS_Y = 170, 30

STEP_Y = 60  # major row step (36+24)
STEP_X = 40  # major column step (36+4)
HALF_Y = STEP_Y // 2  # 30
HALF_X = STEP_X // 2  # 20

# Major line style
MAJOR_BORD = 1.2
MAJOR_COLOR = "&H00FFFF&"  # cyan

# Minor line style
MINOR_BORD = 0.6
MINOR_COLOR = "&H808080&"  # gray

# Dots for minors
DASH_LEN = 6
GAP_LEN = 6

DUR_START = "0:00:00.00"
DUR_END = "2:00:00.00"
STYLE = "normal"
# -------------------


def seg(x1, y1, x2, y2):
    return f"m {x1} {y1} l {x2} {y2} "


def dotted_h(y, x0, x1, dash, gap):
    parts, x = [], x0
    while x < x1:
        x2 = min(x + dash, x1)
        parts.append(seg(x, y, x2, y))
        x = x2 + gap
    return "".join(parts)


def dotted_v(x, y0, y1, dash, gap):
    parts, y = [], y0
    while y < y1:
        y2 = min(y + dash, y1)
        parts.append(seg(x, y, x, y2))
        y = y2 + gap
    return "".join(parts)


# --- Build major path (outer border + major grid) ---
maj = []
# border
maj += [
    seg(0, 0, W, 0),  # top
    seg(W, 0, W, H),  # right
    seg(W, H, 0, H),  # bottom
    seg(0, H, 0, 0),  # left
]
# major horizontals every 60
y = STEP_Y
while y < H:
    maj.append(seg(0, y, W, y))
    y += STEP_Y
# major verticals every 40
x = STEP_X
while x < W:
    maj.append(seg(x, 0, x, H))
    x += STEP_X
major_path = "".join(maj)

# --- Build minor path (half-steps, dotted) ---
minr = []
# minor horizontals every 30
y = HALF_Y
while y < H:
    minr.append(dotted_h(y, 0, W, DASH_LEN, GAP_LEN))
    y += STEP_Y
# minor verticals every 20
x = HALF_X
while x < W:
    minr.append(dotted_v(x, 0, H, DASH_LEN, GAP_LEN))
    x += STEP_X
minor_path = "".join(minr)

# Dialogue for majors
ass_major = (
    f"Dialogue: 0,{DUR_START},{DUR_END},{STYLE},,0,0,0,,"
    f"{{\\an7\\pos({POS_X},{POS_Y})\\p1\\shad0\\1a&HFF&\\3a&H00&\\bord{MAJOR_BORD}\\3c{MAJOR_COLOR}}}"  # noqa: E501
    + major_path
    + "{\\p0}"
)

# Dialogue for minors
ass_minor = (
    f"Dialogue: 0,{DUR_START},{DUR_END},{STYLE},,0,0,0,,"
    f"{{\\an7\\pos({POS_X},{POS_Y})\\p1\\shad0\\1a&HFF&\\3a&H00&\\bord{MINOR_BORD}\\3c{MINOR_COLOR}}}"  # noqa: E501
    + minor_path
    + "{\\p0}"
)

print(repr(ass_major))
print(repr(ass_minor))
