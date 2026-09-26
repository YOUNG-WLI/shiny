# 한 소절

샤이니 컬러즈 HOPEFUL FE@THERS 31곡의 일본어 원문, 한글 발음, 한국어 번역을 함께 읽는 정적 웹사이트입니다.

## 화면

- 하늘색 배경, 중앙 정렬, 원문·발음·번역 모두 같은 16px 글자와 검은색
- 줄별 버튼이나 강조 없이 원문의 연 구분만 여백으로 표시
- 앨범별 곡 선택, 이전·다음 곡, 주소의 곡 ID로 직접 이동
- 보기 설정에서 세 종류의 가사를 켜고 끄거나 글자 크기를 함께 조절
- 현재 기기의 마지막 곡과 보기 설정 저장

## 실행 및 갱신

Python 3.10 이상에서 프로젝트 루트 기준으로 실행합니다. 빌드는 표준 라이브러리만 사용합니다.

```powershell
python scripts/build_site.py
python -m http.server 8000 --directory dist
```

`http://localhost:8000`에 접속하세요. 빌드 후에는 루트의 `index.html`을 직접 열어도 됩니다.

`data/lyrics/*.json`에서 발음·번역을 수정하고 다시 빌드하면 사이트에 반영됩니다. 생성 파일인 `songs.js`를 직접 수정하지 마세요. 원문을 변경할 때는 `manual_input`, 원문 사본, JSON의 원문과 출처 해시도 일치해야 합니다.

## 온라인 배포

GitHub 저장소는 [YOUNG-WLI/shiny](https://github.com/YOUNG-WLI/shiny)이며, 사이트 주소는 [young-wli.github.io/shiny](https://young-wli.github.io/shiny/)입니다. 자동 배포 설정은 `.github/workflows/pages.yml`에 있습니다. 배포 결과는 저장소의 Actions 탭에서 확인합니다.

1. 이 프로젝트를 배포할 GitHub 저장소를 정합니다.
2. 소스와 `data`, `manual_input`, `scripts`, `.github`, `.gitattributes`를 `main` 브랜치에 올립니다. `dist`와 `songs.js`는 자동 생성하므로 올릴 필요가 없습니다.
3. 저장소의 **Settings → Pages → Build and deployment → Source**에서 **GitHub Actions**를 선택합니다.
4. **Actions → Deploy lyric reader to GitHub Pages → Run workflow**를 실행합니다.

이후 `main`에 변경 사항을 올리면 데이터 검증 → 웹사이트 생성 → 배포가 자동으로 실행됩니다. `.gitattributes`는 Windows와 Linux 사이에서 원문 파일의 줄바꿈 및 해시가 바뀌지 않게 유지합니다.

일반적인 주소 형식은 `https://계정명.github.io/저장소명/`입니다. 배포가 완료되면 컴퓨터를 켜둘 필요 없이 다른 기기에서 접속할 수 있습니다. GitHub Free에서는 공개 저장소가 필요하고, 일반적인 Pages 사이트는 인터넷에 공개됩니다. [GitHub Pages 공식 안내](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)

원본 자료가 아닌 웹사이트 파일만 Pages에 게시하도록 배포 대상을 `dist`로 지정했습니다. 공개 저장소에 업로드한 소스·가사 데이터 자체는 저장소에서도 볼 수 있습니다. 서버 프로그램, 데이터베이스, 외부 글꼴 서비스는 필요하지 않습니다.

## 검증과 데이터

```powershell
python scripts/validate_lyrics.py
python scripts/validate_lyrics.py --write-review
```

- [데이터 설명](data/README.md)
- [앨범별 가사 검토](data/review/README.md)
- [읽기·해석 검토 메모](data/review/notes.md)

개발용 브라우저 검증은 `python scripts/verify_ui.py`로 실행합니다. Chrome과 `.tools/python`에 설치된 `websocket-client`가 필요합니다. 31곡 전체의 원문 대응, 동일한 글자 스타일, 표시 설정, 모바일 화면과 로컬 파일 접근을 확인합니다.
