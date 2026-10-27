# Bank AI Platform

A banking system combined with an AI assistant service, built as a portfolio
project in the style of a Java developer's project.

- **Frontend** (React + Vite, port 5173): account list and creation, account
  detail with balance and transaction history, deposit / withdraw / transfer
  forms, and an AI assistant panel. Logs in with the banking API's demo user.
- **Banking service** (Java 17, Spring Boot 3.2 + Spring Security, port
  8080): accounts, deposits, withdrawals, transfers, balance validation (no
  overdraft), full transaction history, and an audit trail for every
  transaction. Data is persisted with Spring Data JPA.
- **AI service** (Python, standard library only, port 8081): an agent that
  answers questions over bank documents using a RAG pipeline, and calls the
  banking service's REST APIs through tools whenever a question needs live
  data (balance, transactions) instead of guessing.

This is a personal portfolio project by Ramesh Poluri. It makes no claim
about any employer: the bank, the documents, and the data are fictional demo
content created for this project.

## Architecture

```
React Frontend (:5173) ──HTTP + Basic auth──▶ Banking Service (Java, :8080)
        │                                            │  JPA
        │  HTTP                                      ▼
        ▼                                     MySQL Database
AI Service (Python, :8081) ──REST + Basic auth──▶ (accounts, transactions)
   │  retrieve                          │  publish
   ▼                                    ▼
Bank Documents (TF-IDF index)      Event Publishers
                                   (local by default, Pub/Sub if configured)
```

Diagrams: `docs/architecture.png`, `docs/rag-pipeline.png`,
`docs/transaction-flow.png`.

## What each part does

1. **React frontend** — `frontend/`: Vite + React single-page app. Login
   form (demo user), account list and creation, account detail with balance
   and transaction history, deposit / withdraw / transfer forms, and an AI
   assistant panel (question + optional account id, answer with sources and
   tools used). Talks to the banking API on :8080 and the AI API on :8081.
2. **Banking microservice** — `banking-service/`: Spring Boot REST APIs
   with request validation, centralized exception handling (`@ControllerAdvice`
   returns a clean `{timestamp, status, error, message, path}` body), and
   clean response contracts.
3. **Security** — Spring Security with HTTP Basic auth on all `/api/**`
   endpoints (see "Demo auth" below). Passwords are BCrypt-hashed; the
   service is stateless (no sessions). CORS is open to the React dev server
   (`http://localhost:5173`, `http://localhost:3000`) so the browser app can
   call the API.
4. **Database** — Spring Data JPA entities (`Account`, `Transaction`) and
   repositories. MySQL is the runtime database (see "Database" below). Every
   money movement writes an immutable `Transaction` (the audit trail) with a
   database-assigned sequence number, so history always comes back in the
   order the movements happened.
5. **Core banking rules** — `BankingService`: account management and
   transaction processing. Balances can never go below zero; transfers lock
   both accounts in a fixed order to avoid deadlocks.
6. **REST APIs** — see "API list" below. A Postman collection is included at
   `postman/bank-ai-platform.postman_collection.json` (with Basic auth
   preconfigured for the demo user).
7. **Python AI service with RAG** — `ai-service/aiservice/`: answers questions
   over bank documents (fee schedule, account policies, FAQs, loan basics).
8. **Document ingestion pipeline** — `ingestion.py`: parsing, sentence-based
   chunking (max 800 chars), and TF-IDF indexing. TF-IDF plays the role of
   embedding-style indexing with plain term vectors, so the pipeline runs
   fully offline with no AI libraries and no API keys.
9. **Agent orchestration + Vertex AI interface** — `agent.py` (ADK-style loop:
   instructions, tool planning, tool calls, document retrieval, final answer)
   and `providers.py`. The agent loop is identical either way; only the final
   text-composition step swaps between providers (see "Local vs cloud").
10. **Tool calling** — `tools.py`: `get_balance` and `list_transactions` hit
    the banking service's REST APIs over HTTP, sending Basic auth from the
    `BANKING_AUTH_USER` / `BANKING_AUTH_PASS` environment variables. The
    agent never guesses a balance or a transaction list.
11. **Pub/Sub event publishing** — both services publish through a publisher
    interface. The default is a local publisher (in-memory + logged). A REST
    publisher for real Google Cloud Pub/Sub exists and is only wired in when
    explicitly configured (see "Local vs cloud").
12. **Docker + CI** — one Dockerfile per service (banking, AI, frontend via
    nginx), `docker-compose.yml` (including MySQL), and a GitHub Actions
    workflow (`.github/workflows/ci.yml`) that runs the Maven tests and the
    Python tests.

## Demo auth — read this before running anything

The banking API is protected by HTTP Basic auth with a LOCAL DEMO user.
There is no external OAuth provider and no real credential anywhere in this
repo. Defaults (demo-only, override with env vars):

| Setting | Default | Env override |
| --- | --- | --- |
| Demo username | `demo` | `APP_DEMO_USERNAME` |
| Demo password | `demo123` | `APP_DEMO_PASSWORD` |

Every banking request needs the header `Authorization: Basic <base64(user:pass)>`.
The React app's login form is prefilled with the demo user. The Postman
collection has Basic auth preconfigured (variables `banking_user` /
`banking_password`). The AI service reads the same credentials from
`BANKING_AUTH_USER` / `BANKING_AUTH_PASS` when it calls the banking API.
Do not reuse this demo password anywhere real.

## Database

MySQL is the runtime database. The banking service's default datasource is
`jdbc:mysql://localhost:3306/bankai` (user `bankai`, password `bankai`,
both overridable with `MYSQL_USER` / `MYSQL_PASSWORD` env vars), with
`spring.jpa.hibernate.ddl-auto=update` so the `accounts` and `transactions`
tables are created automatically. The easiest way to get MySQL is the compose
file (it starts a MySQL 8.0 container with a `bankai` database and user):

```bash
docker compose up mysql        # just MySQL, on localhost:3306
docker compose up --build      # the whole stack (see below)
```

**Tests do not use MySQL.** They run on H2 (in-memory) via
`banking-service/src/test/resources/application.properties`, which takes
precedence on the test classpath. So `mvn test` works with no database
installed, while the running service uses MySQL.

## Run it

### Everything with docker compose (recommended)

```bash
mvn -o package -DskipTests -f banking-service/pom.xml  # build the jar first
docker compose up --build
```

Then open http://localhost:5173 (frontend), banking API on :8080, AI on :8081.

### Banking service alone (port 8080)

Needs MySQL on localhost:3306 (or set `SPRING_DATASOURCE_URL`,
`SPRING_DATASOURCE_USERNAME`, `SPRING_DATASOURCE_PASSWORD`):

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
banking service at `http://localhost:8080` by default (override with the
`BANKING_BASE_URL` environment variable) and sends Basic auth from
`BANKING_AUTH_USER` / `BANKING_AUTH_PASS` when both are set.

### React frontend (port 5173)

```bash
cd frontend
npm install
npm run dev
```

Production build: `npm run build` (output in `dist/`), `npm run preview` to
serve it. To point at other API URLs, set `VITE_BANKING_URL` / `VITE_AI_URL`
before starting (see `frontend/README.md`).

### Try it

```bash
# Create an account (copy the id from the response)
curl -u demo:demo123 -X POST localhost:8080/api/accounts -H "Content-Type: application/json" \
  -d '{"ownerName":"Ramesh Poluri","accountType":"SAVINGS","openingBalance":1000}'

# Deposit, then check the balance
curl -u demo:demo123 -X POST localhost:8080/api/accounts/<id>/deposit \
  -H "Content-Type: application/json" -d '{"amount":250,"description":"Paycheck"}'

# Ask the AI assistant a document question
curl -X POST localhost:8081/api/ask -H "Content-Type: application/json" \
  -d '{"question":"What is the overdraft fee?"}'

# Ask the AI assistant for a live balance (tool call, never a guess)
curl -X POST localhost:8081/api/ask -H "Content-Type: application/json" \
  -d '{"question":"What is my balance?","account_id":"<id>"}'
```

## API list

Banking service (`http://localhost:8080`, all endpoints need HTTP Basic auth):

| Method | Path | What it does |
| --- | --- | --- |
| POST | `/api/accounts` | Create an account |
| GET | `/api/accounts` | List accounts |
| GET | `/api/accounts/{id}` | Get one account |
| POST | `/api/accounts/{id}/deposit` | Deposit money |
| POST | `/api/accounts/{id}/withdraw` | Withdraw money (no overdraft) |
| POST | `/api/accounts/{id}/transfer` | Transfer to another account |
| GET | `/api/accounts/{id}/transactions` | Full transaction history |

AI service (`http://localhost:8081`, no auth of its own):

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
cd banking-service && mvn test        # 20 JUnit 5 + MockMvc tests (H2, see above)
cd ai-service && python -m unittest discover -s tests -v   # 14 tests
```

Banking tests cover the full flow (create / deposit / withdraw / transfer /
history / validation / overdraft), the JPA repositories (persistence and
history ordering), and security (401 without auth, 401 with a wrong password,
200 with the demo user). AI tests cover ingestion, retrieval, the agent,
tool calls against a stub banking server, the auth header, and publishers.

## Project layout

```
frontend/          React + Vite frontend (port 5173)
banking-service/   Spring Boot + Spring Security banking microservice (Java 17, port 8080)
ai-service/        Python AI service: RAG + agent + tools (stdlib only, port 8081)
docs/              Architecture, RAG pipeline, transaction/event flow diagrams
postman/           Postman collection for all endpoints (Basic auth preconfigured)
.github/           CI workflow (Maven tests + Python tests)
docker-compose.yml Docker setup for all services, including MySQL
```
