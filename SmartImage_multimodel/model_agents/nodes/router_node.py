from utils import logger


QUALITY_KEYWORDS = (
    "质量评估",
    "质控",
    "qa",
    "qc",
    "审核",
    "复核",
    "风险",
    "置信度",
    "一致性",
    "误差",
    "漏画",
    "错画",
)
OPERATION_KEYWORDS = (
    "怎么",
    "如何",
    "步骤",
    "操作",
    "使用",
    "点击",
    "上传",
    "导出",
    "查看",
    "打不开",
    "报错",
    "流程",
    "功能",
)
IMAGING_KEYWORDS = (
    "影像分析",
    "读片",
    "图像",
    "截图",
    "病灶",
    "轮廓",
    "边界",
    "热力图",
    "分割",
    "掩膜",
    "勾画",
    "看这张图",
    "这张图",
)
GUIDELINE_KEYWORDS = (
    "指南",
    "共识",
    "规范",
    "sop",
    "推荐",
    "证据",
    "文献",
    "检索",
    "nccn",
    "csco",
    "astro",
    "estro",
    "esmo",
)
AGENT_PRIORITY = {
    "quality_assessment_agent": 4,
    "clinical_guideline_retrieval_agent": 3,
    "imaging_analysis_agent": 2,
    "operation_assistant_agent": 1,
}


def _message_has_image(content) -> bool:
    if not isinstance(content, list):
        return False
    return any(
        isinstance(item, dict) and item.get("type") == "image_url"
        for item in content
    )


def _message_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        return " ".join(part for part in parts if part)
    return str(content or "")


def _score_keywords(text: str, keywords) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def router_node(state):
    has_image = bool(state.get("image_url") or state.get("image_urls"))
    latest_text = str(state.get("query") or "").strip()

    for msg in state.get("messages", []):
        if not hasattr(msg, "content"):
            continue
        has_image = has_image or _message_has_image(msg.content)
        latest_text = _message_text(msg.content) or latest_text

    latest_text = latest_text.lower()
    if has_image:
        selected_agent = "imaging_analysis_agent"
    else:
        scores = {
            "quality_assessment_agent": _score_keywords(latest_text, QUALITY_KEYWORDS),
            "operation_assistant_agent": _score_keywords(latest_text, OPERATION_KEYWORDS),
            "imaging_analysis_agent": _score_keywords(latest_text, IMAGING_KEYWORDS),
            "clinical_guideline_retrieval_agent": _score_keywords(latest_text, GUIDELINE_KEYWORDS),
        }
        selected_agent = max(scores, key=lambda key: (scores[key], AGENT_PRIORITY[key]))
        if scores[selected_agent] == 0:
            selected_agent = "operation_assistant_agent"

    logger.info(f"[router_node] input={latest_text[:100]}")
    logger.info(f"[router_node] next_agent={selected_agent}")
    return {
        "next_agent": selected_agent,
        "step_count": 1,
    }
