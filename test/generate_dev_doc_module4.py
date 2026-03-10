import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


ROOT = Path(r"D:\project\AI\ImageIdentification")
OUT_DIR = ROOT / "test"
ASSET_DIR = OUT_DIR / "dev_doc_assets"
DOC_PATH = Path(os.environ.get("DOC_OUT", str(OUT_DIR / "灵犀智影-项目开发文档.docx")))

FONT_UI = Path(r"C:\Windows\Fonts\msyh.ttc")
FONT_UI_BOLD = Path(r"C:\Windows\Fonts\simhei.ttf")


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    font_path = FONT_UI_BOLD if bold else FONT_UI
    return ImageFont.truetype(str(font_path), size=size)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int):
    lines = []
    current = ""
    for ch in text:
        test = current + ch
        width = draw.textbbox((0, 0), test, font=font)[2]
        if width <= max_width or not current:
            current = test
        else:
            lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def draw_text_center(draw: ImageDraw.ImageDraw, text: str, rect, font, fill=(0, 0, 0)):
    x0, y0, x1, y1 = rect
    lines = wrap_text(draw, text, font, x1 - x0 - 12)
    line_h = draw.textbbox((0, 0), "测", font=font)[3] + 2
    total_h = len(lines) * line_h
    y = y0 + (y1 - y0 - total_h) // 2
    for line in lines:
        w = draw.textbbox((0, 0), line, font=font)[2]
        x = x0 + (x1 - x0 - w) // 2
        draw.text((x, y), line, font=font, fill=fill)
        y += line_h


def draw_number(draw: ImageDraw.ImageDraw, num: int, x: int, y: int):
    r = 15
    draw.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255), outline=(0, 0, 0), width=2)
    font = get_font(16, bold=True)
    txt = str(num)
    bbox = draw.textbbox((0, 0), txt, font=font)
    draw.text((x - (bbox[2] // 2), y - 11), txt, fill=(0, 0, 0), font=font)


def draw_text_left_multiline(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    max_width: int,
    font: ImageFont.FreeTypeFont,
    fill=(0, 0, 0),
    line_gap=4,
    max_lines=None,
):
    if not text:
        return y

    lines = wrap_text(draw, text, font, max_width)
    if max_lines is not None:
        lines = lines[: max(0, max_lines)]

    line_h = draw.textbbox((0, 0), "Ag", font=font)[3] + line_gap
    cursor = y
    for line in lines:
        draw.text((x, cursor), line, font=font, fill=fill)
        cursor += line_h
    return cursor


def draw_widget(draw: ImageDraw.ImageDraw, widget):
    x, y, w, h = widget["rect"]
    kind = widget.get("kind", "panel")
    text = widget.get("text", "")
    subtext = widget.get("subtext", "")

    if kind == "input":
        draw.rectangle((x, y, x + w, y + h), fill=(255, 255, 255), outline=(0, 0, 0), width=2)
        draw.ellipse((x + 14, y + h // 2 - 8, x + 30, y + h // 2 + 8), outline=(0, 0, 0), width=2)
        draw.text((x + 40, y + h // 2 - 11), text, font=get_font(20), fill=(80, 80, 80))
    elif kind == "button_primary":
        draw.rectangle((x, y, x + w, y + h), fill=(238, 238, 238), outline=(0, 0, 0), width=2)
        draw_text_center(draw, text, (x, y, x + w, y + h), get_font(20, bold=True), fill=(0, 0, 0))
    elif kind == "button_secondary":
        draw.rectangle((x, y, x + w, y + h), fill=(255, 255, 255), outline=(0, 0, 0), width=2)
        draw_text_center(draw, text, (x, y, x + w, y + h), get_font(19, bold=True), fill=(0, 0, 0))
    elif kind == "chip":
        draw.rectangle((x, y, x + w, y + h), fill=(245, 245, 245), outline=(0, 0, 0), width=2)
        draw_text_center(draw, text, (x, y, x + w, y + h), get_font(18), fill=(0, 0, 0))
    elif kind == "tab":
        draw.rectangle((x, y, x + w, y + h), fill=(250, 250, 250), outline=(0, 0, 0), width=2)
        draw_text_center(draw, text, (x, y, x + w, y + h), get_font(18), fill=(0, 0, 0))
    elif kind == "card":
        draw.rectangle((x, y, x + w, y + h), fill=(255, 255, 255), outline=(0, 0, 0), width=2)
        title_font = get_font(19, bold=True)
        body_font = get_font(16)
        title_h = draw.textbbox((0, 0), "Ag", font=title_font)[3] + 4
        body_h = draw.textbbox((0, 0), "Ag", font=body_font)[3] + 4

        top = y + 10
        max_title_lines = 2 if h >= 86 else 1
        top = draw_text_left_multiline(
            draw,
            text,
            x + 14,
            top,
            w - 28,
            title_font,
            fill=(0, 0, 0),
            line_gap=4,
            max_lines=max_title_lines,
        )

        if subtext:
            available_h = max(0, (y + h - 14) - top)
            max_sub_lines = max(1, available_h // max(1, body_h))
            draw_text_left_multiline(
                draw,
                subtext,
                x + 14,
                top,
                w - 28,
                body_font,
                fill=(60, 60, 60),
                line_gap=3,
                max_lines=max_sub_lines,
            )

        # Only draw placeholder lines when the card is tall enough.
        if h >= 88:
            yline = y + h - 16
            draw.line((x + 14, yline, x + w - 14, yline), fill=(170, 170, 170), width=1)
            draw.line((x + 14, yline - 10, x + w - 120, yline - 10), fill=(170, 170, 170), width=1)
    elif kind == "panel_dark":
        draw.rectangle((x, y, x + w, y + h), fill=(245, 245, 245), outline=(0, 0, 0), width=2)
        draw_text_left_multiline(draw, text, x + 16, y + 12, w - 32, get_font(18, bold=True), fill=(0, 0, 0), line_gap=3, max_lines=2)
        draw.line((x + 20, y + h - 30, x + w - 20, y + h - 30), fill=(140, 140, 140), width=1)
    elif kind == "chat_left":
        draw.rectangle((x, y, x + w, y + h), fill=(255, 255, 255), outline=(0, 0, 0), width=2)
        draw_text_left_multiline(draw, text, x + 12, y + 10, w - 24, get_font(16), fill=(0, 0, 0), line_gap=2, max_lines=2)
    elif kind == "chat_right":
        draw.rectangle((x, y, x + w, y + h), fill=(245, 245, 245), outline=(0, 0, 0), width=2)
        draw_text_left_multiline(draw, text, x + 12, y + 10, w - 24, get_font(16), fill=(0, 0, 0), line_gap=2, max_lines=2)
    elif kind == "list_row":
        draw.rectangle((x, y, x + w, y + h), fill=(255, 255, 255), outline=(0, 0, 0), width=1)
        if subtext:
            draw_text_left_multiline(draw, text, x + 14, y + 7, w - 28, get_font(17, bold=True), fill=(0, 0, 0), line_gap=2, max_lines=1)
            draw_text_left_multiline(draw, subtext, x + 14, y + 33, w - 28, get_font(15), fill=(70, 70, 70), line_gap=2, max_lines=2)
        else:
            draw_text_center(draw, text, (x + 12, y + 2, x + w - 12, y + h - 2), get_font(17, bold=True), fill=(0, 0, 0))
    else:
        draw.rectangle((x, y, x + w, y + h), fill=(250, 250, 250), outline=(0, 0, 0), width=2)
        draw_text_center(draw, text, (x, y, x + w, y + h), get_font(18), fill=(0, 0, 0))


def create_prototype(path: Path, title: str, page_title: str, components, widgets):
    img = Image.new("RGB", (1880, 1080), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    draw.text((58, 24), title, font=get_font(40, bold=True), fill=(0, 0, 0))
    draw.text((58, 74), "（低保真原型示意，组件位置按实际页面结构标注）", font=get_font(18), fill=(80, 80, 80))

    shell_x, shell_y, shell_w, shell_h = 70, 92, 1080, 940
    draw.rectangle((shell_x, shell_y, shell_x + shell_w, shell_y + shell_h), outline=(0, 0, 0), width=3, fill=(255, 255, 255))

    screen_x, screen_y, screen_w, screen_h = shell_x + 45, shell_y + 38, shell_w - 90, shell_h - 80
    draw.rounded_rectangle(
        (screen_x, screen_y, screen_x + screen_w, screen_y + screen_h),
        radius=2,
        outline=(0, 0, 0),
        width=2,
        fill=(255, 255, 255),
    )
    draw.rectangle((screen_x, screen_y, screen_x + screen_w, screen_y + 34), fill=(245, 245, 245), outline=(0, 0, 0), width=1)
    draw.text((screen_x + 14, screen_y + 8), "09:41", font=get_font(14), fill=(0, 0, 0))
    draw.rectangle((screen_x + screen_w - 108, screen_y + 9, screen_x + screen_w - 22, screen_y + 22), fill=(220, 220, 220), outline=(0, 0, 0), width=1)
    draw.rectangle((screen_x, screen_y + 34, screen_x + screen_w, screen_y + 102), fill=(250, 250, 250), outline=(0, 0, 0), width=1)
    draw.text((screen_x + 22, screen_y + 56), page_title, font=get_font(30, bold=True), fill=(0, 0, 0))

    for widget in widgets:
        wx, wy, ww, wh = widget["rect"]
        abs_widget = dict(widget)
        abs_widget["rect"] = (screen_x + wx, screen_y + wy, ww, wh)
        draw_widget(draw, abs_widget)

    marker_positions = []
    for comp in components:
        x, y, w, h = comp["rect"]
        ax, ay = screen_x + x, screen_y + y
        draw.rectangle((ax, ay, ax + w, ay + h), outline=(0, 0, 0), width=2)

        # Place number markers in the left gutter and avoid marker collisions.
        marker_x = ax - 10
        marker_y = ay + min(14, max(10, h // 4))
        for _ in range(8):
            collided = False
            for ex, ey in marker_positions:
                if abs(marker_x - ex) < 80 and abs(marker_y - ey) < 34:
                    marker_y = ey + 34
                    collided = True
            if not collided:
                break
        marker_positions.append((marker_x, marker_y))
        draw_number(draw, comp["id"], marker_x, marker_y)

    note_x, note_y = 1200, 125
    draw.rectangle((note_x, note_y, 1810, 980), outline=(0, 0, 0), width=2, fill=(255, 255, 255))
    draw.text((note_x + 26, note_y + 20), "组件注解", font=get_font(34, bold=True), fill=(0, 0, 0))

    y = note_y + 70
    for comp in components:
        bullet = f"{comp['id']}. {comp['name']}：{comp['note']}"
        lines = wrap_text(draw, bullet, get_font(21), 560)
        for line in lines:
            draw.text((note_x + 24, y), line, font=get_font(22), fill=(35, 43, 58))
            y += 34
        y += 8

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def create_use_case(path: Path):
    img = Image.new("RGB", (2100, 1320), (245, 248, 253))
    draw = ImageDraw.Draw(img)
    title_font = get_font(46, bold=True)
    draw.text((55, 26), "图 4.1 系统用例图（灵犀智影）", font=title_font, fill=(18, 38, 66))
    draw.text((58, 92), "参与者、核心业务用例及关键 include / extend 关系", font=get_font(23), fill=(72, 90, 120))

    system_rect = (380, 150, 1700, 1180)
    draw.rounded_rectangle(system_rect, radius=24, outline=(46, 78, 120), width=4, fill=(251, 253, 255))
    draw.rectangle((380, 150, 1700, 212), fill=(230, 239, 252))
    draw.text((410, 168), "灵犀智影系统边界", font=get_font(32, bold=True), fill=(36, 73, 120))

    def draw_actor(x, y, title):
        draw.ellipse((x - 24, y - 82, x + 24, y - 34), outline=(34, 34, 34), width=3)
        draw.line((x, y - 34, x, y + 46), fill=(34, 34, 34), width=3)
        draw.line((x - 44, y + 2, x + 44, y + 2), fill=(34, 34, 34), width=3)
        draw.line((x, y + 46, x - 34, y + 98), fill=(34, 34, 34), width=3)
        draw.line((x, y + 46, x + 34, y + 98), fill=(34, 34, 34), width=3)
        draw.text((x - 68, y + 120), title, font=get_font(26, bold=True), fill=(20, 20, 20))

    def draw_service(x, y, title):
        draw.rounded_rectangle((x - 140, y - 56, x + 140, y + 56), radius=16, fill=(239, 245, 255), outline=(83, 118, 168), width=3)
        draw_text_center(draw, title, (x - 132, y - 46, x + 132, y + 46), get_font(22, bold=True), fill=(33, 65, 108))

    draw_actor(175, 360, "放疗医生")
    draw_actor(175, 820, "会诊专家")
    draw_service(1900, 430, "AI 分割推理服务")
    draw_service(1900, 860, "对象存储服务")

    use_cases = {
        "UC01 用户登录": (510, 270, 840, 342),
        "UC02 用户注册": (900, 270, 1230, 342),
        "UC03 患者建档": (1290, 270, 1620, 342),
        "UC04 患者检索": (510, 400, 840, 472),
        "UC05 影像上传与序列管理": (900, 400, 1230, 472),
        "UC06 多模态分割触发": (1290, 400, 1620, 472),
        "UC07 GTV/CTV 精修": (510, 530, 840, 602),
        "UC08 CTV 外扩与热图评估": (900, 530, 1230, 602),
        "UC09 三维模型浏览": (1290, 530, 1620, 602),
        "UC10 会诊会话管理": (510, 660, 840, 732),
        "UC11 会诊消息与附件": (900, 660, 1230, 732),
        "UC12 智能助手问答": (1290, 660, 1620, 732),
        "UC13 结果导出与审计": (900, 790, 1230, 862),
    }

    for name, rect in use_cases.items():
        draw.ellipse(rect, outline=(86, 109, 149), width=3, fill=(240, 246, 255))
        draw_text_center(draw, name, rect, get_font(22, bold=True), fill=(19, 39, 69))

    def arrow(x1, y1, x2, y2, color=(72, 95, 138), width=2):
        draw.line((x1, y1, x2, y2), fill=color, width=width)
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            return
        l = (dx ** 2 + dy ** 2) ** 0.5
        ux, uy = dx / l, dy / l
        px, py = -uy, ux
        size = 12
        p1 = (x2, y2)
        p2 = (x2 - int(size * ux + size * 0.6 * px), y2 - int(size * uy + size * 0.6 * py))
        p3 = (x2 - int(size * ux - size * 0.6 * px), y2 - int(size * uy - size * 0.6 * py))
        draw.polygon([p1, p2, p3], fill=color)

    def connect_actor(actor_x, actor_y, case_key, side="left"):
        rx0, ry0, rx1, ry1 = use_cases[case_key]
        target = (rx0, (ry0 + ry1) // 2) if side == "left" else (rx1, (ry0 + ry1) // 2)
        arrow(actor_x, actor_y, target[0], target[1], color=(85, 105, 143), width=2)

    # actor connections
    for uc in ["UC01 用户登录", "UC03 患者建档", "UC04 患者检索", "UC05 影像上传与序列管理", "UC06 多模态分割触发", "UC07 GTV/CTV 精修", "UC08 CTV 外扩与热图评估", "UC09 三维模型浏览", "UC13 结果导出与审计"]:
        connect_actor(220, 360, uc, "left")
    for uc in ["UC10 会诊会话管理", "UC11 会诊消息与附件", "UC12 智能助手问答", "UC09 三维模型浏览", "UC13 结果导出与审计"]:
        connect_actor(220, 820, uc, "left")

    # external services
    connect_actor(1760, 430, "UC06 多模态分割触发", "right")
    connect_actor(1760, 430, "UC08 CTV 外扩与热图评估", "right")
    connect_actor(1760, 860, "UC05 影像上传与序列管理", "right")
    connect_actor(1760, 860, "UC11 会诊消息与附件", "right")
    connect_actor(1760, 860, "UC13 结果导出与审计", "right")

    # include/extend lines
    arrow(1230, 436, 1290, 566, color=(120, 137, 167), width=2)  # UC06 -> UC08
    draw.text((1218, 490), "<<include>>", font=get_font(18), fill=(102, 118, 150))
    arrow(840, 566, 900, 566, color=(120, 137, 167), width=2)  # UC07 -> UC08
    draw.text((848, 536), "<<extend>>", font=get_font(18), fill=(102, 118, 150))
    arrow(840, 696, 900, 696, color=(120, 137, 167), width=2)  # UC10 -> UC11
    draw.text((846, 666), "<<include>>", font=get_font(18), fill=(102, 118, 150))
    arrow(1230, 696, 1290, 696, color=(120, 137, 167), width=2)  # UC11 -> UC12
    draw.text((1238, 666), "<<extend>>", font=get_font(18), fill=(102, 118, 150))

    legend = (1500, 1045, 2020, 1240)
    draw.rounded_rectangle(legend, radius=14, fill=(249, 252, 255), outline=(150, 170, 202), width=2)
    draw.text((1520, 1065), "图例说明", font=get_font(24, bold=True), fill=(39, 68, 111))
    draw.line((1525, 1110, 1630, 1110), fill=(85, 105, 143), width=2)
    draw.text((1645, 1097), "参与者与用例关联", font=get_font(18), fill=(56, 76, 105))
    draw.line((1525, 1145, 1630, 1145), fill=(120, 137, 167), width=2)
    draw.text((1645, 1132), "<<include>> / <<extend>>", font=get_font(18), fill=(56, 76, 105))

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def create_module_structure(path: Path):
    img = Image.new("RGB", (2200, 1380), (245, 248, 253))
    draw = ImageDraw.Draw(img)
    draw.text((58, 30), "图 4.2 功能模块结构图", font=get_font(46, bold=True), fill=(17, 34, 58))
    draw.text((58, 96), "按“入口层-业务层-能力层-支撑层”组织，无重叠布局", font=get_font(23), fill=(72, 90, 120))

    def box(rect, text, fill=(243, 248, 255), outline=(81, 109, 151), size=24):
        draw.rounded_rectangle(rect, radius=16, fill=fill, outline=outline, width=3)
        draw_text_center(draw, text, rect, get_font(size, bold=True), fill=(21, 43, 79))

    root = (840, 150, 1360, 240)
    box(root, "灵犀智影（NeoVision）", fill=(222, 236, 255), size=30)

    level1 = [
        ("账户权限域", (90, 320, 410, 405)),
        ("患者影像域", (510, 320, 830, 405)),
        ("靶区算法域", (930, 320, 1250, 405)),
        ("会诊协同域", (1350, 320, 1670, 405)),
        ("系统支撑域", (1770, 320, 2090, 405)),
    ]
    for _, rect in level1:
        draw.line(((root[0] + root[2]) // 2, root[3], (rect[0] + rect[2]) // 2, rect[1]), fill=(98, 126, 169), width=3)
    for name, rect in level1:
        box(rect, name, size=26)

    children = [
        (0, "登录/注册", (120, 500, 380, 570)),
        (0, "令牌鉴权", (120, 620, 380, 690)),
        (0, "个人中心", (120, 740, 380, 810)),
        (1, "患者建档", (540, 500, 800, 570)),
        (1, "患者检索", (540, 620, 800, 690)),
        (1, "影像序列管理", (540, 740, 800, 810)),
        (2, "多模态分割", (960, 500, 1220, 570)),
        (2, "GTV/CTV 精修", (960, 620, 1220, 690)),
        (2, "CTV 外扩与热图", (960, 740, 1220, 810)),
        (3, "会诊会话管理", (1380, 500, 1640, 570)),
        (3, "会诊消息协作", (1380, 620, 1640, 690)),
        (3, "智能助手问答", (1380, 740, 1640, 810)),
        (4, "3D 模型服务", (1800, 500, 2060, 570)),
        (4, "对象存储服务", (1800, 620, 2060, 690)),
        (4, "日志审计监控", (1800, 740, 2060, 810)),
    ]

    for pid, _, rect in children:
        pr = level1[pid][1]
        draw.line(((pr[0] + pr[2]) // 2, pr[3], (rect[0] + rect[2]) // 2, rect[1]), fill=(122, 146, 184), width=2)
    for _, name, rect in children:
        box(rect, name, fill=(251, 253, 255), outline=(129, 151, 188), size=21)

    capability_nodes = [
        ("热图评估子任务", (980, 940, 1190, 1004)),
        ("推理任务调度", (1210, 940, 1420, 1004)),
        ("多端消息分发", (1450, 940, 1660, 1004)),
        ("会诊材料归档", (1680, 940, 1890, 1004)),
    ]
    draw.text((900, 890), "能力扩展层", font=get_font(24, bold=True), fill=(51, 77, 117))
    for name, rect in capability_nodes:
        box(rect, name, fill=(239, 246, 255), outline=(114, 147, 192), size=19)
    draw.line((1090, 810, 1085, 940), fill=(120, 143, 181), width=2)
    draw.line((1090, 810, 1315, 940), fill=(120, 143, 181), width=2)
    draw.line((1510, 810, 1555, 940), fill=(120, 143, 181), width=2)
    draw.line((1930, 810, 1785, 940), fill=(120, 143, 181), width=2)

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)


def create_assets():
    use_case = ASSET_DIR / "fig_4_1_usecase.png"
    module_tree = ASSET_DIR / "fig_4_2_module_structure.png"
    create_use_case(use_case)
    create_module_structure(module_tree)

    # 4.4 prototypes
    create_prototype(
        ASSET_DIR / "fig_4_3_login.png",
        "登录与身份认证界面原型",
        "智影登录",
        [
            {"id": 1, "name": "顶部品牌信息区", "rect": (52, 122, 886, 132), "note": "展示“智影医生端”、副标题与能力标签。"},
            {"id": 2, "name": "账户输入框", "rect": (90, 372, 810, 62), "note": "输入手机号或工号，来自 wd-input 账户字段。"},
            {"id": 3, "name": "密码输入框", "rect": (90, 454, 810, 62), "note": "输入密码并进行长度校验。"},
            {"id": 4, "name": "进入工作台按钮", "rect": (90, 540, 810, 62), "note": "点击后执行登录校验并进入患者页。"},
            {"id": 5, "name": "注册新账号按钮", "rect": (90, 622, 810, 62), "note": "跳转到注册页（pages/auth/register）。"},
        ],
        [
            {"kind": "card", "rect": (52, 122, 886, 132), "text": "智影医生端  |  放疗影像智能勾画协作平台", "subtext": "标签：影像管理 / AI勾画 / 医生复核"},
            {"kind": "card", "rect": (52, 276, 886, 456), "text": "欢迎回来（安全加密）", "subtext": "使用注册手机号或工号登录"},
            {"kind": "input", "rect": (90, 372, 810, 62), "text": "请输入手机号或工号"},
            {"kind": "input", "rect": (90, 454, 810, 62), "text": "请输入密码"},
            {"kind": "button_primary", "rect": (90, 540, 810, 62), "text": "进入工作台"},
            {"kind": "button_secondary", "rect": (90, 622, 810, 62), "text": "注册新账号"},
        ],
    )

    create_prototype(
        ASSET_DIR / "fig_4_4_patient_list.png",
        "患者列表与检索界面原型",
        "患者列表",
        [
            {"id": 1, "name": "顶部检索区", "rect": (52, 122, 886, 130), "note": "包含问候信息与关键词检索输入框。"},
            {"id": 2, "name": "快捷操作区", "rect": (52, 270, 886, 170), "note": "“新建病例”“待复核任务”两张快捷卡片。"},
            {"id": 3, "name": "服务入口区", "rect": (52, 456, 886, 86), "note": "病例检索、影像上传、GTV、CTV、会诊入口。"},
            {"id": 4, "name": "患者列表区", "rect": (52, 590, 886, 210), "note": "展示患者卡片信息并可点击进入详情。"},
            {"id": 5, "name": "新增按钮", "rect": (778, 548, 160, 36), "note": "患者列表标题右侧“新增”按钮。"},
        ],
        [
            {"kind": "card", "rect": (52, 122, 886, 62), "text": "你好，张伟医生  |  放疗影像智能勾画工作台", "subtext": ""},
            {"kind": "input", "rect": (52, 188, 886, 64), "text": "查患者、病种、检查号"},
            {"kind": "button_secondary", "rect": (52, 270, 432, 76), "text": "新建病例"},
            {"kind": "button_secondary", "rect": (506, 270, 432, 76), "text": "待复核任务"},
            {"kind": "chip", "rect": (52, 364, 160, 48), "text": "病例检索"},
            {"kind": "chip", "rect": (228, 364, 160, 48), "text": "影像上传"},
            {"kind": "chip", "rect": (404, 364, 120, 48), "text": "GTV"},
            {"kind": "chip", "rect": (540, 364, 120, 48), "text": "CTV"},
            {"kind": "chip", "rect": (676, 364, 262, 48), "text": "会诊中心"},
            {"kind": "card", "rect": (52, 456, 886, 86), "text": "方案模板推荐（横向滚动）", "subtext": "脑胶质瘤模板 / 鼻咽癌模板 / 肺部肿瘤模板"},
            {"kind": "button_primary", "rect": (778, 548, 160, 36), "text": "新增"},
            {"kind": "card", "rect": (52, 590, 886, 98), "text": "赵海（男/58）   ID 1   影像号 10001", "subtext": "鼻咽癌 · T3N2M0 · 最近更新 10:26"},
            {"kind": "card", "rect": (52, 702, 886, 98), "text": "周雪（女/46）   ID 2   影像号 10002", "subtext": "喉癌 · T2N1M0 · 最近更新 09:48"},
        ],
    )

    create_prototype(
        ASSET_DIR / "fig_4_5_patient_detail.png",
        "患者详情与影像序列界面原型",
        "患者详情",
        [
            {"id": 1, "name": "患者概览头部卡", "rect": (52, 122, 886, 118), "note": "显示姓名、性别、年龄、分期及 KPI。"},
            {"id": 2, "name": "病例概览与方案操作", "rect": (52, 254, 886, 130), "note": "含确认方案、导出结构、删除患者按钮。"},
            {"id": 3, "name": "靶区 AI 结果区", "rect": (52, 398, 886, 156), "note": "GTV初稿、CTV外扩、CTV精修、热力图入口。"},
            {"id": 4, "name": "影像序列列表区", "rect": (52, 568, 886, 172), "note": "展示序列状态与模态上传标签。"},
            {"id": 5, "name": "序列操作按钮", "rect": (120, 744, 750, 54), "note": "上传影像、3D查看、更多。"},
        ],
        [
            {"kind": "card", "rect": (52, 122, 886, 118), "text": "赵海  男/58  T3N2M0  |  ID 1  影像号 10001", "subtext": "影像序列 3  ·  轮廓结果 2  ·  医生状态 待确认"},
            {"kind": "card", "rect": (52, 254, 886, 130), "text": "病例概览：鼻咽癌  |  最近更新 10:26", "subtext": "按钮：医生确认方案 / 导出结构 / 删除患者"},
            {"kind": "list_row", "rect": (52, 398, 886, 36), "text": "GTV 初稿  →", "subtext": ""},
            {"kind": "list_row", "rect": (52, 438, 886, 36), "text": "CTV 外扩  →", "subtext": ""},
            {"kind": "list_row", "rect": (52, 478, 886, 36), "text": "CTV 精修  →", "subtext": ""},
            {"kind": "list_row", "rect": (52, 518, 886, 36), "text": "热力图与CPDM  →", "subtext": ""},
            {"kind": "card", "rect": (52, 568, 886, 172), "text": "影像序列：CT/MR/PET-CT（含模态与Label状态）", "subtext": "每条序列含：状态标签、时间、模态上传状态"},
            {"kind": "button_secondary", "rect": (120, 744, 230, 54), "text": "上传影像"},
            {"kind": "button_secondary", "rect": (380, 744, 230, 54), "text": "3D 查看"},
            {"kind": "button_secondary", "rect": (640, 744, 230, 54), "text": "更多"},
        ],
    )

    create_prototype(
        ASSET_DIR / "fig_4_6_gtv_ctv.png",
        "GTV/CTV 标注与结果审核界面原型",
        "GTV 初稿 / CTV 精修",
        [
            {"id": 1, "name": "页面指标头部", "rect": (52, 122, 886, 118), "note": "显示当前序列、模态就绪数量与 GTV Label 状态。"},
            {"id": 2, "name": "序列模态检查区", "rect": (52, 254, 886, 148), "note": "按 Flair/T1/T1c/T2 展示上传状态并支持切换序列。"},
            {"id": 3, "name": "分割执行区", "rect": (52, 416, 886, 146), "note": "包含流程提示与 Flair 基础分割、多模态分割两个主操作。"},
            {"id": 4, "name": "结果状态区", "rect": (52, 576, 886, 84), "note": "显示分割结果是否已生成及可复核状态。"},
            {"id": 5, "name": "下载与归档区", "rect": (52, 672, 886, 88), "note": "提供“下载结果与源数据”统一入口。"},
        ],
        [
            {"kind": "card", "rect": (52, 122, 886, 118), "text": "GTV 初稿工作台 | 当前序列 Study-01", "subtext": "快速靶区分割与审核；模态就绪 4/4；GTV Label 已生成"},
            {"kind": "card", "rect": (52, 254, 886, 148), "text": "序列与模态检查", "subtext": "Flair:已上传  T1:已上传  T1c:已上传  T2:已上传（支持切换序列）"},
            {"kind": "card", "rect": (52, 416, 886, 146), "text": "分割执行（工作流）", "subtext": "1 检查模态  ->  2 执行分割  ->  3 下载复核"},
            {"kind": "chip", "rect": (120, 468, 220, 40), "text": "1 检查模态"},
            {"kind": "chip", "rect": (385, 468, 220, 40), "text": "2 执行分割"},
            {"kind": "chip", "rect": (650, 468, 220, 40), "text": "3 下载复核"},
            {"kind": "button_primary", "rect": (120, 514, 360, 42), "text": "Flair 基础分割"},
            {"kind": "button_secondary", "rect": (500, 514, 360, 42), "text": "多模态分割"},
            {"kind": "card", "rect": (52, 576, 886, 84), "text": "分割结果", "subtext": "状态：已生成，可下载 Label 并进入医生复核"},
            {"kind": "button_secondary", "rect": (120, 682, 750, 64), "text": "下载结果与源数据"},
        ],
    )

    create_prototype(
        ASSET_DIR / "fig_4_7_ctv_heatmap.png",
        "CTV 外扩与热力图校核界面原型",
        "CTV 外扩 / 热力图与 CPDM",
        [
            {"id": 1, "name": "页面指标头部", "rect": (52, 122, 886, 118), "note": "显示序列号、模态就绪数量、热力图状态。"},
            {"id": 2, "name": "序列模态检查区", "rect": (52, 254, 886, 144), "note": "列出 Flair/T1/T1c/T2 上传状态。"},
            {"id": 3, "name": "热力图生成区", "rect": (52, 412, 886, 174), "note": "包含流程步骤、生成按钮、下载按钮。"},
            {"id": 4, "name": "CPDM 操作区", "rect": (52, 600, 886, 106), "note": "完成输入文件选择、上传提交与下载图片操作。"},
            {"id": 5, "name": "结果预览区", "rect": (52, 718, 886, 90), "note": "显示热力图/CPDM 生成图片预览。"},
        ],
        [
            {"kind": "card", "rect": (52, 122, 886, 118), "text": "热力图与CPDM工作台", "subtext": "当前序列 Study-01  ·  模态就绪 4/4  ·  热力图状态 未生成"},
            {"kind": "card", "rect": (52, 254, 886, 144), "text": "序列与模态检查", "subtext": "Flair:已上传  T1:已上传  T1c:已上传  T2:已上传"},
            {"kind": "card", "rect": (52, 412, 886, 174), "text": "热力图生成", "subtext": "步骤：检查模态→生成热图→下载归档"},
            {"kind": "button_primary", "rect": (120, 520, 360, 52), "text": "生成热力图"},
            {"kind": "button_secondary", "rect": (500, 520, 360, 52), "text": "下载热力图"},
            {"kind": "card", "rect": (52, 600, 886, 106), "text": "CPDM 预测", "subtext": "已选输入：T1/xxx.nrrd；状态：待提交"},
            {"kind": "button_secondary", "rect": (120, 660, 220, 34), "text": "选择文件"},
            {"kind": "button_primary", "rect": (368, 660, 220, 34), "text": "上传"},
            {"kind": "button_secondary", "rect": (616, 660, 244, 34), "text": "下载图片"},
            {"kind": "panel_dark", "rect": (52, 718, 886, 90), "text": "结果预览"},
        ],
    )

    create_prototype(
        ASSET_DIR / "fig_4_8_3d_viewer.png",
        "三维模型浏览界面原型",
        "3D 模型浏览",
        [
            {"id": 1, "name": "三维查看窗口", "rect": (52, 246, 886, 306), "note": "glwrap 区域，用于 WebGL 三维渲染显示。"},
            {"id": 2, "name": "参数滑条区", "rect": (52, 566, 886, 184), "note": "阈值、点大小、不透明度、最大点数四组滑条。"},
            {"id": 3, "name": "重建按钮", "rect": (120, 756, 340, 52), "note": "点击执行点云重建（rebuildPoints）。"},
            {"id": 4, "name": "重置视角按钮", "rect": (520, 756, 340, 52), "note": "点击重置摄像机视角（resetView）。"},
            {"id": 5, "name": "操作提示区", "rect": (52, 162, 886, 72), "note": "显示拖动旋转、双指缩放等手势说明。"},
        ],
        [
            {"kind": "card", "rect": (52, 122, 886, 34), "text": "3D重建", "subtext": ""},
            {"kind": "card", "rect": (52, 162, 886, 72), "text": "手势：拖动旋转，滚轮/双指缩放。", "subtext": ""},
            {"kind": "panel_dark", "rect": (52, 246, 886, 306), "text": "三维查看（WebGL 渲染区）"},
            {"kind": "card", "rect": (52, 566, 886, 40), "text": "阈值 slider  |  当前值", "subtext": ""},
            {"kind": "card", "rect": (52, 612, 886, 40), "text": "点大小 slider  |  当前值", "subtext": ""},
            {"kind": "card", "rect": (52, 658, 886, 40), "text": "不透明度 slider  |  当前值", "subtext": ""},
            {"kind": "card", "rect": (52, 704, 886, 40), "text": "最大点数 slider  |  当前值", "subtext": ""},
            {"kind": "button_primary", "rect": (120, 756, 340, 52), "text": "重建"},
            {"kind": "button_secondary", "rect": (520, 756, 340, 52), "text": "重置视角"},
        ],
    )

    create_prototype(
        ASSET_DIR / "fig_4_9_consultation.png",
        "联合会诊与消息协作界面原型",
        "会诊对话",
        [
            {"id": 1, "name": "顶部会话头部", "rect": (52, 122, 886, 76), "note": "返回按钮、头像、会诊标题、成员入口。"},
            {"id": 2, "name": "上下文标签条", "rect": (52, 206, 886, 42), "note": "显示“联合会诊/成员数/会话ID”等上下文。"},
            {"id": 3, "name": "消息列表区", "rect": (52, 256, 886, 426), "note": "展示会诊消息气泡、附件卡片与时间。"},
            {"id": 4, "name": "输入与发送区", "rect": (52, 738, 886, 72), "note": "加号附件按钮、输入框、发送按钮。"},
            {"id": 5, "name": "成员面板", "rect": (52, 688, 886, 40), "note": "展开后可查看成员并增删好友成员。"},
        ],
        [
            {"kind": "card", "rect": (52, 122, 886, 76), "text": "←  [头像]  赵海病例会诊（成员）", "subtext": "5 位医生协作中"},
            {"kind": "chip", "rect": (52, 206, 280, 42), "text": "联合会诊"},
            {"kind": "chip", "rect": (349, 206, 280, 42), "text": "成员 5"},
            {"kind": "chip", "rect": (646, 206, 292, 42), "text": "#10086"},
            {"kind": "card", "rect": (52, 256, 886, 426), "text": "消息列表（scroll-view）", "subtext": ""},
            {"kind": "chat_left", "rect": (84, 308, 500, 56), "text": "请重点关注咽后间隙边界。"},
            {"kind": "chat_right", "rect": (430, 384, 474, 56), "text": "已上传热力图，请查看附件。"},
            {"kind": "chat_left", "rect": (84, 460, 500, 56), "text": "建议 CTV 外扩 5mm。"},
            {"kind": "button_secondary", "rect": (52, 688, 886, 40), "text": "成员面板（展开/收起）"},
            {"kind": "button_secondary", "rect": (52, 738, 92, 72), "text": "+"},
            {"kind": "input", "rect": (160, 738, 596, 72), "text": "输入消息"},
            {"kind": "button_primary", "rect": (772, 738, 166, 72), "text": "发送"},
        ],
    )

    create_prototype(
        ASSET_DIR / "fig_4_10_mine.png",
        "个人中心与系统设置界面原型",
        "我的",
        [
            {"id": 1, "name": "个人信息区", "rect": (52, 122, 886, 136), "note": "头像、姓名、医院科室、账号信息。"},
            {"id": 2, "name": "统计区", "rect": (52, 272, 886, 84), "note": "已完成、我的会诊、医生好友三项统计。"},
            {"id": 3, "name": "医生好友入口", "rect": (74, 386, 842, 74), "note": "设置项“医生好友”。"},
            {"id": 4, "name": "会诊中心入口", "rect": (74, 476, 842, 74), "note": "设置项“进入会诊中心”。"},
            {"id": 5, "name": "退出登录入口", "rect": (74, 646, 842, 74), "note": "设置项“退出登录”。"},
        ],
        [
            {"kind": "card", "rect": (52, 122, 886, 136), "text": "头像  张伟医生", "subtext": "上海肿瘤医院 / 放疗科  ·  账号：13800000001"},
            {"kind": "chip", "rect": (52, 272, 286, 84), "text": "已完成 12"},
            {"kind": "chip", "rect": (352, 272, 286, 84), "text": "我的会诊 6"},
            {"kind": "chip", "rect": (652, 272, 286, 84), "text": "医生好友 18"},
            {"kind": "list_row", "rect": (74, 386, 842, 74), "text": "医生好友", "subtext": "搜索、添加和管理好友"},
            {"kind": "list_row", "rect": (74, 476, 842, 74), "text": "进入会诊中心", "subtext": "查看联合会诊与AI问答"},
            {"kind": "list_row", "rect": (74, 566, 842, 74), "text": "关于灵犀智影", "subtext": "面向放疗影像勾画的智能助手"},
            {"kind": "list_row", "rect": (74, 646, 842, 74), "text": "退出登录", "subtext": "返回登录页"},
        ],
    )


def set_run_font(run, east_asia="宋体", size=12, bold=False):
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), east_asia)
    run.font.size = Pt(size)
    run.bold = bold


def style_document(doc: Document):
    section = doc.sections[0]
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(2.54)
    section.right_margin = Cm(2.54)

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    normal.font.size = Pt(12)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.first_line_indent = Cm(0.74)

    for level, size in [(1, 16), (2, 14), (3, 12)]:
        style = doc.styles[f"Heading {level}"]
        style.font.name = "Times New Roman"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
        style.font.size = Pt(size)
        style.font.bold = True
        style.paragraph_format.line_spacing = 1.5
        style.paragraph_format.first_line_indent = Cm(0)


def add_center_paragraph(doc: Document, text: str, size=12, bold=False):
    p = doc.add_paragraph()
    p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing = 1.5
    r = p.add_run(text)
    set_run_font(r, east_asia="黑体" if bold else "宋体", size=size, bold=bold)
    return p


def add_body_paragraph(doc: Document, text: str, indent=True):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0.74) if indent else Cm(0)
    p.paragraph_format.line_spacing = 1.5
    r = p.add_run(text)
    set_run_font(r, east_asia="宋体", size=12, bold=False)
    return p


def add_heading(doc: Document, text: str, level: int):
    p = doc.add_paragraph(style=f"Heading {level}")
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing = 1.5
    r = p.add_run(text)
    set_run_font(r, east_asia="黑体", size=16 if level == 1 else 14 if level == 2 else 12, bold=True)
    return p


def add_caption(doc: Document, text: str):
    p = doc.add_paragraph()
    p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing = 1.5
    r = p.add_run(text)
    set_run_font(r, east_asia="宋体", size=11, bold=False)
    return p


def insert_image(doc: Document, path: Path, width_cm=15.5):
    doc.add_picture(str(path), width=Cm(width_cm))
    doc.paragraphs[-1].alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    doc.paragraphs[-1].paragraph_format.first_line_indent = Cm(0)


def set_cell_border(cell, top="8", bottom="8", left="8", right="8", color="000000"):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tc_borders = tcPr.find(qn("w:tcBorders"))
    if tc_borders is None:
        tc_borders = OxmlElement("w:tcBorders")
        tcPr.append(tc_borders)
    for edge, sz in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        elem = tc_borders.find(qn(f"w:{edge}"))
        if elem is None:
            elem = OxmlElement(f"w:{edge}")
            tc_borders.append(elem)
        elem.set(qn("w:val"), "single")
        elem.set(qn("w:sz"), sz)
        elem.set(qn("w:space"), "0")
        elem.set(qn("w:color"), color)


def set_cell_text(cell, text, *, bold=False, size=10.5, align=WD_PARAGRAPH_ALIGNMENT.LEFT):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing = 1.2
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(1)
    p.alignment = align
    r = p.add_run(str(text))
    set_run_font(r, east_asia="黑体" if bold else "宋体", size=size, bold=bold)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def add_table(doc: Document, caption: str, headers, rows, col_widths_cm=None, merge_first_col=False):
    add_caption(doc, caption)
    table = doc.add_table(rows=1, cols=len(headers), style="Table Grid")
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    if col_widths_cm:
        for i, w in enumerate(col_widths_cm):
            for row in table.rows:
                row.cells[i].width = Cm(w)

    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        set_cell_text(hdr_cells[i], h, bold=True, size=11, align=WD_PARAGRAPH_ALIGNMENT.CENTER)
        set_cell_border(hdr_cells[i], top="12", bottom="10", left="10", right="10")

    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            align = WD_PARAGRAPH_ALIGNMENT.LEFT if i == 2 else WD_PARAGRAPH_ALIGNMENT.CENTER
            set_cell_text(cells[i], value, bold=False, size=10.5, align=align)
            set_cell_border(cells[i], top="8", bottom="8", left="8", right="8")

    if col_widths_cm:
        for row in table.rows:
            for i, w in enumerate(col_widths_cm):
                row.cells[i].width = Cm(w)

    if merge_first_col and len(rows) > 1:
        start = 1
        while start < len(table.rows):
            current = table.rows[start].cells[0].text
            end = start
            while end + 1 < len(table.rows) and table.rows[end + 1].cells[0].text == current:
                end += 1
            if end > start:
                merged = table.rows[start].cells[0]
                for idx in range(start + 1, end + 1):
                    merged = merged.merge(table.rows[idx].cells[0])
                set_cell_text(merged, current, bold=False, size=10.5, align=WD_PARAGRAPH_ALIGNMENT.CENTER)
                set_cell_border(merged, top="8", bottom="8", left="8", right="8")
            start = end + 1

    return table


def add_cover(doc: Document):
    add_center_paragraph(doc, "第十五届全国大学生软件创新大赛", size=22, bold=True)
    add_center_paragraph(doc, "文档编号：SWC2022-T20220001-代码一定队", size=13, bold=False)
    doc.add_paragraph()
    add_center_paragraph(doc, "灵犀智影", size=32, bold=True)
    add_center_paragraph(doc, "NeoVision", size=18, bold=True)
    doc.add_paragraph()
    add_center_paragraph(doc, "项目开发文档", size=22, bold=True)
    add_center_paragraph(doc, "Version: 4.0.1", size=13, bold=False)
    for _ in range(8):
        doc.add_paragraph()
    add_center_paragraph(doc, "代码一定队", size=13, bold=False)
    add_center_paragraph(doc, "2022-3-21", size=13, bold=False)
    add_center_paragraph(doc, "All Rights Reserved", size=12, bold=False)
    doc.add_page_break()


def add_toc(doc: Document):
    add_center_paragraph(doc, "目录", size=18, bold=True)
    toc_entries = [
        (1, "4 需求分析"),
        (2, "4.1 数据需求"),
        (3, "4.1.1 静态数据"),
        (3, "4.1.2 动态数据"),
        (3, "4.1.3 数据词典"),
        (3, "4.1.4 数据采集"),
        (2, "4.2 功能需求"),
        (3, "4.2.1 项目功能用例图"),
        (3, "4.2.2 功能模块结构图"),
        (2, "4.3 性能需求"),
        (3, "4.3.1 时间特性"),
        (3, "4.3.2 适应性"),
        (2, "4.4 界面需求"),
        (3, "4.4.1 登录与身份认证界面"),
        (3, "4.4.2 患者列表与检索界面"),
        (3, "4.4.3 患者详情与影像序列界面"),
        (3, "4.4.4 GTV/CTV 标注与结果审核界面"),
        (3, "4.4.5 CTV 外扩与热力图校核界面"),
        (3, "4.4.6 三维模型浏览界面"),
        (3, "4.4.7 联合会诊与消息协作界面"),
        (3, "4.4.8 个人中心与系统设置界面"),
        (2, "4.5 接口需求"),
        (3, "4.5.1 硬件接口"),
        (3, "4.5.2 软件接口"),
        (2, "4.6 其他需求"),
        (3, "4.6.1 可使用性"),
        (3, "4.6.2 安全性"),
        (3, "4.6.3 可维护性"),
        (3, "4.6.4 可移植性"),
    ]
    for level, text in toc_entries:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.8 * (level - 1))
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.line_spacing = 1.5
        r = p.add_run(text)
        set_run_font(r, east_asia="宋体", size=12, bold=False)
    doc.add_page_break()


def add_content(doc: Document):
    add_heading(doc, "4 需求分析", 1)
    add_body_paragraph(
        doc,
        "本章为灵犀智影（NeoVision）项目在初赛阶段形成的需求分析结果，围绕数据、功能、性能、界面、接口及其他质量属性展开，覆盖系统当前版本的核心业务边界与实现约束。"
    )

    add_heading(doc, "4.1 数据需求", 2)

    add_heading(doc, "4.1.1 静态数据", 3)
    add_body_paragraph(
        doc,
        "静态数据包括系统运行期相对稳定的数据与配置项，主要由数据库结构定义（如 doctor_user、patient、patient_study、contour_result 等表结构）、环境配置文件（.env、服务地址、存储桶配置）、模型参数文件（如分割模型权重）及界面字典配置组成。该类数据变更频率低，主要在部署、升级或运维阶段调整。"
    )

    add_heading(doc, "4.1.2 动态数据", 3)
    add_body_paragraph(doc, "系统动态数据包括但不限于以下类别：")
    add_body_paragraph(doc, "① 医生与账号数据：登录状态、权限令牌、会话缓存、设备登录记录。")
    add_body_paragraph(doc, "② 患者业务数据：患者基本信息、诊断分期、主治医生关联、病程更新信息。")
    add_body_paragraph(doc, "③ 影像与算法数据：DICOM/NIfTI 序列上传记录、GTV/CTV/OAR 轮廓版本、置信度热力图与 CPDM 结果。")
    add_body_paragraph(doc, "④ 协同会诊数据：会诊会话、成员角色、文本消息、附件索引与交互时间轴。")
    add_body_paragraph(doc, "⑤ 审计与监控数据：关键操作日志、异常日志、接口耗时与任务执行状态。")

    add_heading(doc, "4.1.3 数据词典", 3)
    add_table(
        doc,
        "表 4.1 项目数据词典",
        ["分类", "名称", "定义", "类型"],
        [
            ["账号数据", "doctor_user.id", "医生用户唯一标识", "BIGINT"],
            ["账号数据", "doctor_user.mobile", "登录账号（手机号）", "VARCHAR(20)"],
            ["账号数据", "doctor_user.password_hash", "加密存储的密码摘要", "VARCHAR(255)"],
            ["患者数据", "patient.patient_no", "患者编号（业务唯一）", "VARCHAR(32)"],
            ["患者数据", "patient.name", "患者姓名", "VARCHAR(64)"],
            ["患者数据", "patient.stage", "肿瘤分期信息", "VARCHAR(32)"],
            ["患者数据", "patient.diagnosis", "诊断信息", "VARCHAR(128)"],
            ["影像数据", "patient_study.study_uid", "影像检查唯一号", "VARCHAR(128)"],
            ["影像数据", "patient_study.modality", "影像模态（CT/MR/PET-CT）", "VARCHAR(16)"],
            ["影像数据", "patient_study.status", "影像处理状态", "VARCHAR(32)"],
            ["轮廓数据", "contour_result.type", "轮廓类型（GTV/CTV/OAR）", "ENUM"],
            ["轮廓数据", "contour_result.version", "轮廓版本号", "INT"],
            ["轮廓数据", "contour_result.status", "轮廓审核状态", "VARCHAR(32)"],
            ["轮廓数据", "contour_result.storage_path", "轮廓文件存储地址", "VARCHAR(255)"],
            ["轮廓数据", "contour_result.confidence_map", "置信度热力图路径", "VARCHAR(255)"],
            ["文件数据", "file_upload.file_type", "文件类型（dicom/nii/mesh/rtstruct）", "VARCHAR(32)"],
            ["文件数据", "file_upload.file_path", "文件存储路径", "VARCHAR(255)"],
            ["会诊数据", "consultation_session.title", "会诊标题", "VARCHAR(128)"],
            ["会诊数据", "consultation_member.role", "会诊角色（OWNER/MEMBER）", "VARCHAR(32)"],
            ["会诊数据", "consultation_message.message_type", "消息类型（TEXT/FILE/IMAGE/MODEL/LINK）", "VARCHAR(16)"],
            ["会诊数据", "consultation_message.oss_path", "附件对象存储地址", "VARCHAR(255)"],
            ["系统数据", "audit_log.action", "操作类型（login/review/export）", "VARCHAR(64)"],
        ],
        col_widths_cm=[2.4, 3.8, 7.8, 1.6],
    )

    add_heading(doc, "4.1.4 数据采集", 3)
    add_body_paragraph(doc, "项目数据采集路径如下：")
    add_body_paragraph(doc, "① 临床业务数据：由医生在前端页面录入患者基础信息，影像序列通过系统上传接口接入，来源于院内检查系统导出的脱敏数据。")
    add_body_paragraph(doc, "② 算法训练/验证数据：使用公开医学影像数据集（如 BraTS 系列）与项目内已有的脱敏样例（如 brats_2013_pat0001_1_Flair.mha）进行模型调参与验证。")
    add_body_paragraph(doc, "③ 轮廓标注数据：先由 AI 生成初稿，再由放疗医生在 GTV/CTV 页面精修，形成可追踪版本。")
    add_body_paragraph(doc, "④ 协同交互数据：会诊消息、附件与操作日志在业务流程执行时自动采集并持久化。")
    add_body_paragraph(doc, "⑤ 数据治理要求：所有采集数据均需满足脱敏、最小权限与审计留痕要求。")

    add_heading(doc, "4.2 功能需求", 2)

    add_heading(doc, "4.2.1 项目功能用例图", 3)
    add_body_paragraph(doc, "系统核心参与者为放疗医生与会诊专家，外部协作对象包含模型推理服务与对象存储服务，业务用例如图 4.1 所示。")
    insert_image(doc, ASSET_DIR / "fig_4_1_usecase.png", width_cm=15.8)
    add_caption(doc, "图 4.1 系统用例图")

    add_table(
        doc,
        "表 4.2 功能模块描述",
        ["功能模块", "功能点", "功能描述", "优先级"],
        [
            ["账户权限模块", "用户注册", "录入姓名、医院、科室、手机号、密码并完成注册，校验账号唯一性。", 9],
            ["账户权限模块", "用户登录", "账号密码鉴权成功后签发 Token，并返回医生基础信息。", 10],
            ["账户权限模块", "令牌校验与续签", "对受保护接口执行 Bearer Token 校验，支持会话续签。", 9],
            ["账户权限模块", "登出与权限收敛", "清理本地凭据并回收服务端会话状态。", 8],
            ["患者管理模块", "患者建档", "新增患者编号、诊断、分期、主治医生等核心信息。", 10],
            ["患者管理模块", "患者检索", "按姓名、编号、诊断等条件模糊查询患者。", 10],
            ["患者管理模块", "患者详情编辑", "维护患者基础信息并记录更新时间。", 9],
            ["影像序列模块", "影像上传/登记", "上传 DICOM/NIfTI 并建立 Study 元数据记录。", 10],
            ["影像序列模块", "序列维护", "更新模态、描述、状态等序列信息。", 8],
            ["影像序列模块", "体数据与标签下载", "下载 volume 与 label 数据供算法或复核使用。", 8],
            ["靶区分割模块", "多模态分割触发", "调用模型服务执行分割任务并回传轮廓结果。", 10],
            ["靶区分割模块", "GTV 初稿管理", "查看并保存 AI 生成的 GTV 初稿版本。", 9],
            ["靶区分割模块", "CTV 精修审核", "医生修订 CTV 并提交审核状态。", 10],
            ["靶区分割模块", "轮廓状态流转", "支持待确认、待精修、已确认状态切换与追踪。", 9],
            ["CTV 决策模块", "CTV 外扩计算", "根据参数执行几何外扩并生成候选轮廓。", 9],
            ["CTV 决策模块", "热力图/CPDM 校核", "结合风险热图进行边界一致性分析。", 8],
            ["CTV 决策模块", "质量指标输出", "输出 Dice、HD95、体积偏差等指标。", 8],
            ["三维可视化模块", "模型加载", "按 Study 加载 GTV/CTV/OAR 三维模型。", 8],
            ["三维可视化模块", "图层与透明度控制", "动态控制图层显隐、透明度与阈值。", 7],
            ["三维可视化模块", "剖切与测量", "提供剖切、距离与体积测量工具。", 7],
            ["会诊协作模块", "会诊会话创建", "创建会诊会话并关联患者与资料包。", 9],
            ["会诊协作模块", "成员管理", "按好友关系添加/移除会诊成员并控制角色。", 8],
            ["会诊协作模块", "消息与附件协作", "发送文本消息并上传图片、文件、模型链接。", 9],
            ["会诊协作模块", "会诊纪要导出", "导出会诊关键结论与附件索引。", 7],
            ["智能助手模块", "病例问答", "基于对话上下文与知识库回答临床问题。", 7],
            ["智能助手模块", "历史追溯", "查询历史对话与工具调用记录。", 6],
            ["系统支撑模块", "审计日志", "记录登录、导出、审核等关键操作日志。", 8],
            ["系统支撑模块", "任务监控与告警", "跟踪分割任务状态并触发异常告警。", 8],
            ["系统支撑模块", "对象存储管理", "统一管理影像、轮廓、会诊附件存储路径。", 8],
        ],
        col_widths_cm=[2.8, 3.0, 8.2, 1.6],
        merge_first_col=True,
    )

    add_heading(doc, "4.2.2 功能模块结构图", 3)
    add_body_paragraph(doc, "功能模块分层结构如图 4.2 所示，体现“基础账号层—核心业务层—协作智能层”的演进关系。")
    insert_image(doc, ASSET_DIR / "fig_4_2_module_structure.png", width_cm=15.8)
    add_caption(doc, "图 4.2 功能模块结构图")

    add_heading(doc, "4.3 性能需求", 2)

    add_heading(doc, "4.3.1 时间特性", 3)
    add_body_paragraph(doc, "（1）响应时间")
    add_body_paragraph(doc, "① 登录鉴权接口平均响应时间不高于 2s，95 分位不高于 3s。")
    add_body_paragraph(doc, "② 患者列表与详情查询平均响应时间不高于 2s，复杂条件检索不高于 3s。")
    add_body_paragraph(doc, "③ 会诊文本消息端到端到达时间不高于 1s，附件消息应提供可视化上传进度。")
    add_body_paragraph(doc, "（2）更新处理时间")
    add_body_paragraph(doc, "① 多模态分割任务（单个病例）在标准 GPU 环境下处理时间不高于 120s。")
    add_body_paragraph(doc, "② CTV 外扩与热力图校核处理时间不高于 30s。")
    add_body_paragraph(doc, "③ 轮廓状态更新与版本写回数据库时间不高于 2s。")
    add_body_paragraph(doc, "（3）数据转换与传输时间")
    add_body_paragraph(doc, "① 3D 模型首屏加载时间不高于 5s，交互刷新帧率不低于 20 FPS。")
    add_body_paragraph(doc, "② 影像序列上传采用分片策略，100MB 级文件在校园网环境下应可稳定完成。")
    add_body_paragraph(doc, "（4）运行时间")
    add_body_paragraph(doc, "系统支持 7×24 小时连续运行，日常维护窗口内不影响已登录用户关键业务。")

    add_heading(doc, "4.3.2 适应性", 3)
    add_body_paragraph(
        doc,
        "系统在操作方式、运行环境与接口依赖变化时应具备适应能力：① 前端支持移动端与 H5 环境，保持核心流程一致；② 后端采用网关+微服务架构，接口可按版本演进；③ 模型侧支持替换分割模型与智能体模型而不改变业务入口；④ 在弱网条件下，上传、会诊消息与任务状态需具备重试与降级机制。"
    )

    add_heading(doc, "4.4 界面需求", 2)
    add_body_paragraph(doc, "本节给出 4.2 涉及的核心功能模块界面原型示意图，并对主要组件元素进行注解。")

    add_heading(doc, "4.4.1 登录与身份认证界面", 3)
    add_body_paragraph(doc, "用于完成医生身份验证与初始权限进入。")
    insert_image(doc, ASSET_DIR / "fig_4_3_login.png", width_cm=15.5)
    add_caption(doc, "图 4.3 登录与身份认证界面原型示意图")
    add_body_paragraph(doc, "组件注解：① 医院/科室切换；② 手机号输入框；③ 密码输入框；④ 登录按钮；⑤ 注册/找回入口。", indent=False)

    add_heading(doc, "4.4.2 患者列表与检索界面", 3)
    add_body_paragraph(doc, "用于展示患者总览并支持快速检索与筛选。")
    insert_image(doc, ASSET_DIR / "fig_4_4_patient_list.png", width_cm=15.5)
    add_caption(doc, "图 4.4 患者列表与检索界面原型示意图")
    add_body_paragraph(doc, "组件注解：① 关键词检索框；② 筛选标签栏；③ 患者卡片列表；④ 新增患者按钮；⑤ 底部导航栏。", indent=False)

    add_heading(doc, "4.4.3 患者详情与影像序列界面", 3)
    add_body_paragraph(doc, "用于查看单个患者的完整业务数据并发起后续任务。")
    insert_image(doc, ASSET_DIR / "fig_4_5_patient_detail.png", width_cm=15.5)
    add_caption(doc, "图 4.5 患者详情与影像序列界面原型示意图")
    add_body_paragraph(doc, "组件注解：① 基础信息面板；② 影像序列列表；③ 上传/下载区；④ 分割结果摘要；⑤ 操作按钮组。", indent=False)

    add_heading(doc, "4.4.4 GTV/CTV 标注与结果审核界面", 3)
    add_body_paragraph(doc, "用于医生对 AI 初稿进行精修、审核与版本管理。")
    insert_image(doc, ASSET_DIR / "fig_4_6_gtv_ctv.png", width_cm=15.5)
    add_caption(doc, "图 4.6 GTV/CTV 标注与结果审核界面原型示意图")
    add_body_paragraph(doc, "组件注解：① 切片视图区；② 工具栏；③ 轮廓版本列表；④ 状态流转区；⑤ 保存与导出按钮。", indent=False)

    add_heading(doc, "4.4.5 CTV 外扩与热力图校核界面", 3)
    add_body_paragraph(doc, "用于基于规则与模型进行 CTV 外扩计算与风险核对。")
    insert_image(doc, ASSET_DIR / "fig_4_7_ctv_heatmap.png", width_cm=15.5)
    add_caption(doc, "图 4.7 CTV 外扩与热力图校核界面原型示意图")
    add_body_paragraph(doc, "组件注解：① 参数输入区；② 外扩结果预览；③ 热力图视图；④ 一致性评分；⑤ 一键确认按钮。", indent=False)

    add_heading(doc, "4.4.6 三维模型浏览界面", 3)
    add_body_paragraph(doc, "用于临床人员从三维角度复核靶区空间形态与邻近关系。")
    insert_image(doc, ASSET_DIR / "fig_4_8_3d_viewer.png", width_cm=15.5)
    add_caption(doc, "图 4.8 三维模型浏览界面原型示意图")
    add_body_paragraph(doc, "组件注解：① 3D 主渲染窗口；② 图层树；③ 透明度与阈值；④ 剖切与测量工具；⑤ 视角重置/导出。", indent=False)

    add_heading(doc, "4.4.7 联合会诊与消息协作界面", 3)
    add_body_paragraph(doc, "用于医生与专家完成病例协作沟通与材料共享。")
    insert_image(doc, ASSET_DIR / "fig_4_9_consultation.png", width_cm=15.5)
    add_caption(doc, "图 4.9 联合会诊与消息协作界面原型示意图")
    add_body_paragraph(doc, "组件注解：① 会诊会话列表；② 消息时间轴；③ 附件上传区；④ 输入与发送区；⑤ 成员管理抽屉。", indent=False)

    add_heading(doc, "4.4.8 个人中心与系统设置界面", 3)
    add_body_paragraph(doc, "用于账号设置、安全配置与个性化系统管理。")
    insert_image(doc, ASSET_DIR / "fig_4_10_mine.png", width_cm=15.5)
    add_caption(doc, "图 4.10 个人中心与系统设置界面原型示意图")
    add_body_paragraph(doc, "组件注解：① 医生信息卡；② 快捷功能入口；③ 系统参数设置；④ 安全设置；⑤ 退出登录按钮。", indent=False)

    add_heading(doc, "4.5 接口需求", 2)

    add_heading(doc, "4.5.1 硬件接口", 3)
    add_body_paragraph(doc, "本项目依赖如下硬件能力及其调用方式：")
    add_body_paragraph(doc, "① GPU 推理服务器：用于执行多模态分割、CTV 外扩等计算密集任务；后端通过 HTTP 接口调用模型服务，模型服务内部调用 CUDA 运行时与深度学习框架完成推理。")
    add_body_paragraph(doc, "② 医生终端设备（手机/PC）：用于业务录入、轮廓审核与会诊协作；前端通过标准触控/鼠标交互触发接口调用。")
    add_body_paragraph(doc, "③ 对象存储与磁盘阵列：用于保存 DICOM、轮廓文件与会诊附件；系统通过 OSS SDK 或存储网关进行读写。")
    add_body_paragraph(doc, "④ 若部署环境不具备 GPU，可降级为 CPU 推理模式，但需接受更长的任务处理时间。")

    add_heading(doc, "4.5.2 软件接口", 3)
    add_body_paragraph(doc, "系统软件接口由“内部服务接口”和“外部依赖接口”两部分构成：")
    add_body_paragraph(doc, "① 内部服务接口：前端通过 REST API 访问网关，覆盖鉴权、患者、影像、轮廓、会诊、3D 模型等业务端点。")
    add_body_paragraph(doc, "② 模型服务接口：通过 /api/studies/{studyId}/segment/multimodal、/api/ctv/expand、/api/agent/chat 等接口完成分割、外扩与智能问答。")
    add_body_paragraph(doc, "③ 数据与缓存接口：业务服务通过 MySQL 完成持久化，通过 Redis 管理会话与热点数据。")
    add_body_paragraph(doc, "④ 存储接口：通过 OSS 或文件存储服务保存影像文件与附件资源，返回统一路径供前端下载与回放。")
    add_body_paragraph(doc, "⑤ 安全接口：所有业务接口默认使用 Bearer Token 鉴权，关键操作写入审计日志。")

    add_heading(doc, "4.6 其他需求", 2)

    add_heading(doc, "4.6.1 可使用性", 3)
    add_body_paragraph(doc, "① 界面术语采用放疗业务语境，重点流程（建档→上传→分割→审核→会诊）可在三次点击内进入。")
    add_body_paragraph(doc, "② 关键按钮提供状态反馈与错误提示，避免静默失败。")
    add_body_paragraph(doc, "③ 支持搜索、筛选、快捷入口与历史记录，降低重复操作成本。")
    add_body_paragraph(doc, "④ 复杂任务（如分割推理）需展示进度、预计耗时与可追踪状态。")

    add_heading(doc, "4.6.2 安全性", 3)
    add_body_paragraph(doc, "① 患者敏感信息必须脱敏存储与传输，接口全链路采用 HTTPS。")
    add_body_paragraph(doc, "② 账号密码采用强哈希存储，鉴权令牌设置有效期并支持失效机制。")
    add_body_paragraph(doc, "③ 关键操作（导出、确认、删除）执行审计留痕，满足追溯要求。")
    add_body_paragraph(doc, "④ 附件上传与下载执行类型校验与访问权限校验，防止越权与恶意文件注入。")

    add_heading(doc, "4.6.3 可维护性", 3)
    add_body_paragraph(doc, "① 采用前后端分离与模块化服务架构，业务边界清晰，便于迭代。")
    add_body_paragraph(doc, "② 核心接口统一返回结构（code/message/data），便于问题定位与联调。")
    add_body_paragraph(doc, "③ 模型侧通过可配置化参数与流程编排支持快速替换算法组件。")
    add_body_paragraph(doc, "④ 日志、监控与测试脚本形成闭环，降低故障排查成本。")

    add_heading(doc, "4.6.4 可移植性", 3)
    add_body_paragraph(doc, "① 前端基于 uni-app，可在移动端与 H5 环境复用核心页面。")
    add_body_paragraph(doc, "② 后端与模型服务通过容器化部署，支持在不同 Linux/Windows 服务器环境迁移。")
    add_body_paragraph(doc, "③ 数据库与缓存组件采用通用中间件（MySQL、Redis），具备较强生态兼容性。")
    add_body_paragraph(doc, "④ 通过配置分离（.env/.yml）实现环境切换，降低跨环境部署改造成本。")


def build_document():
    create_assets()
    doc = Document()
    style_document(doc)
    add_cover(doc)
    add_toc(doc)
    add_content(doc)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    doc.save(str(DOC_PATH))


if __name__ == "__main__":
    build_document()
    print(f"已生成: {DOC_PATH}")

