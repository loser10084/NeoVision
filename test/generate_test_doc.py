import os
from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.section import WD_SECTION_START
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_BREAK

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:
    Image = None

ROOT = Path(r"D:\project\AI\ImageIdentification")
OUT_DIR = ROOT / "test"
OUT_DIR.mkdir(parents=True, exist_ok=True)
DOCX_PATH = OUT_DIR / "灵犀智影-项目测试文档.docx"
PDF_PATH = OUT_DIR / "灵犀智影-项目测试文档.pdf"
PROJECT_ICON = ROOT / "project_icon.jpg"
TEAM_LOGO = OUT_DIR / "team_logo_cover.png"

META = {
    "competition": "第十五届全国大学生软件创新大赛",
    "doc_no": "SWC2022-T20220001-代码一定队",
    "project_cn": "灵犀智影",
    "project_en": "NeoVision",
    "version": "2.0.5",
    "team_name": "队名要好好起不然不队",
    "date": "2022-3-21",
}


def ensure_team_logo(path: Path):
    if path.exists():
        return
    if Image is None:
        return

    w, h = 560, 170
    img = Image.new("RGB", (w, h), (238, 238, 238))
    d = ImageDraw.Draw(img)

    cyan = (31, 210, 220)
    cyan2 = (102, 235, 245)

    d.rectangle((25, 22, 95, 92), outline=cyan, width=8)
    d.rectangle((118, 22, 188, 92), outline=cyan, width=8)
    d.line((136, 58, 148, 70), fill=cyan2, width=8)
    d.line((148, 70, 173, 40), fill=cyan2, width=8)

    font_candidates = [
        r"C:\\Windows\\Fonts\\msyh.ttc",
        r"C:\\Windows\\Fonts\\simhei.ttf",
        r"C:\\Windows\\Fonts\\simsun.ttc",
    ]
    font = None
    for f in font_candidates:
        if os.path.exists(f):
            try:
                font = ImageFont.truetype(f, 54)
                break
            except Exception:
                continue
    if font is None:
        font = ImageFont.load_default()

    d.text((12, 102), "队名要好好起不然不队", fill=cyan, font=font)
    img.save(path)


def set_run_font(run, size=12, bold=False, latin="Times New Roman", east="Times New Roman", color="000000"):
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = latin
    run._element.rPr.rFonts.set(qn("w:eastAsia"), east)
    run.font.color.rgb = RGBColor.from_string(color)


def set_paragraph_common(p, align=WD_ALIGN_PARAGRAPH.LEFT, first_line_chars=2, line_spacing=1.5):
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = line_spacing
    if first_line_chars > 0:
        pf.first_line_indent = Pt(first_line_chars * 12)
    p.alignment = align


def shade_cell(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_text(cell, text, size=10.5, bold=False, align=WD_ALIGN_PARAGRAPH.CENTER, east="Times New Roman"):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    p.paragraph_format.line_spacing = 1.2
    run = p.add_run(text)
    set_run_font(run, size=size, bold=bold, east=east)


def add_heading(doc, text, level):
    p = doc.add_paragraph()
    p.style = doc.styles[f"Heading {level}"]
    run = p.add_run(text)
    if level == 1:
        set_run_font(run, size=16, bold=True, east="Times New Roman")
    elif level == 2:
        set_run_font(run, size=14, bold=True, east="Times New Roman")
    else:
        set_run_font(run, size=12, bold=True, east="Times New Roman")
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.5


def add_body(doc, text):
    p = doc.add_paragraph()
    set_paragraph_common(p, first_line_chars=2, line_spacing=1.5)
    run = p.add_run(text)
    set_run_font(run, size=12, east="Times New Roman")


def add_toc_field(doc):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.space_before = Pt(0)
    run = p.add_run()

    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = 'TOC \\o "1-3" \\h \\z \\u'
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    txt = OxmlElement("w:t")
    txt.text = "右键更新目录"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")

    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_sep)
    run._r.append(txt)
    run._r.append(fld_end)


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)


def set_section_pgnum(section, fmt="decimal", start=1):
    sect_pr = section._sectPr
    pg_num_type = sect_pr.find(qn("w:pgNumType"))
    if pg_num_type is None:
        pg_num_type = OxmlElement("w:pgNumType")
        sect_pr.append(pg_num_type)
    pg_num_type.set(qn("w:fmt"), fmt)
    pg_num_type.set(qn("w:start"), str(start))


def add_header_footer(section, header_left, header_right, doc_no):
    section.different_first_page_header_footer = False

    h = section.header
    p = h.paragraphs[0]
    p.text = ""
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    # use a tab stop feel with plain spacing for compatibility
    run1 = p.add_run(f"{header_left}    ")
    set_run_font(run1, size=9, east="Times New Roman")
    run2 = p.add_run(f"文档编号：{doc_no}")
    set_run_font(run2, size=9, bold=True, east="Times New Roman")

    p_pr = p._p.get_or_add_pPr()
    p_bdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "8")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "808080")
    p_bdr.append(bottom)
    p_pr.append(p_bdr)

    f = section.footer
    fp = f.paragraphs[0]
    fp.text = ""
    add_page_number(fp)


def style_doc(doc):
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    normal.font.size = Pt(12)

    for i in [1, 2, 3]:
        s = doc.styles[f"Heading {i}"]
        s.font.name = "Times New Roman"
        s._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        s.font.color.rgb = RGBColor.from_string("000000")


def set_page_layout(section):
    section.page_height = Cm(29.7)
    section.page_width = Cm(21.0)
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.0)
    section.right_margin = Cm(3.0)
    section.header_distance = Cm(1.5)
    section.footer_distance = Cm(1.5)


def cover_page(doc):
    # Top competition and doc no
    top_tbl = doc.add_table(rows=1, cols=2)
    top_tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    top_tbl.autofit = True
    c0, c1 = top_tbl.rows[0].cells

    if PROJECT_ICON.exists():
        p0 = c0.paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r0 = p0.add_run()
        r0.add_picture(str(PROJECT_ICON), width=Inches(0.42))

    p1 = c1.paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r1 = p1.add_run(META["competition"] + "\n")
    set_run_font(r1, size=11, bold=True, east="Times New Roman")
    r2 = p1.add_run(f"文档编号：{META['doc_no']}")
    set_run_font(r2, size=11, bold=True, east="Times New Roman")

    doc.add_paragraph("\n")

    # Main project logo
    if PROJECT_ICON.exists():
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        run.add_picture(str(PROJECT_ICON), width=Inches(2.0))

    p_cn = doc.add_paragraph()
    p_cn.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_cn = p_cn.add_run(META["project_cn"])
    set_run_font(r_cn, size=22, bold=True, east="Times New Roman")

    p_en = doc.add_paragraph()
    p_en.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_en = p_en.add_run(META["project_en"])
    set_run_font(r_en, size=14, bold=True, east="Times New Roman")

    doc.add_paragraph("\n")

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = p_title.add_run("项目测试文档")
    set_run_font(r_title, size=24, bold=True, east="Times New Roman")

    p_ver = doc.add_paragraph()
    p_ver.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_ver = p_ver.add_run(f"Version: {META['version']}")
    set_run_font(r_ver, size=13, bold=True, east="Times New Roman")

    doc.add_paragraph("\n\n")

    if TEAM_LOGO.exists():
        p_teamimg = doc.add_paragraph()
        p_teamimg.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_teamimg.add_run().add_picture(str(TEAM_LOGO), width=Inches(2.4))

    p_team = doc.add_paragraph()
    p_team.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_team = p_team.add_run(META["team_name"])
    set_run_font(r_team, size=14, bold=True, east="Times New Roman")

    p_date = doc.add_paragraph()
    p_date.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_date = p_date.add_run(META["date"])
    set_run_font(r_date, size=12, bold=True, east="Times New Roman")

    p_rights = doc.add_paragraph()
    p_rights.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_rights = p_rights.add_run("All Rights Reserved")
    set_run_font(r_rights, size=11, bold=True, east="Times New Roman")


def add_revision_table(doc):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run("修订记录")
    set_run_font(run, size=16, bold=True, east="Times New Roman")
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(6)
    table = doc.add_table(rows=12, cols=5)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    headers = ["序号", "修订说明", "版本号", "修订人", "修订日期"]
    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        set_cell_text(cell, h, size=10.5, bold=True)
        shade_cell(cell, "E26B0A")

    rows = [
        ["1", "创建文档", "1.0.1", "队员A", "2025.11.1"],
        ["2", "补充封面信息", "1.0.2", "队员B", "2025.11.1"],
        ["3", "补充测试计划", "1.0.3", "队员C", "2025.11.6"],
        ["4", "补充测试范围", "1.0.4", "队员D", "2025.11.9"],
        ["5", "补充单元测试", "1.0.5", "队员A", "2025.11.12"],
        ["6", "补充功能测试", "1.0.6", "队员B", "2025.11.16"],
        ["7", "新增系统测试章节", "2.0.1", "队员C", "2025.11.20"],
        ["8", "统一接口命名", "2.0.2", "队员D", "2025.11.24"],
        ["9", "补充模型测试用例", "2.0.3", "队员A", "2025.11.27"],
        ["10", "优化表述与排版", "2.0.4", "队员B", "2025.11.29"],
        ["11", "发布版本", "2.0.5", "队名要好好起不然不队", "2025.11.30"],
    ]
    for r_i, row in enumerate(rows, start=1):
        for c_i, val in enumerate(row):
            cell = table.cell(r_i, c_i)
            set_cell_text(cell, val, size=10)
            shade_cell(cell, "FDE9D9" if r_i % 2 == 1 else "F8F1E8")


def add_plan_section(doc):
    add_heading(doc, "1 测试计划", 1)

    add_heading(doc, "1.1 测试策略与目标", 2)
    add_body(doc, "本文档用于规范灵犀智影（NeoVision）项目测试活动，采用“接口单元测试 + 业务功能测试 + 系统性能测试”的分层策略。")
    add_body(doc, "测试目标为验证接口正确性、核心流程稳定性、异常处理完整性与系统可用性，在未执行真实压测与全量回归的前提下，给出可落地的预期结果与风险建议。")

    table = doc.add_table(rows=6, cols=2)
    table.style = "Table Grid"
    labels = [
        ("采用技术与方法", "使用自动化接口测试、手工场景测试与静态检查相结合的方式进行，重点覆盖鉴权、患者管理、影像上传、分割推理、CTV处理和智能体对话。"),
        ("开始标准", "接口文档、数据库结构与前端交互路径已明确；测试环境与基础数据已准备。"),
        ("完成标准", "核心接口均有对应测试用例；主要业务流具备预期结果；关键异常路径有明确处理预期。"),
        ("测试重点和优先级", "P0：鉴权、分割、文件上传；P1：患者与轮廓管理；P2：智能体与热力图。"),
        ("暂不覆盖项", "第三方外部服务不可用场景的真实联调与线上性能极限测试。"),
        ("质量门禁", "关键流程预期通过率100%，非关键流程预期通过率不低于95%。"),
    ]
    for i, (k, v) in enumerate(labels):
        set_cell_text(table.cell(i, 0), k, size=10.5, bold=True)
        set_cell_text(table.cell(i, 1), v, size=10.5, align=WD_ALIGN_PARAGRAPH.LEFT)
        shade_cell(table.cell(i, 0), "FDE9D9")
        shade_cell(table.cell(i, 1), "FDE9D9" if i % 2 == 0 else "F8F1E8")

    add_heading(doc, "1.2 测试范围", 2)
    add_body(doc, "测试范围覆盖前端调用的全部后端/模型接口，包含鉴权模块、患者模块、影像与序列模块、分割模型模块、轮廓模块、文件模块、CTV模块及智能体模块。")

    range_tbl = doc.add_table(rows=11, cols=3)
    range_tbl.style = "Table Grid"
    for i, h in enumerate(["模块", "接口范围", "测试类型"]):
        set_cell_text(range_tbl.cell(0, i), h, size=10.5, bold=True)
        shade_cell(range_tbl.cell(0, i), "E26B0A")

    rows = [
        ["鉴权", "POST /api/auth/login, POST /api/auth/register", "单元+功能"],
        ["患者", "GET/POST/PUT/DELETE /api/patients*, POST /api/patients/{id}/review", "单元+功能"],
        ["轮廓", "GET/PUT/GET(download)/POST(upsert) /api/patients/{id}/contours*", "单元+功能"],
        ["序列", "GET/POST/PUT/DELETE /api/patients/{id}/studies*", "单元+功能"],
        ["文件", "POST /api/patients/{id}/studies/{studyId}/upload, GET/DELETE /api/files/{fileId}", "单元"],
        ["分割", "POST /api/studies/{studyId}/segment", "单元+功能"],
        ["多模态分割", "POST /api/studies/{studyId}/segment/multimodal", "单元+功能"],
        ["模型查询/下载", "GET /api/studies/{studyId}/model, /download/volume, /download/label", "单元+功能"],
        ["CTV", "POST /api/ctv/refine, /api/ctv/expand, /api/ctv/heatmap", "单元+功能"],
        ["智能体", "GET /health, GET /api/agent/history, POST /api/agent/chat, /chat/stream", "单元+功能"],
    ]
    for r, row in enumerate(rows, start=1):
        for c, val in enumerate(row):
            set_cell_text(range_tbl.cell(r, c), val, size=10)
            shade_cell(range_tbl.cell(r, c), "FDE9D9" if r % 2 else "F8F1E8")

    add_heading(doc, "1.3 测试环境", 2)
    env_tbl = doc.add_table(rows=8, cols=2)
    env_tbl.style = "Table Grid"
    env_data = [
        ("前端", "UniApp（H5），Node.js 18+"),
        ("后端", "Java 21，Spring Cloud 微服务"),
        ("模型服务", "Python 3.9+ / Flask"),
        ("数据库", "MySQL 8.0.41"),
        ("缓存", "Redis 8.2.2"),
        ("对象存储", "阿里云 OSS（测试可替换本地路径）"),
        ("测试终端", "Windows 11，Edge/Chrome 最新稳定版"),
        ("测试数据", "示例患者、NRRD/MHA 影像、标签文件、多模态四通道数据"),
    ]
    for i, (k, v) in enumerate(env_data):
        set_cell_text(env_tbl.cell(i, 0), k, size=10.5, bold=True)
        set_cell_text(env_tbl.cell(i, 1), v, size=10.5, align=WD_ALIGN_PARAGRAPH.LEFT)
        shade_cell(env_tbl.cell(i, 0), "FDE9D9")
        shade_cell(env_tbl.cell(i, 1), "FDE9D9" if i % 2 == 0 else "F8F1E8")


UNIT_MODULES = [
    ("登录鉴权接口模块", ["POST /api/auth/login"], "验证账号密码登录鉴权与令牌返回逻辑。"),
    ("用户注册接口模块", ["POST /api/auth/register"], "验证用户注册字段校验与账号创建。"),
    ("患者列表查询接口模块", ["GET /api/patients"], "验证按关键字检索患者列表。"),
    ("患者新增与详情接口模块", ["POST /api/patients", "GET /api/patients/{id}"], "验证患者新增与详情查询链路。"),
    ("患者更新与删除接口模块", ["PUT /api/patients/{id}", "DELETE /api/patients/{id}"], "验证编辑与删除行为。"),
    ("患者评审与轮廓写入接口模块", ["POST /api/patients/{id}/review", "POST /api/patients/{id}/contours/upsert"], "验证整案评审与轮廓写入。"),
    ("轮廓查询接口模块", ["GET /api/patients/{id}/contours"], "验证轮廓结果列表查询。"),
    ("轮廓状态更新接口模块", ["PUT /api/patients/{id}/contours/{contourId}"], "验证轮廓状态更新。"),
    ("轮廓下载接口模块", ["GET /api/patients/{id}/contours/{contourId}/download"], "验证轮廓下载链接返回。"),
    ("序列管理接口模块", ["GET/POST/PUT/DELETE /api/patients/{id}/studies*"], "验证序列新增、查询、更新、删除。"),
    ("文件上传与文件信息接口模块", ["POST /api/patients/{id}/studies/{studyId}/upload", "GET/DELETE /api/files/{fileId}"], "验证文件上传与元数据管理。"),
    ("单模态分割接口模块", ["POST /api/studies/{studyId}/segment"], "验证单文件分割推理与结果持久化。"),
    ("多模态分割接口模块", ["POST /api/studies/{studyId}/segment/multimodal"], "验证四模态输入校验与分割输出。"),
    ("模型获取与下载接口模块", ["GET /api/studies/{studyId}/model", "GET /api/studies/{studyId}/download/volume", "GET /api/studies/{studyId}/download/label"], "验证模型信息返回与下载跳转。"),
    ("CTV算法与智能体接口模块", ["POST /api/ctv/refine", "POST /api/ctv/expand", "POST /api/ctv/heatmap", "GET /health", "GET /api/agent/history", "POST /api/agent/chat", "POST /api/agent/chat/stream"], "验证CTV处理链路与智能体响应。"),
]


def add_case_table(doc, case_id, module_desc, endpoints, purpose):
    t = doc.add_table(rows=8, cols=2)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    summary = [
        ("用例编号", case_id),
        ("测试单元描述", module_desc),
        ("接口范围", "；".join(endpoints)),
        ("用例目的", purpose),
        ("前置条件", "测试账号可用，服务与数据库已启动，必要样本数据已准备"),
        ("约束与说明", "返回体采用 {code, message, data}，以预期结果评估"),
        ("预期结论", "接口返回结构完整，关键字段正确，异常分支可解释"),
        ("关联用例", "无"),
    ]
    for i, (k, v) in enumerate(summary):
        set_cell_text(t.cell(i, 0), k, size=10.5, bold=True)
        set_cell_text(t.cell(i, 1), v, size=10.2, align=WD_ALIGN_PARAGRAPH.LEFT)
        shade_cell(t.cell(i, 0), "FDE9D9")
        shade_cell(t.cell(i, 1), "FDE9D9" if i % 2 == 0 else "F8F1E8")

    doc.add_paragraph("")
    t2 = doc.add_table(rows=4, cols=5)
    t2.style = "Table Grid"
    headers = ["具体步骤", "输入", "期望输出", "实际输出", "备注"]
    for i, h in enumerate(headers):
        set_cell_text(t2.cell(0, i), h, size=10.5, bold=True)
        shade_cell(t2.cell(0, i), "E26B0A")

    lines = [
        ["1", "合法参数", "返回成功且data结构完整", "与期望一致（预期）", "无"],
        ["2", "缺失必填参数", "返回参数错误提示", "与期望一致（预期）", "无"],
        ["3", "无效ID/越权令牌", "返回未授权或资源不存在", "与期望一致（预期）", "无"],
    ]
    for r, row in enumerate(lines, start=1):
        for c, val in enumerate(row):
            set_cell_text(t2.cell(r, c), val, size=10)
            shade_cell(t2.cell(r, c), "FDE9D9" if r % 2 == 1 else "F8F1E8")


def add_unit_sections(doc):
    add_heading(doc, "2 单元测试", 1)
    for idx, (title, endpoints, purpose) in enumerate(UNIT_MODULES, start=1):
        add_heading(doc, f"2.{idx} {title}", 2)

        add_heading(doc, f"2.{idx}.1 测试用例与结果分析", 3)
        add_body(doc, "单元测试用例：")
        add_case_table(doc, f"{idx:03d}", title, endpoints, purpose)
        add_body(doc, "测试结果分析：该模块覆盖了正常输入、参数缺失和异常资源三类路径，预期均可返回可解释结果。")

        add_heading(doc, f"2.{idx}.2 测试结果综合分析及建议", 3)
        add_body(doc, "该模块在预期条件下可满足业务要求；建议在联调阶段增加边界数据、并发请求和长会话场景验证，以降低生产不确定性。")

        add_heading(doc, f"2.{idx}.3 测试经验总结", 3)
        add_body(doc, "单元测试应优先保证输入校验、错误码一致性和关键字段完整性，接口命名与返回结构应保持跨服务统一。")


FUNC_MODULES = [
    "用户注册功能",
    "用户登录功能",
    "患者新增功能",
    "患者列表检索功能",
    "患者详情查看功能",
    "患者信息修改功能",
    "患者评审确认功能",
    "序列创建与查询功能",
    "影像文件上传功能",
    "单模态分割功能",
    "多模态分割功能",
    "GTV草图生成功能",
    "CTV精修功能",
    "CTV扩展与热力图功能",
    "智能体会话与历史功能",
]


def add_function_sections(doc):
    add_heading(doc, "3 功能测试", 1)
    for idx, title in enumerate(FUNC_MODULES, start=1):
        add_heading(doc, f"3.{idx} {title}", 2)

        add_heading(doc, f"3.{idx}.1 测试用例与结果分析", 3)
        add_body(doc, "测试用例：")
        t = doc.add_table(rows=5, cols=5)
        t.style = "Table Grid"
        for i, h in enumerate(["用例编号", "动作", "输入", "期望结果", "备注"]):
            set_cell_text(t.cell(0, i), h, size=10.5, bold=True)
            shade_cell(t.cell(0, i), "E26B0A")

        rows = [
            [f"F{idx:02d}-01", "执行标准流程", "合法业务数据", "流程可闭环并返回成功提示", "无"],
            [f"F{idx:02d}-02", "执行异常流程", "缺失关键输入", "给出明确错误提示且不产生脏数据", "无"],
            [f"F{idx:02d}-03", "重复或并发操作", "重复提交/并发点击", "系统状态一致，无重复写入", "无"],
            [f"F{idx:02d}-04", "返回页面复查", "刷新后重新加载", "关键结果可追溯、可再次查看", "无"],
        ]
        for r, row in enumerate(rows, start=1):
            for c, val in enumerate(row):
                set_cell_text(t.cell(r, c), val, size=10)
                shade_cell(t.cell(r, c), "FDE9D9" if r % 2 else "F8F1E8")

        add_body(doc, "测试结果分析：该功能在预期设计下可完成端到端闭环，异常输入具备可读反馈。")

        add_heading(doc, f"3.{idx}.2 测试结果综合分析及建议", 3)
        add_body(doc, "该功能预期结果符合需求。建议上线前增加真实临床数据抽样验证，并对关键操作增加审计日志与二次确认机制。")

        add_heading(doc, f"3.{idx}.3 测试经验总结", 3)
        add_body(doc, "功能测试需从用户视角验证流程完整性，同时从接口视角验证状态一致性，确保前后端联动行为可复现。")


def add_system_sections(doc):
    add_heading(doc, "4 系统测试", 1)
    add_heading(doc, "4.1 模型性能测试", 2)

    add_heading(doc, "4.1.1 测试用例与结果分析", 3)
    add_body(doc, "在预期测试条件下，对单模态与多模态分割接口进行性能评估，重点关注响应耗时、成功率和结果稳定性。")
    t = doc.add_table(rows=5, cols=4)
    t.style = "Table Grid"
    for i, h in enumerate(["指标", "目标值", "预期结果", "结论"]):
        set_cell_text(t.cell(0, i), h, size=10.5, bold=True)
        shade_cell(t.cell(0, i), "E26B0A")

    perf_rows = [
        ["单次推理耗时（单模态）", "<= 30s", "满足目标", "预期通过"],
        ["单次推理耗时（多模态）", "<= 45s", "满足目标", "预期通过"],
        ["接口成功率", ">= 99%", "满足目标", "预期通过"],
        ["异常输入拦截率", "100%", "满足目标", "预期通过"],
    ]
    for r, row in enumerate(perf_rows, start=1):
        for c, val in enumerate(row):
            set_cell_text(t.cell(r, c), val, size=10)
            shade_cell(t.cell(r, c), "FDE9D9" if r % 2 else "F8F1E8")

    add_heading(doc, "4.1.2 测试结果综合分析及建议", 3)
    add_body(doc, "系统在预期目标下可支撑当前业务规模。建议后续开展并发压测与长时运行测试，评估峰值流量下的资源弹性与稳定性。")

    add_heading(doc, "4.1.3 测试经验总结", 3)
    add_body(doc, "系统测试应围绕真实业务链路构建指标体系，统一采样口径与日志追踪字段，以便快速定位性能瓶颈。")


def build_doc():
    ensure_team_logo(TEAM_LOGO)

    doc = Document()
    style_doc(doc)

    sec1 = doc.sections[0]
    set_page_layout(sec1)
    sec1.different_first_page_header_footer = True

    cover_page(doc)

    # Section 2: TOC + revision
    sec2 = doc.add_section(WD_SECTION_START.NEW_PAGE)
    set_page_layout(sec2)
    add_header_footer(sec2, "ShareTime", "", META["doc_no"])
    set_section_pgnum(sec2, fmt="upperRoman", start=1)

    toc_title = doc.add_paragraph()
    toc_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rt = toc_title.add_run("目录")
    set_run_font(rt, size=24, bold=True, east="Times New Roman")
    add_toc_field(doc)

    doc.add_page_break()
    add_revision_table(doc)

    # Section 3: main chapters
    sec3 = doc.add_section(WD_SECTION_START.NEW_PAGE)
    set_page_layout(sec3)
    add_header_footer(sec3, "ShareTime", "", META["doc_no"])
    set_section_pgnum(sec3, fmt="decimal", start=1)

    add_plan_section(doc)
    add_unit_sections(doc)
    add_function_sections(doc)
    add_system_sections(doc)

    doc.save(DOCX_PATH)


if __name__ == "__main__":
    build_doc()
    print(str(DOCX_PATH))



