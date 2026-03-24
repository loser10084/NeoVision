from pathlib import Path
import sys

from langchain_core.messages import HumanMessage


ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
sys.path.insert(0, str(ROOT))

from model_agents.nodes.router_node import router_node


def test_router_selects_imaging_analysis_agent_when_image_is_present():
    state = {
        "messages": [
            HumanMessage(
                content=[
                    {"type": "text", "text": "\u8bf7\u5e2e\u6211\u5206\u6790\u8fd9\u5f20\u56fe"},
                    {"type": "image_url", "image_url": {"url": "https://example.com/a.png"}},
                ]
            )
        ],
        "query": "\u8bf7\u5e2e\u6211\u5206\u6790\u8fd9\u5f20\u56fe",
        "image_url": "https://example.com/a.png",
    }

    result = router_node(state)
    assert result["next_agent"] == "imaging_analysis_agent"


def test_router_selects_quality_assessment_agent_for_quality_queries():
    query = "\u8bf7\u505a\u4e00\u4e0b\u52fe\u753b\u8d28\u91cf\u8bc4\u4f30\u548cQA\u590d\u6838"
    state = {
        "messages": [HumanMessage(content=query)],
        "query": query,
        "image_url": None,
    }

    result = router_node(state)
    assert result["next_agent"] == "quality_assessment_agent"


def test_router_selects_operation_assistant_agent_for_how_to_queries():
    query = "\u8bf7\u544a\u8bc9\u6211\u600e\u4e48\u4e0a\u4f20\u75c5\u4f8b\u5e76\u5bfc\u51fa\u7ed3\u679c"
    state = {
        "messages": [HumanMessage(content=query)],
        "query": query,
        "image_url": None,
    }

    result = router_node(state)
    assert result["next_agent"] == "operation_assistant_agent"


def test_router_selects_clinical_guideline_agent_for_guideline_queries():
    query = "\u5e2e\u6211\u68c0\u7d22\u4e00\u4e0b\u9f3b\u54bd\u764c\u653e\u7597\u6307\u5357\u548c\u5171\u8bc6"
    state = {
        "messages": [HumanMessage(content=query)],
        "query": query,
        "image_url": None,
    }

    result = router_node(state)
    assert result["next_agent"] == "clinical_guideline_retrieval_agent"
