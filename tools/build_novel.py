#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""story/ の各話を、一冊の小説 book/応え.md に組む。"""
import io, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORY = os.path.join(ROOT, "story")
OUT = os.path.join(ROOT, "book", "archive", "応え.md")

KAN = "〇一二三四五六七八九"

PARTS = [
    (1,  5,  "第一部", "器"),
    (6,  18, "第二部", "声"),
    (19, 22, "第三部", "渡る"),
    (23, 29, "第四部", "外"),
    (None, "01-まちの一日.md", "幕間", "まちの一日"),
    (30, 32, "第五部", "ふえる"),
    (33, 39, "第六部", "なりわい"),
    (None, "02-かさなって.md", "幕間", "かさなって"),
    (40, 43, "第七部", "おとす"),
    (None, "03-みっかめ.md", "幕間", "みっかめ"),
    (44, 47, "第八部", "ちから"),
    (48, 53, "第九部", "ぜんぶ"),
    (54, 57, "第十部", "そだつ"),
    (58, 60, "第十一部", "女王"),
    (61, 62, "第十二部", "降臨"),
    (63, 66, "第十三部", "そら"),
]

FRONT = """# 応え

> 宇宙のどこかで、何かが一つを選んだ。
> 理由はなかった。必要でもなかった。

"""

BACK = """
---

## 覚え書き

### 読み方について

この物語には、二つの大きさがある。

第一部から第四部までは、**一つの身体の中**の話である。
そこに出てくる「まち」は臓器であり、「流れ」は血であり、
「壁」は器官の縁である。歩いている者は、細胞ほどの大きさしかない。

第五部から先は、**その身体を持っていた人**の話である。
第四部の終わりで内側が完成し、そこではじめて外側が動きはじめる。

二つの大きさは、混ざらない。
同じ言葉が両方に出てくるが、指しているものは別である。

### 大きさについて

部が進むごとに、扱う大きさが一段ずつ上がる。

| 部 | 大きさ |
| --- | --- |
| 一〜四 | 一つの身体の中 |
| 五 ふえる | 一つの街 |
| 六 なりわい | 一つの国 |
| **七 おとす** | **一人ずつ**（ここだけ、桁が下がる） |
| 八 ちから | 一つの国 |
| 九 ぜんぶ | 地球 |
| 十 そだつ | 地球（人間がいなくなったあと） |
| 十一 女王 | 地球 |
| 十二 降臨 | 太陽系 |
| 十三 そら | 全宇宙 |

第七部だけが、桁を下げる。
いちばん大きくなる直前に、いちばん小さいところへ一度戻すためである。

### 幕間について

三つある。番号を持たない。

本編は「次に何が起きるか」で進むが、
幕間は次に何も起こらなくてよい。暮らしのほうだけを書いてある。

読み飛ばしても、本編は繋がる。

### 繰り返しについて

同じ形の場面が、何度も出てくる。

行き場のなくなった者が、隣へ手を伸ばす。
伸ばした先が、応える。温かくなる。満ちる。
そして、しばらくすると、また誰かのそばへ行きたくなる。

これは書き癖ではない。**この物語で起きていることは、それ一つだけである。**
大きさと、数と、渡す速さだけが変わっていく。

### 設定について

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

    toc = ["## 目次\n"]
    parts = []
    for lo, hi, label, name in PARTS:
        parts.append("## %s　%s\n" % (label, name))
        toc.append("**%s　%s**\n" % (label, name))
        if lo is None:
            text = io.open(os.path.join(STORY, "幕間", hi),
                           encoding="utf-8").read().split("\n", 1)[1].strip()
            parts.append(text + "\n")
            continue
        for n in range(lo, hi + 1):
            if n not in chapters:
                continue
            title, body = chapters[n]
            parts.append("### %s　%s\n\n%s\n" % (kanji(n), title, body))
            toc.append("%s　%s" % (kanji(n), title))
        toc.append("")

    io.open(OUT, "w", encoding="utf-8").write(
        FRONT + "---\n\n" + "\n".join(toc) + "\n---\n\n"
        + "\n".join(parts) + BACK)

    chars = len(re.sub(r"\s", "", io.open(OUT, encoding="utf-8").read()))
    print("book/archive/応え.md: %s 話 / %s 字" % (len(chapters), format(chars, ",")))


if __name__ == "__main__":
    main()
