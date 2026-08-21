#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""novel/ の各話を、一冊の小説 book/ひとりずつ.md に組む。"""
import io, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "novel")
OUT = os.path.join(ROOT, "book", "ひとりずつ.md")

KAN = "〇一二三四五六七八九"

ACTS = [
    ("第一幕", "ミクロ", [
        ("一章", "落ちる", 1, 5),
        ("二章", "ふえる", 6, 11),
        ("三章", "こえる", 12, 16),
        ("四章", "あたま", 17, 21),
    ]),
    ("第二幕", "マクロ", [
        ("五章", "そと", 22, 28),
        ("六章", "あかり", 29, 36),
        ("七章", "くちづけ", 37, 42),
        ("八章", "まちが変わる", 43, 48),
    ]),
    ("第三幕", "邂逅と星々", [
        ("九章", "女王", 49, 53),
        ("十章", "降臨", 54, 59),
        ("十一章", "超科学", 60, 63),
        ("十二章", "まだ向こう", 64, 66),
    ]),
]

FRONT = """# ひとりずつ

> だれか、こないかなあ。

"""

BACK = """
---

## 覚え書き

### 読み方について

この物語には、三つの大きさがある。

第一幕は、**一つの身体の中**の話である。
そこに出てくる「まち」は臓器であり、「流れ」は血であり、
「かべ」は器官の縁である。歩いている者は、細胞ほどの大きさしかない。

第二幕は、**その身体を持っていた人**の話になる。
第一幕の終わりで内側が終わり、そこではじめて外側が動きはじめる。

第三幕は、**その先**である。

三つの大きさは、混ざらない。
同じ言葉が出てくるが、指しているものは別である。

### 繰り返しについて

同じ形の場面が、何度も出てくる。

一人になる。耐えられなくなる。手を伸ばす。応えが返る。薄れた気がする。
しばらくして、また立ち上がる。

これは書き癖ではない。
**この物語で起きていることは、それ一つだけである。**
大きさと、数と、渡す速さだけが変わっていく。

### 設定について

この物語の世界の細部は、別に一冊にまとめてある。
`book/セラ大全.md` がそれである。

ここに書いたことは、そのすべてに従っている。
食い違いがあれば、あちらが正しい。

### 一冊目について

同じ世界を、細胞の側から、言葉を削って書いたものがある。
`book/archive/応え.md` がそれである。

本書とは、書きかたが違う。読む順序は問わない。
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
    files = sorted(p for p in os.listdir(SRC) if re.match(r"^\d\d-.*\.md$", p))
    chapters = {}
    for name in files:
        n = int(name[:2])
        text = io.open(os.path.join(SRC, name), encoding="utf-8").read()
        head, body = text.split("\n", 1)
        title = re.sub(r"^#\s*第.+?話\s*", "", head).strip()
        chapters[n] = (title, body.strip())

    toc = ["## 目次\n"]
    parts = []
    for act, act_name, chaps in ACTS:
        if not any(lo in chapters for _, _, lo, _ in chaps):
            continue
        parts.append("## %s　%s\n" % (act, act_name))
        toc.append("### %s　%s\n" % (act, act_name))
        for label, name, lo, hi in chaps:
            got = [n for n in range(lo, hi + 1) if n in chapters]
            if not got:
                continue
            parts.append("### %s　%s\n" % (label, name))
            toc.append("**%s　%s**\n" % (label, name))
            for n in got:
                title, body = chapters[n]
                parts.append("#### %s　%s\n\n%s\n" % (kanji(n), title, body))
                toc.append("%s　%s" % (kanji(n), title))
            toc.append("")

    io.open(OUT, "w", encoding="utf-8").write(
        FRONT + "---\n\n" + "\n".join(toc) + "\n---\n\n"
        + "\n".join(parts) + BACK)

    chars = len(re.sub(r"\s", "", io.open(OUT, encoding="utf-8").read()))
    print("book/ひとりずつ.md: %s 話 / %s 字" % (len(chapters), format(chars, ",")))


if __name__ == "__main__":
    main()
