import asyncio
from typing import List, Dict
import httpx
import feedparser
from bs4 import BeautifulSoup

class ScraperService:
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36"
        )
    }

    @classmethod
    async def parse_rss_feed(cls, feed_url: str) -> List[Dict[str, str]]:
        """异步拉取并解析标准 RSS / Atom 摘要"""
        async with httpx.AsyncClient(timeout=15.0, headers=cls.DEFAULT_HEADERS, follow_redirects=True) as client:
            try:
                resp = await client.get(feed_url)
                resp.raise_for_status()
                content = resp.text
            except Exception:
                # 针对测试环境或无网络时，优雅降级
                return []

        # feedparser 运行在线程池中避免阻塞事件循环
        loop = asyncio.get_event_loop()
        parsed = await loop.run_in_executor(None, feedparser.parse, content)

        results = []
        for entry in parsed.entries[:20]:  # 每次拉取最新 20 条
            url = getattr(entry, "link", "")
            title = getattr(entry, "title", "未命名通知")
            summary = getattr(entry, "summary", "") or getattr(entry, "description", "")

            # 清洗 html 标签
            soup = BeautifulSoup(summary, "html.parser")
            clean_text = soup.get_text(separator="\n", strip=True)

            # 抽取潜在海报图片
            img_urls = [img["src"] for img in soup.find_all("img") if img.get("src")]

            results.append({
                "title": title,
                "url": url,
                "clean_text": clean_text,
                "image_urls": img_urls
            })
        return results

    @classmethod
    async def fetch_article_content(cls, url: str) -> Dict[str, any]:
        """抓取单篇网页/公众号并提取正文与图片"""
        async with httpx.AsyncClient(timeout=15.0, headers=cls.DEFAULT_HEADERS, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text

        soup = BeautifulSoup(html, "html.parser")

        # 针对微信公众号专有正文容器及通用文章标签清洗
        content_elem = soup.find(id="js_content") or soup.find("article") or soup.find("main") or soup.body
        title_elem = soup.find("h1") or soup.find("title")

        title = title_elem.get_text(strip=True) if title_elem else "未命名推文"

        # 提取全部图片
        images = []
        if content_elem:
            for img in content_elem.find_all("img"):
                src = img.get("data-src") or img.get("src")
                if src and src.startswith("http"):
                    images.append(src)
            text = content_elem.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)

        return {
            "title": title,
            "text": text,
            "raw_html": html,
            "image_urls": images
        }
