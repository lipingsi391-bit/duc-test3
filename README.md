# API 版启动说明

## 1. 配置 Ark API Key

推荐做法：复制一份本地配置文件。

```bash
cp .env.example .env
```

然后打开 `.env`，填入你自己的 key：

```env
ARK_API_KEY=你的真实ArkAPIKey
ARK_MODEL=deepseek-v3-2-251201
```

也可以不用 `.env`，直接在终端临时设置：

```bash
export ARK_API_KEY="你的真实ArkAPIKey"
export ARK_MODEL="deepseek-v3-2-251201"
```

## 2. 启动本地服务

在项目目录运行：

```bash
python3 server.py
```

启动后访问：

```text
http://127.0.0.1:8000
```

## 3. 页面行为

- 点击 `同频未来` 会调用 Ark Responses API
- 每次点击都会重新生成不同标题和文案
- 标题会围绕“开学典礼”或“加州多明尼克大学是否靠谱”展开
- 文案结尾话题固定不变

## 4. 注意

- 不要直接双击打开 `index.html`，API 版需要通过 `server.py` 启动
- 如果页面提示 `API 连接失败`，先检查服务是否启动，以及 `ARK_API_KEY` 是否已设置
- `.env` 是你本机专用配置，不建议把真实 key 写进代码文件里

## 5. 让所有设备都能访问

如果你希望“任何设备都能通过一个链接访问”，就不能只在自己电脑本地运行，必须把这个项目部署到公网服务器。

这个项目已经补了 [render.yaml](/Users/lipingsi/Documents/多大招生/render.yaml)，可以直接部署到 Render 这类平台：

1. 把项目上传到 GitHub
2. 在 Render 新建 `Blueprint` 或 `Web Service`
3. 连接你的 GitHub 仓库
4. 在平台环境变量里配置：

```env
ARK_API_KEY=你的真实ArkAPIKey
ARK_MODEL=deepseek-v3-2-251201
```

5. 部署成功后，平台会给你一个公开网址，所有设备都可以直接打开

说明：
- 这一步不一定需要先买域名
- 没买域名时，也会有一个平台默认链接
- 如果你以后想更正式，再绑定自己的域名即可
