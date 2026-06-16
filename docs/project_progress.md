# Project Progress Summary

작성일: 2026-06-16

이 문서는 `person-ai-project`가 처음 어떤 상태에서 시작했고, 지금까지 어떤 순서로 무엇을 만들었는지 정리한 진행 기록입니다.

## 한 줄 요약

이 프로젝트는 **D2C 헤어케어 브랜드의 매출, 광고, 재고, 리뷰/VOC 데이터를 분석하고 자연어 질문을 분석 Tool로 연결하는 운영 자동화 AI Agent MVP**입니다.

단순 챗봇이 아니라, 숫자는 SQL/Pandas 분석 함수에서만 계산하고 Agent는 어떤 Tool을 호출할지 결정하는 구조입니다. Mock Agent, OpenAI Tool Calling, FastAPI, Streamlit, SQLite, pytest, Docker, CI, Agent Evaluation까지 갖춘 포트폴리오형 프로젝트로 발전했습니다.

## 현재 상태

| 영역 | 현재 구현 상태 |
| --- | --- |
| 샘플 데이터 | 가상 헤어케어 D2C 브랜드 `LumaRoot` 데이터 생성 |
| 데이터 저장소 | CSV 생성 후 SQLite 적재 |
| 분석 함수 | 매출, 광고, 재고, 리뷰/VOC, 이상 탐지, Slack 보고서 |
| Agent | Rule-based Mock Provider와 OpenAI Responses API Provider |
| Tool Calling | Pydantic schema 기반 Tool Registry |
| API | FastAPI endpoint와 Swagger 문서 |
| Dashboard | Streamlit multipage 운영 대시보드 |
| Evaluation | Agent Tool 선택, 인자, 근거 포함 여부 자동 평가 |
| 테스트 | pytest 28개 통과 |
| CI/CD | GitHub Actions에서 테스트, Agent Evaluation, Docker build |
| 실행 환경 | 로컬 Python과 Docker Compose 지원 |

## 처음 요청한 MVP 범위 대비 결과

| 요청 항목 | 결과 |
| --- | --- |
| Python 데이터 파이프라인 | `scripts/generate_sample_data.py`, `scripts/init_db.py` 구현 |
| SQL 기반 분석 | `app/analysis` 모듈에서 SQLite 쿼리와 Pandas 계산 구현 |
| LLM Agent Tool Calling 구조 | `app/agent/registry.py`, `tool_schemas.py`, `providers` 구현 |
| Streamlit 대시보드 | Home, Sales, Marketing, Inventory, Review/VOC, AI Agent Report 화면 구현 |
| FastAPI 백엔드 | `/health`, `/sales`, `/ads`, `/inventory`, `/reviews`, `/agent` 계열 endpoint 구현 |
| 테스트 코드 | 계산, Router, Provider, API, Dashboard, Evaluation 테스트 구현 |
| README 문서화 | 프로젝트 개요, 실행법, API, Agent 설계, 한계점 문서화 |
| Prompt Test & Learn 로그 | `docs/prompt_test_learn.md` 작성 |
| Mock LLM 모드 | API Key 없이 `mock`/`auto` 모드 실행 가능 |
| 숫자 hallucination 방지 | `formula`와 `evidence`를 Tool 결과로 반환 |

## 작업 타임라인

### 1. 저장소 연결과 기본 구조 정리

- GitHub 저장소: `RohKJ/person-ai-project`
- 로컬 작업 폴더: `C:\Users\Dell5371\AI 프로젝트`
- Python 프로젝트 기본 구조를 만들고 Git remote와 연결했습니다.
- 이후 모든 작업은 커밋 후 `origin/main`으로 푸시하는 방식으로 진행했습니다.

주요 커밋:

- `d450de5 Initial project setup`
- `045d7a0 Initial commit`

### 2. D2C 운영 자동화 AI Agent MVP 구축

처음 요청한 MVP 범위를 기준으로 실행 가능한 프로젝트를 만들었습니다.

구현 내용:

- `products.csv`, `orders.csv`, `ads.csv`, `inventory.csv`, `reviews.csv`, `cs_messages.csv` 샘플 데이터 생성
- SQLite DB 초기화와 CSV 적재
- 매출, 광고, 재고, 리뷰/VOC 분석 함수 구현
- 자연어 질문을 Tool로 연결하는 rule-based Agent Router 구현
- FastAPI endpoint 구현
- Streamlit multipage dashboard 구현
- pytest 기반 핵심 계산 테스트 구현
- README 초안 작성

주요 커밋:

- `52949a6 Build D2C operations AI agent MVP`
- `5f64bf3 Clean up local project workflow`

### 3. Agent 구조 고도화

초기 rule-based Router를 유지하면서, 나중에 OpenAI/LangGraph로 확장하기 쉬운 구조로 나눴습니다.

구현 내용:

- Tool Registry 도입
- Pydantic 기반 Tool argument schema 정리
- Tool 실행과 답변 formatter 분리
- Agent Provider 추상화
- OpenAI Responses API Tool Calling Provider 추가
- `AGENT_MODE=auto|mock|openai` 지원
- OpenAI 모드에서도 모델은 Tool과 인자만 고르고, 숫자 답변은 deterministic formatter가 만들도록 설계

주요 커밋:

- `fdaad43 Refactor agent tool registry`
- `9cc4009 Add OpenAI tool calling agent provider`

### 4. Streamlit 운영 대시보드 개선

처음 돌아가는 MVP에서 포트폴리오 시연이 가능한 화면으로 다듬었습니다.

구현 내용:

- Home KPI 화면 개선
- Sales Dashboard
- Marketing Dashboard
- Inventory Dashboard
- Review/VOC Dashboard
- AI Agent Report 화면
- 계산식과 근거 데이터 표시
- Playwright 기반 화면 확인 후 screenshot 문서 추가

주요 산출물:

- `docs/screenshots/operations-overview.png`
- `docs/screenshots/agent-tool-trace.png`

주요 커밋:

- `a69a007 Polish Streamlit operations dashboard`

### 5. Docker와 CI 추가

로컬에서만 돌아가는 프로젝트를 재현 가능한 실행 환경으로 정리했습니다.

구현 내용:

- `Dockerfile`
- `compose.yaml`
- `.dockerignore`
- GitHub Actions CI
- CI에서 샘플 데이터 생성, DB 초기화, compile, pytest, Docker build 실행
- Docker Compose로 `init`, `api`, `dashboard` 서비스 실행

검증:

- 로컬 Python 테스트 통과
- Docker 이미지 빌드 성공
- Compose 기반 API와 Streamlit health check 성공
- 원격 GitHub Actions 성공

주요 커밋:

- `351091e Add containerized runtime and CI`

### 6. Agent Evaluation 시스템 추가

Agent가 단지 동작하는지뿐 아니라, 올바르게 동작하는지를 측정할 수 있도록 평가 체계를 만들었습니다.

구현 내용:

- `data/evals/agent_eval_cases.jsonl`
- `scripts/evaluate_agent.py`
- `docs/agent_eval_report.md`
- `tests/test_agent_evaluation.py`
- `scripts/dev.ps1 eval`
- CI에 Agent Evaluation 단계 추가

평가 기준:

- `tool_accuracy`: 질문에 맞는 Tool을 골랐는지
- `argument_accuracy`: 날짜, 기간, 숫자 인자를 올바르게 만들었는지
- `grounding_coverage`: 결과에 계산식, 근거 데이터, 핵심 metric이 포함됐는지
- `overall_pass_rate`: 위 조건을 모두 만족한 케이스 비율

최근 평가:

- 8개 케이스 중 8개 통과
- Tool accuracy 100%
- Argument accuracy 100%
- Grounding coverage 100%

주요 커밋:

- `d52e5e1 Add agent evaluation workflow`

### 7. Agent Evaluation을 API와 대시보드에 노출

평가 결과를 개발자만 보는 CLI 결과가 아니라, API와 화면에서 바로 확인할 수 있게 만들었습니다.

구현 내용:

- 평가 로직을 `app/agent/evaluation.py`로 모듈화
- `GET /agent/evaluation` endpoint 추가
- Streamlit `AI Agent Report` 화면에 Evaluation Scorecard 추가
- API 테스트 추가
- README에 평가 API와 화면 설명 반영

검증:

- pytest 28개 통과
- Agent Evaluation 8/8 통과
- Docker Compose config 검증 통과
- 원격 GitHub Actions 성공

주요 커밋:

- `9cec4ce Expose agent evaluation in API and dashboard`

## 현재 실행 명령

샘플 데이터 생성:

```bash
python scripts/generate_sample_data.py
```

DB 초기화:

```bash
python scripts/init_db.py
```

FastAPI 실행:

```bash
uvicorn app.main:app --reload
```

Streamlit 실행:

```bash
streamlit run dashboard/Home.py
```

테스트:

```bash
pytest
```

Agent 평가:

```bash
python scripts/evaluate_agent.py
```

Docker Compose:

```bash
docker compose up --build
```

## 현재 API 목록

| Method | Path | 목적 |
| --- | --- | --- |
| `GET` | `/health` | 서버와 DB 상태 확인 |
| `GET` | `/sales/daily` | 일별 매출 요약 |
| `GET` | `/sales/anomaly` | 매출 이상 탐지 |
| `GET` | `/ads/performance` | 광고 성과 분석 |
| `GET` | `/inventory/risk` | 재고 위험 상품 확인 |
| `GET` | `/reviews/summary` | 리뷰/VOC 요약 |
| `GET` | `/agent/tools` | Agent Tool Registry 확인 |
| `GET` | `/agent/status` | Agent Provider 상태 확인 |
| `GET` | `/agent/evaluation` | Agent 평가 점수 확인 |
| `POST` | `/agent/query` | 자연어 질문 실행 |

## 현재 대시보드 화면

| 화면 | 내용 |
| --- | --- |
| Home | 총매출, 광고비, ROAS, 재고 위험, 부정 리뷰 등 운영 KPI |
| Sales Dashboard | 일별 매출 추이, 상품별 매출, 이상 탐지 |
| Marketing Dashboard | 캠페인별 광고비, ROAS, CTR, CVR |
| Inventory Dashboard | 상품별 재고, 소진 예상일, 위험 상품 |
| Review/VOC Dashboard | 평균 평점, 부정 리뷰, 불만 키워드 |
| AI Agent Report | 자연어 질문, Tool trace, 계산식, 근거 데이터, Evaluation Scorecard |

## 포트폴리오에서 강조할 점

이 프로젝트는 다음 역량을 보여줍니다.

- Python 데이터 파이프라인을 직접 설계하고 실행 가능한 형태로 구성
- SQL과 Pandas로 비즈니스 지표를 재현 가능하게 계산
- LLM이 숫자를 임의 생성하지 못하도록 Tool 결과 기반 답변 구조 설계
- Mock Provider와 OpenAI Provider를 분리해 API Key 없이도 테스트 가능
- FastAPI와 Streamlit이 같은 분석/Agent 모듈을 재사용
- Agent Evaluation 데이터셋으로 Tool 선택, 인자, 근거 포함 여부를 자동 측정
- GitHub Actions와 Docker Compose로 실행과 검증을 자동화

## 남은 개선 후보

다음 단계로 진행하기 좋은 작업입니다.

1. LangGraph 기반 Agent state graph 추가
2. Slack Webhook 실제 전송 기능 추가
3. VOC keyword rule을 embedding clustering 기반으로 개선
4. 광고/주문/재고 외부 API connector mock 추가
5. 사용자 인증과 배포 환경 설정
6. OpenAI Provider에 대한 별도 eval set과 실패 케이스 분석 추가
7. 포트폴리오용 데모 영상 또는 GIF 추가

## 최신 검증 기준

마지막으로 확인한 기준:

- `pytest`: 28 passed
- `python scripts/evaluate_agent.py`: 8/8 passed
- GitHub Actions CI: success
- 주요 브랜치: `main`
