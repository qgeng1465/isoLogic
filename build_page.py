#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把仓库里那份 README 渲染成 GitHub Pages 首页。

为什么在本地烤成 HTML 而不是前端拉取后渲染：Pages 只发静态文件，没有一个
「GitHub 的 markdown 渲染器」可用；写成前端渲染就得依赖 CDN 上的 marked，
评委那台机器一断外网就白屏。这里一次性烤好，页面自包含。

跑法（先改 README_SRC 或直接传参）：
    python3 build_page.py README.source.md

正文一字不改，只做两件机械处理：
  1. 相对链接改写 —— 仓库文件（docs/…、demo/…）在 Pages 上打不开，
     改成指向源仓库对应提交的绝对地址；
  2. 演示视频入口 —— 视频播放页在 /video/，顶部横幅里给一个入口。
"""
import re
import sys
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "README.source.md"
OUT = HERE / "index.html"

# 这份 README 的来源（写进页面页脚，方便对账）
REPO = "Scarlett-yzy/logic-coloc"
REF = "main"
RAW = f"https://raw.githubusercontent.com/{REPO}/{REF}"
BLOB = f"https://github.com/{REPO}/blob/{REF}"

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>知源 · 跨学科知识同源翻译机</title>
<style>
  :root {{ --ink:#1c2b3a; --dim:#66788a; --line:#dbe5ee; --bg:#f4f7fa; --card:#fff; --accent:#2f6fb0; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; padding:28px 16px 60px; background:var(--bg); color:var(--ink);
         font:15.5px/1.75 -apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC","PingFang SC","Microsoft YaHei",sans-serif; }}
  .wrap {{ max-width:820px; margin:0 auto; background:var(--card); border:1px solid var(--line);
           border-radius:14px; padding:26px 30px 34px; box-shadow:0 1px 2px rgba(28,43,58,.04); }}
  .banner {{ display:flex; flex-wrap:wrap; gap:8px 16px; align-items:center; justify-content:space-between;
             margin:0 0 22px; padding:11px 15px; border-radius:10px; font-size:13.5px;
             background:#eaf2f9; border:1px solid #cfe0ee; color:#31556f; }}
  .banner a {{ color:var(--accent); font-weight:600; text-decoration:none; }}
  .banner a:hover {{ text-decoration:underline; }}
  h1 {{ font-size:25px; line-height:1.4; margin:.2em 0 .7em; padding-bottom:.3em; border-bottom:1px solid var(--line); }}
  h2 {{ font-size:20px; margin:1.6em 0 .6em; padding-bottom:.25em; border-bottom:1px solid var(--line); }}
  h3 {{ font-size:16.5px; margin:1.3em 0 .5em; }}
  h4 {{ font-size:15px; margin:1.1em 0 .4em; }}
  p {{ margin:.65em 0; }}
  a {{ color:var(--accent); }}
  code {{ background:#f2f6f9; border:1px solid #e2ebf1; border-radius:4px; padding:.08em .35em;
          font-size:.88em; font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }}
  pre {{ background:#f6f9fb; border:1px solid var(--line); border-radius:9px; padding:12px 14px; overflow:auto; }}
  pre code {{ background:none; border:none; padding:0; font-size:12.8px; line-height:1.6; }}
  blockquote {{ margin:.8em 0; padding:.5em 1em; border-left:3px solid #cfe0ee; background:#f7fafc;
                color:#4a6070; border-radius:0 8px 8px 0; }}
  blockquote p {{ margin:.35em 0; }}
  table {{ border-collapse:collapse; width:100%; margin:1em 0; font-size:14px; }}
  th, td {{ border:1px solid #d7e3ec; padding:7px 10px; text-align:left; vertical-align:top; }}
  th {{ background:#eaf3f9; color:#173b63; }}
  img {{ max-width:100%; }}
  hr {{ border:none; border-top:1px solid var(--line); margin:1.8em 0; }}
  ul, ol {{ padding-left:1.5em; }}
  li {{ margin:.28em 0; }}
  footer {{ margin-top:30px; padding-top:14px; border-top:1px solid var(--line); color:var(--dim); font-size:12.5px; }}
  @media (max-width:560px) {{ .wrap {{ padding:18px 16px 26px; }} }}
</style>
</head>
<body>
<div class="wrap">
  <div class="banner">
    <span>本页是仓库 <a href="https://github.com/{repo}">{repo}</a> 的 README 渲染版</span>
    <a href="video/">▶ 演示视频（2 分 10 秒）</a>
  </div>
{body}
  <footer>
    正文来自 <a href="{blob}/README.md">{repo}@{ref}</a>（提交 <code>{sha}</code>），未改一字；
    仅把仓库内相对链接改写为绝对地址，页首加了视频入口。页面由 qgeng1465 发布。
  </footer>
</div>
</body>
</html>
"""


def github_slugify(value: str, separator: str) -> str:
    """按 GitHub 的规则生成标题锚点。

    python-markdown 自带的 slugify 会把非 ASCII 全部丢掉，中文标题就变成 `_1`、`_2`、
    `3` 这种编号——README 里手写的「目录」全是 `#一评委-3-分钟怎么验` 这类中文锚点，
    一丢就整份目录点不动。这里照 github-slugger 的做法来：小写 → 去掉标点（保留中日韩、
    字母数字、空格、连字符）→ 空格换成分隔符。
    """
    value = value.strip().lower()
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    return re.sub(r"\s+", separator, value)


def rewrite(html: str) -> str:
    """仓库内相对链接 → 源仓库绝对地址。外链、锚点、绝对路径一律不动。"""
    def fix(m):
        attr, url = m.group(1), m.group(2)
        if re.match(r"^(https?:|mailto:|#|/)", url) or url.startswith("data:"):
            return m.group(0)
        return f'{attr}="{BLOB}/{url}"'

    return re.sub(r'(href|src)="([^"]+)"', fix, html)


def main() -> None:
    src = SRC.read_text(encoding="utf-8")
    sha = (HERE / "README.source.sha").read_text(encoding="utf-8").strip() \
        if (HERE / "README.source.sha").exists() else REF
    body = markdown.markdown(
        src,
        extensions=["tables", "fenced_code", "toc", "sane_lists", "attr_list", "md_in_html"],
        extension_configs={"toc": {"permalink": False, "slugify": github_slugify}},
    )
    OUT.write_text(
        TEMPLATE.format(body=rewrite(body), repo=REPO, ref=REF,
                        blob=BLOB, raw=RAW, sha=sha[:10]),
        encoding="utf-8",
    )
    print(f"写入 {OUT}（源 {len(src.splitlines())} 行 → {len(OUT.read_text(encoding='utf-8'))} 字节）")


if __name__ == "__main__":
    main()
