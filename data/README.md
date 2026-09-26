# 가사 데이터

사용자가 제공한 `manual_input`의 31개 텍스트 파일을 바탕으로 원문, 한글 발음, 한국어 번역을 저장했습니다. 수록 순서는 `hopeful-feathers.json`에 있습니다.

## 확인하기

- [전체 현황과 앨범별 검토 문서](review/README.md)
- [읽기 가정·말장난 해석·버전 검토 메모](review/notes.md)

## 파일 구조

- `hopeful-feathers.json`: 공식 앨범·트랙 정보와 곡별 `lyricsFile` 경로. 경로는 `data` 폴더 기준입니다.
- `lyrics/{앨범 ID}-{트랙 번호}.json`: 줄별 `original`, `pronunciation`, `translation` 필드. `stanzas` 배열로 연 구분과 반복 위치를 유지합니다.
- `lyrics/*.original.txt`: 수동 입력 파일의 바이트 단위 사본.
- `review/*.md`: JSON에서 생성한 검토용 표. 수정이 필요하면 곡별 JSON을 고친 뒤 검토 문서를 재생성합니다.

모든 입력 파일은 UTF-8로 읽었습니다. 입력 원문은 수정하지 않았으며 JSON에서도 각 줄의 문장부호와 공백을 유지합니다. 빈 줄은 연 구분으로 저장하고 원문 파일의 줄바꿈 방식은 사본에 그대로 보관합니다. 입력 경로와 SHA-256을 각 곡에 기록했습니다.

한글 발음은 텍스트 기반 근사 표기이고 실제 음원의 가창을 확인하지 않았습니다. 한자 뒤 괄호가 지정 읽기일 때는 이를 발음에 반영하고, 추임새일 때는 별도 발음으로 유지합니다. 한국어 번역은 비공식 문맥 번역입니다. 모호한 읽기나 해석은 각 JSON의 `notes`에 있습니다.

`プラニスフィア ～planisphere～`, `リフレクトサイン`, `SOLAR WAY`는 입력 파일명에 colors 버전이 생략되어 있어 해당 앨범의 팀 곡에 연결했습니다. 해당 버전의 가창·파트 배분은 대조하지 않았습니다.

## 검증

프로젝트 루트에서 실행하세요. Python 표준 라이브러리만 사용합니다.

```powershell
python scripts/validate_lyrics.py
python scripts/validate_lyrics.py --write-review
```

첫 명령은 곡 매핑, 입력 파일 해시, 원문 보존, 연·줄 정렬, 필수 필드와 반복 일관성을 검사합니다. 두 번째 명령은 검증 후 검토용 Markdown을 재생성합니다.

31곡 모두 사이트에 연결되어 있습니다. JSON 수정 후 프로젝트 루트에서 `python scripts/build_site.py`를 실행하면 브라우저용 `songs.js`와 배포용 `dist` 폴더를 갱신합니다.
