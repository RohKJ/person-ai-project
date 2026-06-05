# person-ai-project

## 1. 프로젝트 개요

`person-ai-project`는 D2C 헤어케어 브랜드의 운영 업무를 자동화하는 AI Agent MVP입니다. 매출, 광고, 재고, 리뷰/VOC 데이터를 로컬 CSV와 SQLite로 구성하고, Python 분석 함수와 Agent Router가 필요한 Tool을 호출해 운영 리포트를 생성합니다.

이 프로젝트는 채용 포트폴리오용으로 설계되었으며, 단순 챗봇이 아니라 데이터 파이프라인, SQL 분석, Tool Calling 구조, FastAPI, Streamlit, 테스트 코드, 프롬프트 Test & Learn 로그를 함께 보여주는 것을 목표로 합니다.

## 2. 문제 정의

D2C 브랜드 운영자는 매일 반복적으로 다음 업무를 수행합니다.

- 전일/금일 매출 확인
- 광고 캠페인 성과와 ROAS 점검
- 재고 소진 위험 상품 확인
- 리뷰와 CS 문의에서 주요 불만사항 요약
- Slack에 공유할 운영 리포트 작성

반복 업무의 핵심은 숫자 계산과 근거 데이터 확인입니다. 따라서 이 MVP는 LLM이 숫자를 임의로 생성하지 않도록 분석 함수가 계산한 결과만 기반으로 답변하도록 설계했습니다.

## 3. 시스템 아키텍처

```text
CSV Generator -> SQLite DB -> Analysis Tools -> Agent Router
                                      |             |
                                      v             v
                                  FastAPI      Streamlit Dashboard
```

주요 설계 원칙:

- CSV 샘플 데이터는 `scripts/generate_sample_data.py`에서 생성합니다.
- SQLite 적재는 `scripts/init_db.py`가 담당합니다.
- SQL/Pandas 기반 분석 함수는 `app/analysis`에 모았습니다.
- Agent는 `app/agent/router.py`에서 rule-based mock mode로 Tool을 선택합니다.
- FastAPI와 Streamlit은 같은 분석 함수를 호출합니다.
- 모든 주요 분석 결과는 `formula`와 `evidence`를 함께 반환합니다.

## 4. 데이터 구조

샘플 데이터는 `data/sample`에 생성됩니다.

| 파일 | 설명 | 주요 컬럼 |
| --- | --- | --- |
| `products.csv` | 상품 마스터 | `product_id`, `product_name`, `brand`, `category`, `price` |
| `orders.csv` | 주문/매출 | `order_id`, `order_date`, `product_id`, `channel`, `quantity`, `sales_amount`, `discount_amount` |
| `ads.csv` | 광고 성과 | `ad_date`, `campaign_id`, `campaign_name`, `product_id`, `spend`, `impressions`, `clicks`, `conversions`, `attributed_sales` |
| `inventory.csv` | 일별 재고 | `inventory_date`, `product_id`, `stock_quantity`, `safety_stock` |
| `reviews.csv` | 상품 리뷰 | `review_id`, `review_date`, `product_id`, `rating`, `review_text` |
| `cs_messages.csv` | 고객 문의/VOC | `message_id`, `message_date`, `product_id`, `category`, `message`, `status` |

## 5. 주요 기능

- 일별 매출 요약: 총매출, 주문수, 판매수량, 전일 대비 증감률
- 광고 성과 분석: 캠페인별 광고비, 클릭, 전환, 기여 매출, ROAS, CTR, CVR
- 매출 이상 탐지: 최근 기간과 이전 동일 기간 비교
- 재고 리스크 확인: 최근 7일 평균 판매량 기준 예상 소진일 계산
- 리뷰/VOC 요약: 평균 평점, 부정 리뷰 수, 불만 키워드 룰 기반 요약
- Slack 리포트 생성: 운영자가 바로 공유할 수 있는 문안 생성
- AI Agent Router: 자연어 질문을 분석 Tool 호출로 라우팅

## 6. Agent Tool 설계

현재 Agent는 OpenAI API Key 없이 동작하는 mock/rule-based 모드입니다.

지원 Tool:

- `get_daily_sales_summary(date)`
- `get_campaign_performance(start_date, end_date)`
- `detect_sales_anomaly(start_date, end_date)`
- `check_inventory_risk(days=7)`
- `summarize_reviews(start_date, end_date)`
- `generate_slack_report(report_type, date, start_date, end_date)`

라우팅 예시:

| 사용자 질문 | 호출 Tool |
| --- | --- |
| 어제 매출 요약해줘 | `get_daily_sales_summary` |
| 이번 주 광고 성과 알려줘 | `get_campaign_performance` |
| 품절 위험 상품 있어? | `check_inventory_risk` |
| 리뷰 불만사항 정리해줘 | `summarize_reviews` |
| 오늘 슬랙 보고서 만들어줘 | `generate_slack_report` |

숫자 생성 원칙:

- Agent 답변의 숫자는 Tool 반환값에서만 사용합니다.
- Tool 반환값에는 `formula`와 `evidence`가 포함됩니다.
- 향후 LangGraph/OpenAI Tool Calling으로 교체해도 분석 함수는 그대로 재사용할 수 있습니다.

## 7. 실행 방법

Python 3.11 기준입니다. Windows PowerShell에서는 아래 간편 스크립트를 사용할 수 있습니다.

전체 초기화와 검증:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1 all
```

FastAPI 실행:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1 api
```

Streamlit 실행:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1 dashboard
```

로컬 서버 종료:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1 stop
```

개별 명령어로 실행하려면 아래 순서를 따르면 됩니다.

의존성 설치:

```bash
pip install -r requirements.txt
```

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

테스트 실행:

```bash
pytest
```

## 8. API 문서

FastAPI 실행 후 Swagger 문서는 아래에서 확인할 수 있습니다.

```text
http://127.0.0.1:8000/docs
```

엔드포인트:

| Method | Path | 설명 |
| --- | --- | --- |
| `GET` | `/health` | 서버와 DB 파일 상태 확인 |
| `GET` | `/sales/daily?date=YYYY-MM-DD` | 일별 매출 요약 |
| `GET` | `/ads/performance?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` | 광고 캠페인 성과 |
| `GET` | `/inventory/risk?days=7` | 재고 리스크 상품 |
| `GET` | `/reviews/summary?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` | 리뷰/VOC 요약 |
| `POST` | `/agent/query` | 자연어 질문 기반 Agent 응답 |

Agent 요청 예시:

```bash
curl -X POST http://127.0.0.1:8000/agent/query ^
  -H "Content-Type: application/json" ^
  -d "{\"query\":\"오늘 슬랙 보고서 만들어줘\"}"
```

## 9. 대시보드 화면 설명

Streamlit 화면:

- `Home`: 총매출, 광고비, ROAS, 재고 위험 상품 수, 부정 리뷰 수
- `Sales Dashboard`: 일별 매출 추이, 상품별 매출
- `Marketing Dashboard`: 캠페인별 광고비, ROAS, CTR, CVR
- `Inventory Dashboard`: 상품별 재고, 예상 소진일, 품절 위험 상품
- `Review/VOC Dashboard`: 평균 평점, 부정 리뷰, 주요 불만 키워드
- `AI Agent Report`: 자연어 질문, Agent 답변, 사용 Tool, 계산식, 근거 데이터

## 10. Test & Learn 계획

프롬프트와 라우팅 실험 로그는 `docs/prompt_test_learn.md`에서 관리합니다.

초기 실험 항목:

- 상대 날짜 표현: 오늘, 어제, 이번 주
- 광고 지표 질문에서 ROAS/CTR/CVR Tool 선택 정확도
- 재고 질문에서 품절/소진/안전재고 표현 처리
- 리뷰/VOC 질문에서 불만 키워드 요약 품질
- Slack 리포트 문안의 가독성과 액션 가능성

## 11. 한계점 및 향후 개선 방향

현재 한계:

- Agent Router는 rule-based mock mode입니다.
- 리뷰 요약은 간단한 키워드 룰 기반입니다.
- 이상 탐지는 기간 비교 기반의 단순 threshold 방식입니다.
- 실시간 외부 API 연동은 포함하지 않았습니다.
- 인증, 권한, 배포 설정은 MVP 범위에서 제외했습니다.

향후 개선:

- LangGraph 기반 Agent State Graph 도입
- OpenAI Tool Calling 연결
- 광고/주문/재고 외부 API Connector 추가
- 리뷰 임베딩 기반 VOC 클러스터링
- Slack Webhook 발송 기능
- Docker Compose와 CI 테스트 파이프라인
- 통합 테스트와 E2E 대시보드 테스트 추가
