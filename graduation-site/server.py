import json
import os
import random
import re
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"
GRAD_API_URL = os.environ.get("GRAD_API_URL", "https://ark.cn-beijing.volces.com/api/v3/responses")


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

GRAD_API_KEY = os.environ.get("GRAD_API_KEY")
GRAD_MODEL = os.environ.get("GRAD_MODEL", "doubao-seed-2-0-lite-260215")

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

FIXED_TAGS = "#加州多明尼克大学 #毕业典礼 #人工智能 #人工智能硕士 #布克终身学习 #布克硕博 #AI #毕业季"

TITLE_VARIATIONS = {
    "graduation": [
        "毕业典礼后的实感",
        "毕业这一刻很具体",
        "毕业典礼看到的变化",
        "毕业不是句号",
        "毕业这一刻我在想什么",
    ],
    "reflection": [
        "为什么选这所学校",
        "读完后的真实感受",
        "这一段读研值不值",
        "毕业后回看这段选择",
        "这段硕士经历带来了什么",
    ],
}

STYLE_VARIATIONS = [
    "更像本人随手写下的毕业笔记，语气自然。",
    "更像毕业典礼当天的真实记录，不夸张。",
    "更像读完硕士后的复盘分享，句子短一点。",
    "更像小红书里的真实经验贴，不要官方语气。",
]

ANGLE_POOL = {
    "当初选择学校的原因": "写自己当初为什么选择加州多明尼克大学。",
    "硕士期间的知识收获": "写专业提升、项目实践或方法论上的收获。",
    "硕士期间的人脉收获": "写同学、教授、行业资源带来的变化。",
    "对终身学习的最新感悟": "写现在对持续学习的理解，比如学习是长期投资。",
    "对AI行业发展趋势的思考": "写自己对 AI 行业方向的观察和判断。",
    "对未来的规划与展望": "写毕业后的下一步计划和目标。",
}

def extract_text(response_json):
    if response_json.get("output_text"):
        return response_json["output_text"]

    parts = []
    for item in response_json.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            text = None
            if content.get("type") in {"output_text", "text", "input_text"}:
                text = content.get("text") or content.get("value")
            elif isinstance(content.get("text"), str):
                text = content.get("text")
            if text:
                parts.append(text)
    return "\n".join(parts).strip()


def build_prompt():
    theme = random.choice(["graduation", "reflection"])
    seed_title = random.choice(TITLE_VARIATIONS[theme])
    style_hint = random.choice(STYLE_VARIATIONS)
    angle_count = random.randint(2, 3)
    selected_angles = random.sample(list(ANGLE_POOL.items()), angle_count)
    angle_lines = "\n".join(
        f"- {name}：{desc}" for name, desc in selected_angles
    )
    nonce = random.randint(100000, 999999)

    return f"""你要生成一篇用于小红书发布的中文内容，必须输出 JSON，不要输出 Markdown 代码块。

目标：
1. 生成一个标题，标题必须围绕毕业典礼、硕士收获、学校选择或未来规划中的任一条线展开。
2. 标题长度不能超过20个汉字或等效字符。
3. 正文必须以第一人称来写，像本人随手写的毕业笔记，口吻自然、真实、轻口语。
4. 每次生成都要明显不同，不能只是换几个词。请参考本次随机变化提示：{style_hint}
5. 不要写任何“欢迎私信”“留言”“进一步沟通”“咨询我”之类的引导。
6. 不要编造院校事实，只能使用我提供的真实信息。
7. 文案结尾的话题固定为：{FIXED_TAGS}
8. 输出结构必须是 JSON：{{"title":"...","body":"...","tags":"..."}}
9. title 可以参考但不能照抄这个随机起点：{seed_title}
10. 为了保证本次与其他版本不同，请将本次变体编号隐含参考为：{nonce}，但不要在最终文案里输出编号。
11. body 正文必须控制在 300 字以内。
12. 本次只围绕下面随机抽取的方向来写，不要把所有方向都写全：
{angle_lines}

真实院校信息如下：
{FACTS_TEXT}

正文要求：
1. 内容要像真实分享，不要像官网宣传稿，不要堆砌 bullet。
2. 必须只围绕本次抽到的 2 到 3 个方向展开，其他未抽到的方向可以不写。
3. 不要抒情过度，不要鸡汤，不要宣传片语气，不要写得文绉绉。
4. 句子尽量短一点，表达直接一点，像真实发帖，不像官方介绍。
5. 要有毕业阶段的真实感，可以出现毕业典礼现场、阶段总结、下一步计划等内容。
6. 可以带少量真实院校亮点，但不要写成大段资料罗列。
7. 正文不要重复输出标题。
8. body 最后一行不要再追加别的话，只保留固定 tags 前的正文收尾。
"""


def call_api(payload):
    request = urllib.request.Request(
        GRAD_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {GRAD_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_plain_text(raw_text):
    raw_text = raw_text.strip()
    if not raw_text:
        raise RuntimeError("Model returned empty text.")

    cleaned = raw_text.strip("` \n")
    if cleaned.startswith("{") and cleaned.endswith("}"):
        try:
            parsed = json.loads(cleaned)
            title = str(parsed.get("title", "")).strip()[:20]
            body = str(parsed.get("body", "")).replace(FIXED_TAGS, "").strip()
            if body:
                return {
                    "title": title or "毕业典礼后的实感",
                    "body": body,
                    "tags": FIXED_TAGS,
                }
        except json.JSONDecodeError:
            pass

    title_match = re.search(r"标题[:：]\s*(.+)", raw_text)
    body_match = re.search(r"正文[:：]\s*([\s\S]+?)(?:\n?话题[:：][\s\S]*)?$", raw_text)

    if title_match and body_match:
        title = title_match.group(1).strip()[:20]
        body = body_match.group(1).replace(FIXED_TAGS, "").strip()
        if body:
            return {
                "title": title or "毕业典礼后的实感",
                "body": body,
                "tags": FIXED_TAGS,
            }

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    title = ""
    body = ""

    if len(lines) >= 2:
        title = re.sub(r"^标题[:：]\s*", "", lines[0]).strip()[:20]
        body = "\n".join(
            re.sub(r"^(正文|话题)[:：]\s*", "", line).strip()
            for line in lines[1:]
            if not line.startswith("话题")
        ).replace(FIXED_TAGS, "").strip()
    elif len(lines) == 1:
        single = re.sub(r"^标题[:：]\s*", "", lines[0]).strip()
        if "。 " in single:
            sentence_parts = single.split("。 ", 1)
            title = sentence_parts[0].strip()[:20]
            body = sentence_parts[1].strip()
        else:
            title = single[:20]
            body = single

    body = body.replace(FIXED_TAGS, "").strip()
    if not title:
        title = "毕业典礼后的实感"
    return {
        "title": title,
        "body": body,
        "tags": FIXED_TAGS,
    }


def build_plain_payload():
    prompt = build_prompt() + (
        "\n请按以下纯文本格式输出：\n"
        "标题：xxx\n"
        "正文：xxx\n"
        "话题：" + FIXED_TAGS
    )
    return {
        "model": GRAD_MODEL,
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
    if not GRAD_API_KEY:
        raise RuntimeError("Missing GRAD_API_KEY environment variable.")

    response_json = call_api(build_plain_payload())
    raw_text = extract_text(response_json)
    raw_text = raw_text.strip()
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
