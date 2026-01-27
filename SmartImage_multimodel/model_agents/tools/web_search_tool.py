"""
model_agents.tools.web_search_tool：
    网络搜索工具
"""
import json
import re
from html.parser import HTMLParser
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from langchain_core.tools import tool

from .. import llm
from utils import logger


class _DDGParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = []
        self._capture = False
        self._href = ""
        self._text = ""

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        attr_map = dict(attrs)
        href = attr_map.get("href", "")
        if "duckduckgo.com/l/" in href:
            self._capture = True
            self._href = href
            self._text = ""

    def handle_data(self, data):
        if self._capture:
            self._text += data

    def handle_endtag(self, tag):
        if tag == "a" and self._capture:
            title = re.sub(r"\s+", " ", self._text).strip()
            if title:
                self.results.append({"title": title, "url": self._href})
            self._capture = False
            self._href = ""
            self._text = ""


@tool
def web_search(query: str) -> str:
    """Search the web using DuckDuckGo HTML results."""
    logger.info(f"[web_search] query={query}")
    query = (query or "").strip()
    if not query:
        return ""
    url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    logger.debug(f"[web_search] 开始搜索 url={url}")
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=10) as response:
        html = response.read().decode("utf-8", errors="ignore")
    parser = _DDGParser()
    parser.feed(html)
    results = parser.results[:5]
    logger.debug(f"[web_search] 搜索结果={results}")
    return json.dumps(results, ensure_ascii=True)