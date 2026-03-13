from pathlib import Path
import sys

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
sys.path.insert(0, ROOT)

from api_gateway import patient_assistant


def test_parse_query_intent():
    intent = patient_assistant._parse_intent("\u67e5\u8be2\u4e00\u4e0b\u5f20\u4e09\u7684\u4e00\u4e9b\u60a3\u8005\u6570\u636e")
    assert intent is not None
    assert intent.intent == "query"
    assert intent.keyword == "\u5f20\u4e09"


def test_parse_navigation_intent():
    intent = patient_assistant._parse_intent("\u5e2e\u6211\u4eec\u76f4\u63a5\u8df3\u8f6c\u8fdb\u5165\u5f20\u4e09\u7684\u60a3\u8005\u8be6\u60c5\u754c\u9762")
    assert intent is not None
    assert intent.intent == "navigate"
    assert intent.keyword == "\u5f20\u4e09"


def test_build_navigation_reply_detail():
    intent = patient_assistant.PatientIntent(intent="navigate", keyword="\u5f20\u4e09")
    candidates = [{"id": 101, "name": "\u5f20\u4e09"}]
    payload = patient_assistant._build_navigation_reply(intent, candidates, candidates[0])
    assert payload["action"]["type"] == "open_patient_detail"
    assert payload["action"]["patientId"] == 101


def test_build_navigation_reply_list():
    intent = patient_assistant.PatientIntent(intent="navigate", keyword="\u5f20\u4e09")
    candidates = [{"id": 101, "name": "\u5f20\u4e09"}, {"id": 102, "name": "\u5f20\u4e09"}]
    payload = patient_assistant._build_navigation_reply(intent, candidates, candidates[0])
    assert payload["action"]["type"] == "open_patient_list"
    assert payload["action"]["keyword"] == "\u5f20\u4e09"
