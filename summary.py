import feedparser
import os
import requests
import json
from datetime import datetime
from openai import OpenAI

# ============ 配置区域（请务必修改）============
# WxPusher配置（从官网获取）
APP_TOKEN = "AT_Ap3x5LvAFoh2CiFkTtvdPe0JumhXaoJm"      # 替换成你的AppToken
TARGET_UID = "UID_YrzfdAKFDnUyaJAQQNmk5FIMzYq1"    # 替换成你的UID

# DeepSeek API配置
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

# 调试：检查是否读取到了API Key（仅用于排查问题，运行正常后可删除）
if not DEEPSEEK_API_KEY:
    print("❌ 错误：未读取到 DEEPSEEK_API_KEY 环境变量")
    print("请检查 GitHub Secrets 中是否设置了 DEEPSEEK_API_KEY")
    exit(1)
else:
    print(f"✅ 已读取到 API Key，长度：{len(DEEPSEEK_API_KEY)} 字符")

# RSS源列表
RSS_FEEDS = [
    "https://www.jiqizhixin.com/rss",
    "https://www.qbitai.com/feed",
    "https://rss.arxiv.org/rss/cs.AI",
    "https://rss.arxiv.org/rss/cs.LG",
    "https://huggingface.co/blog/feed.xml",
]

# ============ 抓取新闻 ============
def fetch_news():
    """从所有RSS源抓取最新文章"""
    all_articles = []
    seen_titles = set()
    
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                if entry.title in seen_titles:
                    continue
                seen_titles.add(entry.title)
                all_articles.append({
                    "title": entry.title,
                    "link": entry.link,
                    "source": feed.feed.title if hasattr(feed.feed, 'title') else "未知来源"
                })
        except Exception as e:
            print(f"抓取 {feed_url} 失败: {e}")
            continue
    
    return all_articles

# ============ 调用DeepSeek生成摘要 ============
def generate_summary(articles):
    """使用DeepSeek API生成每日摘要"""
    if not articles:
        return "今日未抓取到AI相关资讯，请检查RSS源是否可用。"
    
    # 构建待总结的文本
    news_text = ""
    for i, article in enumerate(articles[:20], 1):
        news_text += f"{i}. {article['title']}\n   {article['link']}\n"
    
    system_prompt = """你是一个专业的AI资讯助手。请将以下新闻整理成一份简洁的每日摘要。

要求：
1. 按重要性排序（重大模型发布 > 技术突破 > 行业应用 > 其他）
2. 每条新闻用一句话概括，不超过30字
3. 在每条摘要前用【】标注类别，如【模型发布】【技术研究】【行业动态】
4. 末尾附上"今日重点关注"

输出格式示例：
【模型发布】OpenAI发布GPT-4o，支持实时语音交互
【技术研究】谷歌推出新算法，大模型推理速度提升3倍

今日重点关注：OpenAI GPT-4o的发布标志着多模态交互进入新阶段。"""

    # 创建客户端时明确传入api_key
    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,  # 直接使用变量，不再从环境变量读取
        base_url="https://api.deepseek.com"
    )
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",  # 使用稳定版本
            # model="deepseek-v4-pro",  # 或 deepseek-chat（即将弃用）
            # model="deepseek-chat",  # 使用稳定版本
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"今日AI资讯列表（共{len(articles)}条）：\n\n{news_text}"}
            ],
            temperature=0.3,
            max_tokens=800,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"生成摘要时出错：{str(e)}"

# ============ 通过WxPusher推送到微信 ============
def send_to_wechat(summary, article_count):
    """使用WxPusher的Web API推送消息"""
    today = datetime.now().strftime("%Y年%m月%d日")
    
    full_content = f"## 📰 AI每日资讯摘要 - {today}\n\n"
    full_content += f"📊 共抓取 {article_count} 条资讯\n\n"
    full_content += "---\n\n"
    full_content += summary
    full_content += "\n\n---\n"
    full_content += "🤖 由 DeepSeek API + WxPusher 自动生成"
    
    api_url = "http://wxpusher.zjiecode.com/api/send/message"
    
    data = {
        "appToken": APP_TOKEN,
        "content": full_content,
        "summary": f"AI日报 - {today}",
        "contentType": 2,
        "uids": [TARGET_UID],
    }
    
    try:
        response = requests.post(api_url, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 1000:
                print("✅ 微信推送成功！")
            else:
                print(f"⚠️ 推送失败：{result}")
        else:
            print(f"⚠️ HTTP请求失败，状态码：{response.status_code}")
    except Exception as e:
        print(f"❌ 推送异常：{e}")

# ============ 主函数 ============
def main():
    print("🚀 开始抓取AI资讯...")
    articles = fetch_news()
    print(f"📥 共抓取到 {len(articles)} 条资讯")
    
    print("🧠 正在调用DeepSeek生成摘要...")
    summary = generate_summary(articles)
    print("✅ 摘要生成完成")
    
    print("📤 正在推送到微信...")
    send_to_wechat(summary, len(articles))
    print("🎉 全部流程执行完毕！")

if __name__ == "__main__":
    main()
