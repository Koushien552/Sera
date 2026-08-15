#!/usr/bin/env python3
"""セラ世界設定の整合検査。

節参照・不変ルールの採番・付録 B の索引・禁止語を機械的に点検する。
標準ライブラリのみで動く。

    python3 tools/check_lore.py

エラーが一件でもあれば終了コード 1 を返す。
製本（tools/build_book.py）はこの検査を通ってからでないと走らない。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "lore" / "sera"
STORY = ROOT / "story"
RULES_SRC = ROOT / "lore" / "README.md"

# 非キャノン。参照の点検対象にしない。
SKIP = {"consistency-notes"}

# どこにも現れてはならない語。改称の取りこぼしを拾う。
FORBIDDEN = {
    "くノ一": "忍 へ改称済み",
}

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


# ---------------------------------------------------------------- 出典の収集

def volume_key(name: str) -> str:
    m = re.match(r"vol(\d)", name)
    if m:
        return f"vol{m.group(1)}"
    if "appendix-a" in name:
        return "付録A"
    if "appendix-b" in name:
        return "付録B"
    return name


def load_sources() -> dict[str, tuple[Path, str, set[str]]]:
    """巻・付録ごとに、本文と見出し番号の集合を集める。"""
    out: dict[str, tuple[Path, str, set[str]]] = {}
    for path in sorted(SRC.glob("*.md")):
        if path.stem in SKIP or "advisory" in str(path):
            continue
        text = path.read_text(encoding="utf-8")
        heads = {
            m.group(1)
            for m in re.finditer(r"^#{1,6}\s+§?(\d+(?:\.\d+)*)", text, re.M)
        }
        out[volume_key(path.name)] = (path, text, heads)
    if not out:
        err("lore/sera/ に出典が見つからない")
    return out


VOL_LABEL = {**{f"vol{i}": f"第 {i} 巻" for i in range(1, 9)},
             "付録A": "付録 A", "付録B": "付録 B"}


def owns(heads: set[str], num: str) -> bool:
    """§2.10 は §2.10.7 しか無くても解決したものとみなす。"""
    return any(h == num or h.startswith(num + ".") for h in heads)


# ------------------------------------------------------------ 一：節参照の検査

def check_references(sources: dict[str, tuple[Path, str, set[str]]]) -> None:
    owners_cache: dict[str, list[str]] = {}

    def owners(num: str) -> list[str]:
        if num not in owners_cache:
            owners_cache[num] = [k for k, (_, _, h) in sources.items() if owns(h, num)]
        return owners_cache[num]

    targets: list[tuple[str, Path, str, str | None]] = []
    for key, (path, text, _) in sources.items():
        targets.append((key, path, text, key))
    for path in sorted(STORY.rglob("*.md")):
        targets.append((path.stem, path, path.read_text(encoding="utf-8"), None))

    vol_of = {str(i): f"vol{i}" for i in range(1, 9)}

    for label, path, text, home in targets:
        for m in re.finditer(r"§(\d+(?:\.\d+)*)", text):
            num = m.group(1)
            before = text[max(0, m.start() - 60):m.start()]
            after = text[m.end():m.end() + 12]

            candidates: list[str] = []
            if home:
                candidates.append(home)

            am = re.match(r"（第\s*(\d)\s*巻", after)
            if am:
                candidates = [vol_of[am.group(1)]]
            else:
                bm = list(re.finditer(r"第\s*(\d)\s*巻|付録\s*([AB])", before))
                if bm:
                    last = bm[-1]
                    tail = before[last.end():]
                    if "。" not in tail and "\n\n" not in tail:
                        inherited = (vol_of[last.group(1)] if last.group(1)
                                     else ("付録A" if last.group(2) == "A" else "付録B"))
                        candidates.append(inherited)

            if any(c in sources and owns(sources[c][2], num) for c in candidates):
                continue

            holders = owners(num)
            line = text[:m.start()].count("\n") + 1
            where = f"{path.relative_to(ROOT)}:{line}"
            if not holders:
                err(f"{where}  §{num} — どの巻にも存在しない節を参照している")
            elif len(holders) == 1:
                err(f"{where}  §{num} — 巻名がない。実体は {VOL_LABEL[holders[0]]} にある")
            else:
                warn(f"{where}  §{num} — 巻名がなく、複数の巻に同番号がある "
                     f"（{'／'.join(VOL_LABEL[h] for h in holders)}）")


# -------------------------------------------------------- 二：不変ルールの検査

def check_rules() -> int:
    text = RULES_SRC.read_text(encoding="utf-8")
    m = re.search(r"^## 全体を貫く不変ルール\s*$(.*?)^## ", text, re.S | re.M)
    if not m:
        err("lore/README.md に「全体を貫く不変ルール」節が見つからない")
        return 0

    rules = [l for l in m.group(1).split("\n") if re.match(r"^\d+\. ", l)]
    if not rules:
        err("不変ルールを 1 件も抽出できなかった")
        return 0

    nums = [int(r.split(".", 1)[0]) for r in rules]
    for got, want in zip(nums, range(1, len(nums) + 1)):
        if got != want:
            err(f"不変ルールの採番が飛んでいる（{want} のところに {got}）")
            break

    seen: dict[str, int] = {}
    for i, rule in enumerate(rules, start=1):
        head = re.sub(r"^\d+\.\s*", "", rule).split(" — ")[0].strip()
        if head in seen:
            err(f"不変ルール {seen[head]} と {i} が同じ内容である：{head[:50]}")
        else:
            seen[head] = i
    return len(rules)


# ------------------------------------------------------ 三：付録 B の索引の検査

def check_encyclopedia(sources: dict[str, tuple[Path, str, set[str]]]) -> None:
    entry = sources.get("付録B")
    if not entry:
        return
    path, text, _ = entry
    real = {m.group(2): m.group(1) for m in re.finditer(r"### ([12]\.\d+) (\S+)", text)}
    for m in re.finditer(r"([^\s|｜／・（）*]+)（§([12]\.\d+)）", text):
        name, num = m.group(1), m.group(2)
        if name in real and real[name] != num:
            line = text[:m.start()].count("\n") + 1
            err(f"{path.relative_to(ROOT)}:{line}  {name} の参照が §{num}。"
                f"実際は §{real[name]}")


# ---------------------------------------------------------- 四：禁止語の検査

def check_forbidden() -> None:
    files = [p for p in ROOT.rglob("*.md")
             if "archive" not in str(p) and "book/セラ大全" not in str(p)]
    for path in files:
        text = path.read_text(encoding="utf-8")
        for word, reason in FORBIDDEN.items():
            if word in text:
                line = text[:text.index(word)].count("\n") + 1
                err(f"{path.relative_to(ROOT)}:{line}  「{word}」が残っている（{reason}）")


# ------------------------------------------------------------------------

def main() -> None:
    sources = load_sources()
    check_references(sources)
    n_rules = check_rules()
    check_encyclopedia(sources)
    check_forbidden()

    for w in warnings:
        print(f"警告  {w}")
    for e in errors:
        print(f"エラー {e}", file=sys.stderr)

    print(f"\n検査：出典 {len(sources)} 件 / 不変ルール {n_rules} 項 "
          f"/ 警告 {len(warnings)} 件 / エラー {len(errors)} 件")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
