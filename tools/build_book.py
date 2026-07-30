#!/usr/bin/env python3
"""セラ世界設定大全 — 分冊から一冊の本を組み上げる。

lore/sera/ に置かれた第 1〜8 巻と付録を、篇立て・目次つきの単一ファイルへ製本する。
出典ファイルは一切書き換えない。生成物は book/セラ大全.md のみ。

    python3 tools/build_book.py
"""

from __future__ import annotations

import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "lore" / "sera"
BOOK = ROOT / "book"
OUT = BOOK / "セラ大全.md"

# 出典側の見出しは # から ##### まで使われている。
# 篇の扉を # に据えるため、本文はすべて 1 段下げる（最大 ######）。
DEMOTE = 1


@dataclass
class Part:
    """篇。扉の題と、そこへ収める本文ファイル。"""

    numeral: str
    title: str
    lead: str
    sources: list[Path] = field(default_factory=list)


PARTS: list[Part] = [
    Part(
        "第一篇",
        "生命",
        "セラとは何か。何でできていて、何ができるのか。\n"
        "この篇を読まずに先へ進むと、以降のすべてが比喩に見えてしまう。",
        [SRC / "vol1-life-system.md", SRC / "vol2-body-and-abilities.md"],
    ),
    Part(
        "第二篇",
        "階梯",
        "セラ体系は二重である。この篇だけは、順番を飛ばして読んではならない。\n"
        "マクロとミクロを一本の図に混ぜた瞬間に、設定全体が崩れる。",
        [SRC / "vol3-evolution-and-hierarchy.md"],
    ),
    Part(
        "第三篇",
        "生と不死",
        "セラは死なない。それは祝福として書かれているが、\n"
        "この篇の終わりで、何も失われない世界が何を恐れているかが明かされる。",
        [SRC / "vol4-reproduction-and-immortality.md"],
    ),
    Part(
        "第四篇",
        "心",
        "情報を共有しても、個性は失われない。\n"
        "そして誰一人として、すべてを知ってはいない。女王を除いて。",
        [SRC / "vol5-information-mind-language.md"],
    ),
    Part(
        "第五篇",
        "起源",
        "本書の中核。ここに、セラがなぜこうであるかのすべてが書かれている。\n"
        "他の篇は、この篇の帰結にすぎない。",
        [SRC / "vol6-origin-love-consent.md"],
    ),
    Part(
        "第六篇",
        "文明",
        "満たされた者たちが、満たされたまま築いた社会。\n"
        "ここに書かれた幸福は、すべて本物である。",
        [SRC / "vol7-civilization.md"],
    ),
    Part(
        "第七篇",
        "世界",
        "星ひとつが、一体の気まぐれによって性質を変えていく過程。\n"
        "固定された「現在」は存在しない。これは、広がっていく途中の物語である。",
        [SRC / "vol8-world-history-future.md"],
    ),
    Part(
        "付録",
        "参照",
        "本文を読み終えたあとに引くためのもの。通読は要さない。",
        [SRC / "appendix-a-assimilation-ratios.md"],
    ),
]

FRONT = [BOOK / "front" / "01-扉.md", BOOK / "front" / "02-凡例.md"]
BACK = [BOOK / "back" / "appendix-b-invariants.md", BOOK / "back" / "99-後記.md"]


class Slugger:
    """GitHub 互換の見出しアンカーを、重複を避けながら振る。"""

    def __init__(self) -> None:
        self.seen: dict[str, int] = {}

    def slug(self, text: str) -> str:
        s = unicodedata.normalize("NFKC", text).strip().lower()
        s = re.sub(r"[*_`\[\]()<>]", "", s)          # 強調・リンク記法を落とす
        s = re.sub(r"[^\w\s　-鿿-]", "", s)  # 記号を落とす（CJK は残す）
        s = re.sub(r"[\s　]+", "-", s).strip("-")
        n = self.seen.get(s, 0)
        self.seen[s] = n + 1
        return s if n == 0 else f"{s}-{n}"


@dataclass
class Entry:
    level: int
    title: str
    anchor: str


def read(path: Path) -> str:
    if not path.exists():
        sys.exit(f"missing source: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8").strip("\n")


def demote(body: str, by: int = DEMOTE) -> str:
    """コードフェンスの外側の ATX 見出しだけを下げる。"""
    out, fenced = [], False
    for line in body.split("\n"):
        if re.match(r"^\s*(```|~~~)", line):
            fenced = not fenced
        elif not fenced:
            m = re.match(r"^(#{1,6})(\s+)(.*)$", line)
            if m:
                level = min(len(m.group(1)) + by, 6)
                line = "#" + "#" * (level - 1) + m.group(2) + m.group(3)
        out.append(line)
    return "\n".join(out)


def anchorize(body: str, slugger: Slugger, toc: list[Entry], toc_depth: int) -> str:
    """見出しに採番済みアンカーを埋め、目次項目を集める。

    GitHub の自動アンカーは重複時に -1 を付ける。巻をまたぐと同名見出しが
    衝突するため、明示的な <a id> を置いて安定させる。
    """
    out, fenced = [], False
    for line in body.split("\n"):
        if re.match(r"^\s*(```|~~~)", line):
            fenced = not fenced
            out.append(line)
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line) if not fenced else None
        if not m:
            out.append(line)
            continue
        level, title = len(m.group(1)), m.group(2).strip()
        anchor = slugger.slug(title)
        if level <= toc_depth:
            toc.append(Entry(level, title, anchor))
        out.append(f'<a id="{anchor}"></a>')
        out.append(line)
    return "\n".join(out)


def render_toc(toc: list[Entry]) -> str:
    lines = ["## 目次", ""]
    base = min(e.level for e in toc) if toc else 1
    for e in toc:
        indent = "  " * (e.level - base)
        title = re.sub(r"\*\*(.+?)\*\*", r"\1", e.title)
        lines.append(f"{indent}- [{title}](#{e.anchor})")
    return "\n".join(lines)


def main() -> None:
    slugger = Slugger()
    toc: list[Entry] = []
    chunks: list[str] = []

    for path in FRONT:
        chunks.append(read(path))

    toc_placeholder = "<!--TOC-->"
    chunks.append(toc_placeholder)

    for part in PARTS:
        title = f"{part.numeral}　{part.title}"
        anchor = slugger.slug(title)
        toc.append(Entry(1, title, anchor))
        chunks.append(f'<a id="{anchor}"></a>\n\n# {title}\n\n{part.lead}')
        for path in part.sources:
            body = demote(read(path))
            chunks.append(anchorize(body, slugger, toc, toc_depth=3))

    for path in BACK:
        body = read(path)
        chunks.append(anchorize(body, slugger, toc, toc_depth=1))

    book = "\n\n---\n\n".join(chunks)
    book = book.replace(toc_placeholder, render_toc(toc))

    # 分冊どうしの相対リンクは、製本後は本文内アンカーへ潰す。
    book = re.sub(r"\]\((?:sera/)?(?:vol\d|appendix)[^)]*\.md\)", "](#目次)", book)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(book + "\n", encoding="utf-8")

    chars = len(book)
    print(f"{OUT.relative_to(ROOT)}: {chars:,} 字 / 目次 {len(toc)} 項")


if __name__ == "__main__":
    main()
