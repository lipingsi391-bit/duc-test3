# 毕业典礼版启动说明

这个目录是独立的毕业典礼网页版本：

- 页面入口：`index.html`
- 本地服务：`server.py`
- 独立环境变量：`GRAD_API_KEY` / `GRAD_MODEL` / `GRAD_API_URL`

## 1. 配置新 API

先复制配置模板：

```bash
cp .env.example .env
```

然后打开 `.env`，填入你新的 API：

```env
GRAD_API_KEY=你的毕业典礼版本APIKey
GRAD_MODEL=doubao-seed-2-0-lite-260215
GRAD_API_URL=https://ark.cn-beijing.volces.com/api/v3/responses
```

如果你后面要换成新的 provider，只需要改：

- `GRAD_API_KEY`
- `GRAD_MODEL`
- `GRAD_API_URL`

## 2. 本地启动

在这个目录运行：

```bash
python3 server.py
```

启动后访问：

```text
http://127.0.0.1:8000
```

## 3. 当前已完成的内容

- 顶部标题改成“美国加州多明尼克大学毕业典礼”
- 主按钮改成“我的专属毕业笔记”
- 主色切换为 `#fec612`
- 辅助色切换为 `#0e8dab`
- 文案方向切到毕业典礼场景
- 文案风格改成自然、真实、短句、非宣传片语气

## 4. 下一步

下一步最合适的事情就是把你新的 API 请求格式给我，我会把这个目录里的 `server.py` 改成对应接口版本。
