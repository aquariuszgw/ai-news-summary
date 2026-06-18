import feedparser
import openai
import os

# 你要订阅的RSS源列表
rss_feeds = [
    "https://www.jiqizhixin.com/rss",  # 机器之心
    "https://www.qbitai.com/feed",     # 量子位
    "https://rss.arxiv.org/rss/cs.AI", # arXiv AI论文
]

# 抓取所有文章
all_news = []
for feed_url in rss_feeds:
    feed = feedparser.parse(feed_url)
    for entry in feed.entries[:5]:  # 每个源取最新5条
        all_news.append(f"{entry.title}\n{entry.link}")

# 让AI生成摘要
client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "你是一个AI资讯助手。请将以下新闻整理成一份简洁的每日摘要，按重要性排序，每条不超过20字。"},
        {"role": "user", "content": "\n\n".join(all_news)}
    ]
)

summary = response.choices[0].message.content
print(summary)

# 这里可以添加推送逻辑（如发邮件、推送到飞书/钉钉/微信）
