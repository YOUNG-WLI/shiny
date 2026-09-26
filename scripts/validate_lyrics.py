"""Validate user lyric alignment and optionally generate readable review files.

    python scripts/validate_lyrics.py
    python scripts/validate_lyrics.py --write-review
"""
import argparse
import hashlib
import json
from pathlib import Path

from save_lyrics import ROOT, source_for


def require(condition, message):
    if not condition:
        raise ValueError(message)


def stanzas_from_text(text):
    stanzas, current = [], []
    for line in text.splitlines():
        if line.strip():
            current.append(line)
        elif current:
            stanzas.append(current)
            current = []
    if current:
        stanzas.append(current)
    return stanzas


def cell(text):
    return (text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('|', '&#124;').replace('\\', '&#92;').replace('`', '&#96;'))


def validate(write_review=False):
    catalog = json.loads((ROOT / 'data/hopeful-feathers.json').read_text(encoding='utf-8'))
    review_dir = ROOT / 'data/review'
    if write_review:
        review_dir.mkdir(exist_ok=True)
    summary = [
        '# 가사 데이터 검토', '',
        '입력: 사용자가 작성한 `manual_input/*.txt`. 원문 파일은 수정하지 않았습니다.', '',
        '발음은 원문과 괄호 속 지정 읽기에 근거한 한글 근사 표기이며 음원 대조는 하지 않았습니다. '
        '영어 발음도 한글로 근사 표기했습니다. 한국어 번역은 비공식 문맥 번역입니다.', '',
        '| 앨범 | 곡 수 | 가사 줄 수 | 검토 문서 |',
        '|---|---:|---:|---|'
    ]
    notes = ['# 곡별 검토 메모', '',
             '아래에는 읽기 가정, 말장난 해석, 버전 확인 사항이 포함되어 있습니다. '
             '괄호의 읽기가 주어진 곳은 그 읽기를 우선했습니다. '
             '모든 곡의 실제 가창 발음 및 파트 배분은 음원 미검증입니다.', '']
    seen_sources, seen_ids, seen_outputs = set(), set(), set()
    song_count = line_count = stanza_count = 0
    for album in catalog['albums']:
        album_lines = 0
        review = [f"# {album['title']}", '',
                  '원문 · 한글 발음 · 한국어 번역. 원문 파일의 연 구분과 반복을 유지했습니다.', '']
        for track in album['tracks']:
            track_id = f"{album['id']}-{track['number']:02}"
            source = source_for(track)
            raw = source.read_bytes()
            original_stanzas = stanzas_from_text(raw.decode('utf-8-sig'))
            relative_path = track.get('lyricsFile')
            require(relative_path, f'{track_id}: missing lyricsFile')
            path = ROOT / 'data' / relative_path
            require(path.resolve().parent == (ROOT / 'data/lyrics').resolve(), f'{track_id}: unexpected path')
            data = json.loads(path.read_text(encoding='utf-8'))
            require(track_id not in seen_ids, f'{track_id}: duplicate ID')
            require(source not in seen_sources, f'{track_id}: duplicate input mapping')
            require(path not in seen_outputs, f'{track_id}: duplicate output mapping')
            seen_ids.add(track_id)
            seen_sources.add(source)
            seen_outputs.add(path)
            require(data['id'] == track_id and data['albumId'] == album['id'] and
                    data['trackNumber'] == track['number'], f'{track_id}: wrong identity')
            require(data['title'] == track['title'] and data['vocal'] == track['vocal'], f'{track_id}: metadata mismatch')
            require(data['source']['inputFile'] == source.relative_to(ROOT).as_posix(), f'{track_id}: wrong input path')
            require(data['source']['sha256'] == hashlib.sha256(raw).hexdigest(), f'{track_id}: changed input')
            require((path.parent / data['source']['originalFile']).read_bytes() == raw, f'{track_id}: changed original snapshot')
            require([[l['original'] for l in s['lines']] for s in data['stanzas']] == original_stanzas,
                    f'{track_id}: original line or stanza mismatch')
            require([s['number'] for s in data['stanzas']] == list(range(1, len(original_stanzas) + 1)),
                    f'{track_id}: stanza numbering mismatch')
            lines = [l for s in data['stanzas'] for l in s['lines']]
            require([l['number'] for l in lines] == list(range(1, len(lines) + 1)), f'{track_id}: line numbering mismatch')
            repeated = {}
            for line in lines:
                for key in ['original', 'pronunciation', 'translation']:
                    require(isinstance(line[key], str) and line[key].strip(), f'{track_id}: empty {key}')
                pair = (line['pronunciation'], line['translation'])
                require(line['original'] not in repeated or repeated[line['original']] == pair,
                        f'{track_id}: inconsistent repeated line {line["number"]}')
                repeated[line['original']] = pair
            song_count += 1
            line_count += len(lines)
            album_lines += len(lines)
            stanza_count += len(data['stanzas'])
            review += [f"## {track['number']:02}. {track['title']}", '',
                       f"가창: {track['vocal']} · {len(lines)}줄 · {len(data['stanzas'])}연", '',
                       f"[JSON](../{relative_path}) · [입력 원문](../../{source.relative_to(ROOT).as_posix()})", '']
            for stanza in data['stanzas']:
                review += [f"### {stanza['number']}연", '', '| 줄 | 일본어 원문 | 한글 발음 | 한국어 번역 |', '|---:|---|---|---|']
                for line in stanza['lines']:
                    review.append(f"| {line['number']} | {cell(line['original'])} | {cell(line['pronunciation'])} | {cell(line['translation'])} |")
                review.append('')
            if data['notes']:
                review += ['검토 메모:', ''] + ['- ' + n for n in data['notes']] + ['']
                notes += [f"## {track_id} · {track['title']}", ''] + ['- ' + n for n in data['notes']] + ['']
        summary.append(f"| {album['artist']} | {len(album['tracks'])} | {album_lines} | [가사 검토]({album['id']}.md) |")
        if write_review:
            (review_dir / (album['id'] + '.md')).write_text('\n'.join(review) + '\n', encoding='utf-8')
        print(f"PASS {album['id']}: {len(album['tracks'])} songs, {album_lines} lines")
    require(seen_sources == set((ROOT / 'manual_input').glob('*.txt')), 'Unmapped or missing input text file')
    require(seen_outputs == set((ROOT / 'data/lyrics').glob('*.json')), 'Unexpected or missing lyric JSON file')
    summary += ['', f'총 **{song_count}곡 · {line_count}줄 · {stanza_count}연**.', '',
                '[곡별 검토 메모](notes.md)', '',
                '검증: 곡 매핑, 원문 SHA-256, 원본 사본의 바이트 일치, 연·줄 순서, '
                '일본어·발음·번역 필드, 반복 구절 일관성을 확인했습니다. 이 검증은 번역 품질이나 실제 가창 일치의 보증은 아닙니다.', '',
                '재검증: `python scripts/validate_lyrics.py`', '',
                '검토 문서 재생성: `python scripts/validate_lyrics.py --write-review`', '']
    if write_review:
        (review_dir / 'README.md').write_text('\n'.join(summary), encoding='utf-8')
        (review_dir / 'notes.md').write_text('\n'.join(notes), encoding='utf-8')
    print(f'PASS total: {song_count} songs, {line_count} lines, {stanza_count} stanzas')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-review', action='store_true')
    validate(parser.parse_args().write_review)
