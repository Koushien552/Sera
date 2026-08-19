#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""断章形式の story/*.md を、小説の地の文へ変換する。

もとの形式：
    一文ごとに空行で区切り、`---` で刻み、`## 　` で大きく空け、**強調**を多用する。

小説の形式：
    複数の文をまとめて段落にし、会話は行を独立させ、場面の変わり目だけ空ける。
"""
import io, os, re, sys

STORY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "story")

BREAK = "◇"          # ◇ 場面の変わり目
ATTR = re.compile(r'^と[、。]')        # 「……」と、○○が言った。
MAXCHARS = 120
MINGAP = 500          # ◇ と ◇ のあいだの、最低限の字数            # 一段落のおおよその上限


def blocks(text):
    for raw in re.split(r'\n\s*\n', text):
        b = raw.strip()
        if b:
            yield b


def convert(text):
    body = re.sub(r'^#\s.*$', '', text, count=1, flags=re.M)   # 見出しを落とす
    body = body.replace('**', '')                              # 強調を落とす
    units, pause = [], 0
    for b in blocks(body):
        if b == '---':
            continue
        if set(b.split()) <= {'##', '　'} or b in ('## 　', '##　'):
            pause += 1          # 一つなら段落の切れ目、二つ以上なら場面の切れ目
            continue
        multiline = '\n' in b
        b = ''.join(l.strip() for l in b.split('\n')).strip()
        if not b:
            continue
        if pause >= 3:
            units.append(('break', ''))
        elif pause >= 1:
            units.append(('pause', ''))
        pause = 0
        # もとから段落になっているもの（複数行、または長い一文）は、そのまま段落とする
        if b.startswith('「'):
            kind = 'speech'
        elif multiline or len(b) >= 45:
            kind = 'para'
        else:
            kind = 'text'
        # 直前が会話で、これが「と、〜」なら地の文として繋げる
        if kind == 'text' and ATTR.match(b) and units and units[-1][0] == 'speech':
            units[-1] = ('speech', units[-1][1] + b)
            continue
        units.append((kind, b))

    out, para = [], []

    def flush():
        if para:
            out.append(''.join(para))
            para.clear()

    for kind, b in units:
        if kind == 'pause':
            if sum(len(x) for x in para) >= 95:
                flush()
        elif kind == 'break':
            flush()
            if out and out[-1] != BREAK:
                out.append(BREAK)
        elif kind == 'speech':
            flush()
            out.append(b)
        elif kind == 'para':
            flush()
            out.append(b)
        else:
            para.append(b)
            if sum(len(x) for x in para) >= MAXCHARS:
                flush()
    flush()
    while out and out[-1] == BREAK:
        out.pop()
    # ◇ は場面の変わり目にだけ置く。近すぎるものは落とす
    cleaned, since = [], 10 ** 9
    for line in out:
        if line == BREAK:
            if since >= MINGAP and cleaned and cleaned[-1] != BREAK:
                cleaned.append(BREAK)
                since = 0
            continue
        cleaned.append(line)
        since += len(line)
    while cleaned and cleaned[-1] == BREAK:
        cleaned.pop()
    return '\n\n'.join(cleaned).strip() + '\n'


def main():
    targets = sys.argv[1:]
    paths = sorted(p for p in os.listdir(STORY) if re.match(r'^\d\d-.*\.md$', p))
    if targets:
        paths = [p for p in paths if any(t in p for t in targets)]
    for name in paths:
        full = os.path.join(STORY, name)
        src = io.open(full, encoding='utf-8').read()
        if '\n---\n' not in src and BREAK in src:
            print('変換済み', name)
            continue
        head = src.split('\n', 1)[0]
        io.open(full, 'w', encoding='utf-8').write(head + '\n\n' + convert(src))
        print('変換', name)


if __name__ == '__main__':
    main()
