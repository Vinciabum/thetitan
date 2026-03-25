# Monologue Dashboard Design Spec

**Date:** 2026-03-25
**Version:** 1.0.0

---

## 개요

Monologue 서비스를 관리하는 로컬 웹 대시보드. Streamlit 기반으로 다크 미니멀 UI를 제공하며, 콘텐츠 자동 포스팅 타이머, 에이전트 모니터링, 플랫폼 설정을 통합 관리한다.

**실행:** `streamlit run dashboard/app.py`
**배포:** git을 통한 개인 로컬 사용

---

## 기술 스택

- **UI:** Streamlit (멀티페이지)
- **데이터 수집:** Playwright (네이버/소셜 트렌드 크롤링)
- **상태 저장:** `dashboard_state.json` (로컬 파일)
- **플랫폼:** Instagram (기존) + Threads (신규)

---

## 파일 구조

```
autogram-main/
├── dashboard/
│   ├── app.py                 # 메인 진입점
│   ├── pages/
│   │   ├── 01_preview.py      # 콘텐츠 미리보기 + 자동 포스팅 타이머
│   │   ├── 02_monitor.py      # 에이전트 상태 + 로그
│   │   └── 03_settings.py     # 플랫폼 설정
│   ├── components/
│   │   ├── slide_card.py      # 슬라이드 카드 컴포넌트
│   │   └── status_badge.py    # 에이전트 상태 뱃지
│   └── state.py               # dashboard_state.json 읽기/쓰기
├── core/
│   └── threads_publisher.py   # Threads 포스팅 (신규)
└── dashboard_state.json       # 포스팅 히스토리, 설정값, 생성 콘텐츠
```

---

## 페이지별 기능

### Page 1: 콘텐츠 미리보기 (`01_preview.py`)
- 생성된 5슬라이드 카드 가로 배열 (이미지 + 텍스트)
- Instagram / Threads 동시 포스팅 토글
- 자동 포스팅 타이머 (분 단위 직접 입력) + MM:SS 카운트다운
- "지금 바로 포스팅" / "건너뛰기" 수동 버튼
- 포스팅 성공/실패 알림

### Page 2: 에이전트 모니터링 (`02_monitor.py`)
- 현재 상태 뱃지: IDLE / COLLECTING / ANALYZING / GENERATING / POSTING / ERROR
- 오늘 포스팅 횟수, 성공률 메트릭
- 최근 실행 로그 (스크롤 가능, 자동 갱신)
- 에이전트 시작 / 중지 버튼

### Page 3: 설정 (`03_settings.py`)
- Instagram 계정 정보 (username, password)
- Threads 계정 정보 (신규)
- 블로그 섹션 (비활성 - "Coming Soon")
- 자동 실행 주기 (하루 몇 번)
- Gemini API 키 관리

---

## 데이터 흐름

```
main.py (에이전트)
  └─ 콘텐츠 생성 완료
      └─ dashboard_state.json 저장
          └─ dashboard/app.py 폴링 (5초 간격)
              └─ 미리보기 표시
                  └─ 타이머 카운트다운
                      └─ 자동 포스팅 (Instagram + Threads)
```

---

## UI 디자인 시스템

### 컬러 팔레트
| 용도 | 색상 |
|---|---|
| 배경 | `#0F0F0F` |
| 카드 배경 | `#1A1A1A` |
| 보더 | `#2C2C2C` |
| 메인 텍스트 | `#F5F0E8` |
| 서브 텍스트 | `#8B7355` |
| 액센트 (골드) | `#C9A96E` |
| 성공 | `#4CAF50` |
| 에러 | `#E57373` |

### 컴포넌트
- 슬라이드 카드: 라운드 코너 + 골드 보더
- 상태 뱃지: 컬러 도트 + 상태 텍스트
- 타이머: 대형 MM:SS 카운트다운 숫자
- 버튼: 골드 액센트 아웃라인 스타일
- 전체 다크 테마: `st.markdown()` + `<style>` 커스텀 CSS

---

## dashboard_state.json 스키마

```json
{
  "agent_state": "idle",
  "last_run": "2026-03-25T09:00:00",
  "pending_content": {
    "slides": [...],
    "instagram_caption": "...",
    "hashtags": [...],
    "image_paths": [...],
    "created_at": "2026-03-25T09:00:00"
  },
  "post_history": [...],
  "settings": {
    "auto_post_delay_minutes": 30,
    "post_frequency": 3,
    "platforms": {
      "instagram": {"enabled": true},
      "threads": {"enabled": false},
      "blog": {"enabled": false}
    }
  }
}
```

---

## Threads 포스팅 (`core/threads_publisher.py`)

- `ThreadsPublisher` 클래스
- `publish(caption, image_paths)` async 메서드
- Threads API (Meta) 사용
- 실패 시 로그만 남기고 Instagram 포스팅은 영향 없음

---

## Phase 2 확장 (블로그 - 이번 범위 외)

- `core/blog_converter.py`: 5슬라이드 → 장문 블로그 포스팅 변환
- 설정 페이지에 "Coming Soon" 섹션으로 공간 확보
