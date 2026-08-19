#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""story/ の各話を、一冊の小説 book/応え.md に組む。"""
import io, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORY = os.path.join(ROOT, "story")
OUT = os.path.join(ROOT, "book", "応え.md")

KAN = "〇一二三四五六七八九"

PARTS = [
    (1,  5,  "第一部", "器"),
    (6,  18, "第二部", "声"),
    (19, 22, "第三部", "渡る"),
    (23, 29, "第四部", "外"),
    (30, 32, "第五部", "ふえる"),
    (33, 38, "第六部", "なりわい"),
    (39, 44, "第七部", "ちから"),
    (45, 46, "第八部", "女王"),
    (47, 48, "第九部", "降臨"),
    (49, 50, "第十部", "そら"),
]

FRONT = """# 応え

> 宇宙のどこかで、何かが一つを選んだ。
> 理由はなかった。必要でもなかった。

"""

BACK = """
---

## 覚え書き

この物語の世界の細部は、別に一冊にまとめてある。
`book/セラ大全.md` がそれである。

ここに書いたことは、そのすべてに従っている。
食い違いがあれば、あちらが正しい。
"""


def kanji(n):
    if n < 10:
        return KAN[n]
    if n == 10:
        return "十"
    if n < 20:
        return "十" + KAN[n % 10]
    t, o = divmod(n, 10)
    return KAN[t] + "十" + (KAN[o] if o else "")


def main():
    files = sorted(p for p in os.listdir(STORY) if re.match(r"^\d\d-.*\.md$", p))
    chapters = {}
    for name in files:
        n = int(name[:2])
        text = io.open(os.path.join(STORY, name), encoding="utf-8").read()
        head, body = text.split("\n", 1)
        title = re.sub(r"^#\s*第.+?話\s*", "", head).strip()
        chapters[n] = (title, body.strip())

    parts = []
    for lo, hi, label, name in PARTS:
        parts.append("## %s　%s\n" % (label, name))
        for n in range(lo, hi + 1):
            if n not in chapters:
                continue
            title, body = chapters[n]
            parts.append("### %s　%s\n\n%s\n" % (kanji(n), title, body))

    io.open(OUT, "w", encoding="utf-8").write(
        FRONT + "---\n\n" + "\n".join(parts) + BACK)

    chars = len(re.sub(r"\s", "", io.open(OUT, encoding="utf-8").read()))
    print("book/応え.md: %s 話 / %s 字" % (len(chapters), format(chars, ",")))


if __name__ == "__main__":
    main()
