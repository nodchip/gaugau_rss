from flask import Flask, Response, request
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

app = Flask(__name__)


def fetch_comic(work_id):
    url = f"https://gaugau.futabanex.jp/list/work/{work_id}"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")

    title_tag = soup.find("title")
    comic_title = title_tag.text

    description_element = soup.find("meta", attrs={"name": "description"})
    comic_description = description_element.attrs["content"]

    comic = {
        "title": comic_title,
        "description": comic_description,
    }

    # ↓↓↓ ページ構造によってこの部分を修正してください ↓↓↓
    episodes = []
    for ep in soup.find_all(
        "div", class_="episode__grid"
    ):  # ここは実際のclass名に合わせて修正
        episode = dict()

        a_tag = ep.find("a")
        link = a_tag.attrs["href"]
        episode["link"] = link
        episode["id"] = link

        episode_num_element = a_tag.find("div", class_="episode__num")
        episode_title_element = a_tag.find("div", class_="episode__title")
        title = f"{episode_num_element.text} {episode_title_element.text}"
        title = title.strip()
        episode["title"] = title

        span_tag = a_tag.find("span")
        if not span_tag:
            continue
        date_str = span_tag.text
        try:
            pub_date = datetime.strptime(date_str, "%Y年%m月%d日 更新")
            pub_date = pub_date.replace(tzinfo=ZoneInfo("Asia/Tokyo"))
            episode["date"] = pub_date
        except:
            continue

        episodes.append(episode)
    return comic, episodes


@app.route("/rss/<work_id>")
def rss_feed(work_id):
    comic, episodes = fetch_comic(work_id)
    if not episodes:
        return Response("No episodes found or parsing error.", status=404)
    fg = FeedGenerator()
    fg.title(comic["title"])
    fg.link(href=f"https://gaugau.futabanex.jp/list/work/{work_id}")
    fg.description(comic["description"])
    for ep in episodes:
        fe = fg.add_entry()
        fe.id(ep["id"])
        fe.title(ep["title"])
        fe.link(href=ep["link"])
        if "date" in ep:
            fe.published(ep["date"])
    rss_feed = fg.rss_str(pretty=True)
    return Response(rss_feed, mimetype="application/rss+xml")


if __name__ == "__main__":
    app.run(debug=True, port=8080)
