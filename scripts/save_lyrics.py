"""Build line-aligned lyric data from user-supplied text and reviewed annotations.

Usage: python scripts/save_lyrics.py TRACK_ID BASE64_JSON
JSON: {"pairs": [["Hangul pronunciation", "Korean translation"], ...], "notes": []}
Pairs follow first occurrence order of distinct, nonblank original lines.
"""
import base64
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source_for(track):
    title = track['title'].replace(' -9 colors-', '').replace(' -10 colors-', '')
    return ROOT / 'manual_input' / (title + '.txt')


def build(track_id, payload):
    catalog_path = ROOT / 'data/hopeful-feathers.json'
    catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
    album, track = next((a, t) for a in catalog['albums'] for t in a['tracks']
                        if f"{a['id']}-{t['number']:02}" == track_id)
    source = source_for(track)
    raw = source.read_bytes()
    original = raw.decode('utf-8-sig')
    unique = list(dict.fromkeys(line for line in original.splitlines() if line.strip()))
    pairs = payload['pairs']
    if len(unique) != len(pairs):
        raise ValueError(f'{track_id}: expected {len(unique)} unique lines, got {len(pairs)}')
    if any(len(p) != 2 or not all(isinstance(s, str) and s.strip() for s in p) for p in pairs):
        raise ValueError('Every line requires pronunciation and translation')
    annotations = dict(zip(unique, pairs))
    stanzas, current, number = [], [], 0
    for line in original.splitlines():
        if not line.strip():
            if current:
                stanzas.append({'number': len(stanzas) + 1, 'lines': current})
                current = []
            continue
        number += 1
        reading, translation = annotations[line]
        current.append({'number': number, 'original': line, 'pronunciation': reading, 'translation': translation})
    if current:
        stanzas.append({'number': len(stanzas) + 1, 'lines': current})
    notes = payload.get('notes', [])
    if ' colors-' in track['title']:
        notes = notes + ['입력 파일명에는 colors 버전 표기가 없어 앨범 목록의 해당 팀 곡에 연결했습니다. 제공 원문을 사용했으며 해당 버전의 가창·파트 배분은 음원과 대조하지 않았습니다.']
    data = {
        'schemaVersion': 1, 'id': track_id, 'albumId': album['id'],
        'trackNumber': track['number'], 'title': track['title'], 'vocal': track['vocal'],
        'source': {'type': 'user-provided', 'receivedAt': '2026-09-27',
                   'inputFile': source.relative_to(ROOT).as_posix(),
                   'sha256': hashlib.sha256(raw).hexdigest(),
                   'originalFile': track_id + '.original.txt',
                   'normalization': '원본 파일을 바이트 그대로 별도 보관. JSON은 줄바꿈으로 분리하고 빈 줄을 연 구분으로 처리하며 각 가사 줄의 공백과 문장부호를 유지.'},
        'pronunciation': {'language': 'ko', 'method': '원문의 문맥에 따른 한글 근사 발음. 장음을 모음으로 표시하고 영어도 한글로 표기. 실제 가창 미검증.', 'audioVerified': False},
        'translation': {'language': 'ko', 'method': '원문 줄별 문맥 번역', 'official': False},
        'notes': notes, 'stanzas': stanzas
    }
    output = ROOT / 'data/lyrics'
    output.mkdir(exist_ok=True)
    (output / (track_id + '.original.txt')).write_bytes(raw)
    (output / (track_id + '.json')).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    track['lyricsFile'] = f'lyrics/{track_id}.json'
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{track_id}: saved {number} lines / {len(unique)} unique / {len(stanzas)} stanzas')


if __name__ == '__main__':
    build(sys.argv[1], json.loads(base64.b64decode(sys.argv[2]).decode('utf-8')))
