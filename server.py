import json
import os
import random
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"
ARK_API_URL = "https://ark.cn-beijing.volces.com/api/v3/responses"


def load_local_env():
    if not ENV_FILE.exists():
        return

    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_local_env()

ARK_API_KEY = os.environ.get("ARK_API_KEY")
ARK_MODEL = os.environ.get("ARK_MODEL", "deepseek-v3-2-251201")

FACTS_TEXT = """🏫关于加州多明尼克大学
加州多明尼克大学（Dominican University of California），建校于1890年，是一所坐落于加利福尼亚州的、拥有超过百年历史的学府。2021年加州多明尼克大学在QS世界大学排名中位列 美国大学第171名，在US News美国西部大学中位列第18位，并被《美国新闻与世界报道》评为“美国西部最佳大学”之一。2020-2021年，加州多明尼克大学因其学生优异、教学成果卓著，再次被评为杰出学校（College of Distinction），其在四个特定领域（包括博思凯商学院）的创新成就也获得了专业认可。

🎓加州多明尼克大学
1. 全球5%拥有AACSB认证的大学
2. 美国西部教育署WASC认证
3. GradReports薪资全美大学第10位
4. US News排名美国西部18名，最有价值的大学第20名
5. QS全美排名171名，全美top4%名校

📸我们的闪光点
1. 美国教育委员会评价加州多明尼克大学为“全美最具变革性的四年制大学”
2. 加州多明尼克大学MBA项目结合了暨南大学的管理学专业优势和加州多明尼克大学的国际化视野培养
3. 个性化的、高度实践性和体验性的教育模式
4. 国际校友资源遍布全球各地，共计17000+人次

☑️MBA项目方向
1. MBA（全球战略和领导力）
2. 人工智能 AI artificial intelligence
3. 医疗健康 Healthcare"""

FIXED_TAGS = "#加州多明尼克大学  #加州多明尼克大学开学季  #开学典礼  #在职硕士  #在职研究生  #MBA  #在线硕士  #开学季"

TITLE_VARIATIONS = {
    "ceremony": [
        "从开学典礼看学校",
        "开学典礼后的判断",
        "开学典礼里的学校气质",
        "开学典礼看出什么",
        "开学典礼值不值得看",
    ],
    "reliable": [
        "加州多明尼克大学靠谱吗",
        "加州多明尼克大学靠不靠谱",
        "多明尼克大学是否靠谱",
        "这所学校到底靠不靠谱",
        "读多明尼克大学值吗",
    ],
}

STYLE_VARIATIONS = [
    "更像在职校友的真实复盘，语气克制、有判断。",
    "更像小红书经验分享，语气自然、有代入感。",
    "更像成熟职场人的留学观察，信息密度高一些。",
    "更像开学季真实见闻，带一点现场感，但不浮夸。",
]


def extract_text(response_json):
    if response_json.get("output_text"):
        return response_json["output_text"]

    parts = []
    for item in response_json.get("output", []):
      if item.get("type") != "message":
          continue
      for content in item.get("content", []):
          if content.get("type") in {"output_text", "text"}:
              text = content.get("text") or content.get("value")
              if text:
                  parts.append(text)
    return "\n".join(parts).strip()


def build_prompt():
    theme = random.choice(["ceremony", "reliable"])
    seed_title = random.choice(TITLE_VARIATIONS[theme])
    style_hint = random.choice(STYLE_VARIATIONS)
    nonce = random.randint(100000, 999999)

    return f"""你要生成一篇用于小红书发布的中文内容，必须输出 JSON，不要输出 Markdown 代码块。

目标：
1. 生成一个标题，标题必须围绕以下两条线之一展开：A. 加州多明尼克大学开学典礼；B. 加州多明尼克大学是否靠谱。
2. 标题长度不能超过20个汉字或等效字符。
3. 正文必须以“在线硕士校友”的第一人称口吻来写，以在职人的体验为主。
4. 每次生成都要明显不同，不能只是换几个词。请参考本次随机变化提示：{style_hint}
5. 不要写任何“欢迎私信”“留言”“进一步沟通”“咨询我”之类的引导。
6. 不要编造院校事实，只能使用我提供的真实信息。
7. 文案结尾的话题固定为：{FIXED_TAGS}
8. 输出结构必须是 JSON：{{"title":"...","body":"...","tags":"..."}}
9. title 可以参考但不能照抄这个随机起点：{seed_title}
10. 为了保证本次与其他版本不同，请将本次变体编号隐含参考为：{nonce}，但不要在最终文案里输出编号。

真实院校信息如下：
{FACTS_TEXT}

正文要求：
1. 首段先说明自己是在线硕士校友，并从在职人的角度切入。
2. 中段要自然带出学校排名、认证、项目亮点、校友资源、MBA方向中的关键信息。
3. 内容要像真实分享，不要像官网宣传稿，不要堆砌 bullet。
4. 正文不要重复输出标题。
5. body 最后一行不要再追加别的话，只保留固定 tags 前的正文收尾。
"""


def call_api(payload):
    request = urllib.request.Request(
        ARK_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {ARK_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_plain_text(raw_text):
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("Model returned empty text.")

    title = lines[0][:20]
    body = "\n".join(lines[1:]).strip()
    if not body:
        raise RuntimeError("Model returned no body content.")

    body = body.replace(FIXED_TAGS, "").strip()
    return {
        "title": title,
        "body": body,
        "tags": FIXED_TAGS,
    }


def build_structured_payload():
    return {
        "model": ARK_MODEL,
        "stream": False,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": build_prompt(),
                    }
                ],
            }
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "xiaohongshu_copy",
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "title": {"type": "string"},
                        "body": {"type": "string"},
                        "tags": {"type": "string"},
                    },
                    "required": ["title", "body", "tags"],
                },
                "strict": True,
            }
        },
    }


def build_plain_payload():
    prompt = build_prompt() + '\n请按以下纯文本格式输出：\n标题：xxx\n正文：xxx'
    return {
        "model": ARK_MODEL,
        "stream": False,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt,
                    }
                ],
            }
        ],
    }


def call_model():
    if not ARK_API_KEY:
        raise RuntimeError("Missing ARK_API_KEY environment variable.")

    try:
        response_json = call_api(build_structured_payload())
        raw_text = extract_text(response_json)
        result = json.loads(raw_text)
    except Exception:
        response_json = call_api(build_plain_payload())
        raw_text = extract_text(response_json)
        raw_text = raw_text.replace("标题：", "", 1) if raw_text.startswith("标题：") else raw_text
        if "\n正文：" in raw_text:
            title, body = raw_text.split("\n正文：", 1)
            result = {
                "title": title.strip(),
                "body": body.strip(),
                "tags": FIXED_TAGS,
            }
        else:
            result = parse_plain_text(raw_text)

    result["title"] = result["title"].strip()[:20]
    result["tags"] = FIXED_TAGS
    return result


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def do_POST(self):
        if self.path != "/api/generate":
            self.send_error(404, "Not found")
            return

        try:
            result = call_model()
            body = json.dumps({"ok": True, "result": result}, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            body = json.dumps(
                {"ok": False, "error": f"API error: {exc.code}", "detail": detail},
                ensure_ascii=False,
            ).encode("utf-8")
            self.send_response(502)
        except Exception as exc:
            body = json.dumps(
                {"ok": False, "error": str(exc)},
                ensure_ascii=False,
            ).encode("utf-8")
            self.send_response(500)

        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), AppHandler)
    print(f"Serving on http://{HOST}:{PORT}")
    server.serve_forever()
