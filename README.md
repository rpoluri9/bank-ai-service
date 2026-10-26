# Bank AI Platform

A banking system combined with an AI assistant service, built as a portfolio
project in the style of a Java developer's project.

- **Banking service** (Java 17, Spring Boot 3.2): accounts, deposits,
  withdrawals, transfers, balance validation (no overdraft), full transaction
  history, and an audit trail for every transaction.
- **AI service** (Python, standard library only): an agent that answers
  questions over bank documents using a RAG pipeline, and calls the banking
  service's REST APIs through tools whenever a question needs live data
  (balance, transactions) instead of guessing.

This is a personal portfolio project by Ramesh Poluri. It makes no claim
about any employer: the bank, the documents, and the data are fictional demo
content created for this project.

## Architecture

```
User / Postman
   │  HTTP
   ▼
AI Service (Python, :8081) ──REST──▶ Banking Service (Java, :8080)
   │  retrieve                          │  publish
   ▼                                    ▼
Bank Documents (TF-IDF index)      Event Publishers
                                   (local by default, Pub/Sub if configured)
```

Diagrams: `docs/architecture.png`, `docs/rag-pipeline.png`,
`docs/transaction-flow.png`.

## What each part does

1. **Banking microservice** — `banking-service/`: Spring Boot REST APIs with
   request validation, centralized exception handling (`@ControllerAdvice`
   returns a clean `{timestamp, status, error, message, path}` body), and
   clean response contracts. State is held in memory, so no database setup is
   needed to run it.
2. **Core banking rules** — `BankingService`: account management and
   transaction processing. Every money movement writes an immutable
   `Transaction` (the audit trail) and publishes a `TransactionEvent`.
   Balances can never go below zero; transfers lock both accounts in a fixed
   order to avoid deadlocks.
3. **REST APIs** — see "API list" below. A Postman collection is included at
   `postman/bank-ai-platform.postman_collection.json`.
4. **Python AI service with RAG** — `ai-service/aiservice/`: answers questions
   over bank documents (fee schedule, account policies, FAQs, loan basics).
5. **Document ingestion pipeline** — `ingestion.py`: parsing, sentence-based
   chunking (max 800 chars), and TF-IDF indexing. TF-IDF plays the role of
   embedding-style indexing with plain term vectors, so the pipeline runs
   fully offline with no AI libraries and no API keys.
6. **Agent orchestration + Vertex AI interface** — `agent.py` (ADK-style loop:
   instructions, tool planning, tool calls, document retrieval, final answer)
   and `providers.py`. The agent loop is identical either way; only the final
   text-composition step swaps between providers (see "Local vs cloud").
7. **Tool calling** — `tools.py`: `get_balance` and `list_transactions` hit
   the banking service's REST APIs over HTTP. The agent never guesses a
   balance or a transaction list.
8. **Pub/Sub event publishing** — both services publish through a publisher
   interface. The default is a local publisher (in-memory + logged). A REST
   publisher for real Google Cloud Pub/Sub exists and is only wired in when
   explicitly configured (see "Local vs cloud").
9. **Postman collection** — `postman/bank-ai-platform.postman_collection.json`.
10. **Docker + CI** — one Dockerfile per service, `docker-compose.yml`, and a
    GitHub Actions workflow (`.github/workflows/ci.yml`) that runs the Maven
    tests and the Python tests.

## Run it

### Banking service (port 8080)

```bash
cd banking-service
mvn spring-boot:run
# or, after building:
mvn package -DskipTests
java -jar target/banking-service-1.0.0.jar
```

In VS Code: open `banking-service/`, run the `BankAiBankingApplication`
class with the Java extension's Run button.

### AI service (port 8081)

```bash
cd ai-service
python -m aiservice.server
```

Python 3.10+ with no third-party packages needed. The AI service calls the
banking service at `http://localhost:8080` by default; override with the
`BANKING_BASE_URL` environment variable.

### Docker

```bash
mvn -o package -DskipTests -f banking-service/pom.xml  # build the jar first
docker compose up --build
```

### Try it

```bash
# Create an account (copy the id from the response)
curl -X POST localhost:8080/api/accounts -H "Content-Type: application/json" \
  -d '{"ownerName":"Ramesh Poluri","accountType":"SAVINGS","openingBalance":1000}'

# Deposit, then check the balance
curl -X POST localhost:8080/api/accounts/<id>/deposit \
  -H "Content-Type: application/json" -d '{"amount":250,"description":"Paycheck"}'

# Ask the AI assistant a document question
curl -X POST localhost:8081/api/ask -H "Content-Type: application/json" \
  -d '{"question":"What is the overdraft fee?"}'

# Ask the AI assistant for a live balance (tool call, never a guess)
curl -X POST localhost:8081/api/ask -H "Content-Type: application/json" \
  -d '{"question":"What is my balance?","account_id":"<id>"}'
```

## API list

Banking service (`http://localhost:8080`):

| Method | Path | What it does |
| --- | --- | --- |
| POST | `/api/accounts` | Create an account |
| GET | `/api/accounts` | List accounts |
| GET | `/api/accounts/{id}` | Get one account |
| POST | `/api/accounts/{id}/deposit` | Deposit money |
| POST | `/api/accounts/{id}/withdraw` | Withdraw money (no overdraft) |
| POST | `/api/accounts/{id}/transfer` | Transfer to another account |
| GET | `/api/accounts/{id}/transactions` | Full transaction history |

AI service (`http://localhost:8081`):

| Method | Path | What it does |
| --- | --- | --- |
| GET | `/api/health` | Health + active provider (`local` or `vertex-ai`) |
| GET | `/api/documents` | Seeded bank documents |
| POST | `/api/ask` | Ask a question (`question`, optional `account_id`) |

## Local vs cloud — read this before claiming anything

Everything in this project runs **locally by default, with no GCP account,
no API keys, and no network calls to Google**:

| Feature | Default (what actually runs) | Cloud option (needs your own setup) |
| --- | --- | --- |
| Answer composition | Local template provider (`providers.LocalModelProvider`) | Vertex AI `generateContent` REST API, only when `VERTEX_PROJECT_ID`, `VERTEX_LOCATION`, `VERTEX_MODEL`, and `VERTEX_ACCESS_TOKEN` are all set |
| Transaction events | Local publisher (in-memory + logged) | Google Cloud Pub/Sub REST API, only when `pubsub.enabled=true` (banking service) or `PUBSUB_ENABLED=1` (AI service) plus `PUBSUB_PROJECT_ID`, `PUBSUB_TOPIC`, and `PUBSUB_ACCESS_TOKEN` |

Nothing in this repo talks to GCP unless you set those variables yourself.
Do not describe this project as "running on GCP/Vertex AI" unless you have
actually configured it that way.

## Tests

```bash
cd banking-service && mvn test        # 13 JUnit 5 + MockMvc tests
cd ai-service && python -m unittest discover -s tests -v   # 12 tests
```

Verified on this machine: banking service **13/13 tests passing**, AI service
**12/12 tests passing**. Live boot verified: created an account, deposited
250, withdrew 100 (balance 1000 → 1250 → 1150), an overdraft was rejected
with a clean 400 error, and the AI service answered a fee-schedule question
from the documents and a balance question via a live tool call (1150).

## Project layout

```
banking-service/   Spring Boot banking microservice (Java 17)
ai-service/        Python AI service: RAG + agent + tools (stdlib only)
docs/              Architecture, RAG pipeline, transaction/event flow diagrams
postman/           Postman collection for all endpoints
.github/           CI workflow (Maven tests + Python tests)
docker-compose.yml Docker setup for both services
```
