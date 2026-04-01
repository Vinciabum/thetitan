# AutoGram (Monologue) 셋업 가이드

## 새 환경에서 시작할 때

### 1. 코드 받기
```
git clone https://github.com/Vinciabum/thetitan.git
cd thetitan
```

### 2. 패키지 설치
```
pip install -r requirements.txt
```

### 3. `.env` 파일 만들기
프로젝트 루트에 `.env` 파일을 직접 생성하고 아래 내용 입력:
```
GEMINI_API_KEY=여기에입력
REPLICATE_API_TOKEN=여기에입력
UNSPLASH_ACCESS_KEY=zv-3Z0CAPQJCX0BDYIIgAuxGwNh2-oq1srnYwzJMwG0
IG_USERNAME=여기에입력
IG_PASSWORD=여기에입력
THREADS_ACCESS_TOKEN=여기에입력
THREADS_USER_ID=908232
```

### 4. 빈티지 사진 다운로드
```
python download_photos.py
```
→ `photos/vintage_portraits/` 폴더에 저장됨 (목표 50장)

### 5. 슬라이드 테스트
```
python test_slides.py
```
→ `output_test/` 폴더에 slide_01~05.jpg 생성됨

### 6. 실제 에이전트 실행
```
python main.py
```

---

## 오늘 작업 내용 요약 (2026-03-28)

### 핵심 문제 → 해결
- **문제**: 카드뉴스 슬라이드 디자인이 레퍼런스(@onestepahead.mag)와 달리 감성이 없고, 텍스트와 배경 이미지가 따로 노는 느낌
- **해결**: Method B (로컬 빈티지 사진 풀) + Method C (레이아웃/디자인 코드 개선) 조합

---

### 변경/신규 파일

#### `core/photo_pool.py` (신규)
- 로컬 빈티지 사진을 관리하는 PhotoPool 클래스
- 사진에 자동 빈티지 처리 파이프라인 적용
  - 흑백 변환 → 대비 강화(1.5x) → 밝기 감소(0.82) → 드림 블러(GaussianBlur 0.8) → 비네팅 → 필름 그레인(노이즈 9)

#### `core/slide_generator.py` (대폭 개선)
- 텍스트 전체 **중앙 정렬** 전환 (기존 좌측 정렬에서 변경)
- **소프트 글로우** 효과 추가 — 텍스트 주변 번짐 레이어로 사진과 자연스럽게 융합
- **2레이어 그라디언트**: 상단 얕은 베일(0~25%) + 하단 메인(38~100%)
- 제목-본문 사이 **얇은 1px 구분선** (레퍼런스 감성)
- **Outro 슬라이드** 전용 레이아웃 추가
  - 질문 형태 문구를 화면 정중앙 배치
  - 위아래 짧은 장식선
  - 하단 CTA 고정: **"하루 한 장, 당신을 위해"**

#### `core/psychological_engine.py` (수정)
- P5(Outro) AI 프롬프트 변경: "소제목 + 질문" 형식 → **질문 단독** 형식으로
- 예시: "오늘 하루,\n당신의 감정은 안녕했나요?"

#### `download_photos.py` (신규)
- Unsplash API 연동, 빈티지 사진 50장 자동 다운로드
- `photos/vintage_portraits/` 폴더에 저장

#### `test_slides.py` (신규)
- API 키, 인터넷 연결 없이 5장 슬라이드 전체를 로컬에서 바로 테스트
- 실행: `python test_slides.py` → `output_test/` 폴더에 결과 저장

---

### 슬라이드 구조 (5장)

| 페이지 | Role | 내용 |
|---|---|---|
| 01 | Hook | 스크롤 멈추게 하는 짧고 강렬한 선언형 문장 (2~3줄) |
| 02 | Context | 오늘의 뉴스/날씨/트렌드 반영 현재 공기 묘사 |
| 03 | Insight | 프랭클/스토아 철학 기반 따뜻한 통찰 |
| 04 | Action | 지금 당장 할 수 있는 작고 구체적인 행동 1가지 |
| 05 | Outro | 공감형 질문 + CTA "하루 한 장, 당신을 위해" |

---

### 남은 과제
- [ ] 로컬에서 `python test_slides.py` 실행 → 한국어 텍스트 렌더링 최종 확인
- [ ] 사진 추가 다운로드 (`python download_photos.py` — 현재 23장/목표 50장)
- [ ] 실제 에이전트 전체 사이클 테스트 (`python main.py`)
- [ ] GitHub Actions 스케줄링 (개발 완성 후)

---

## 주의사항
- `.env` 파일은 git에 올라가지 않음 (보안) — 새 환경마다 직접 생성 필요
- `photos/`, `output/`, `output_test/` 폴더도 git 제외 — `download_photos.py`로 재생성
- 한국어 폰트: Windows 환경에서는 `C:\Windows\Fonts\malgunbd.ttf` 자동 사용
