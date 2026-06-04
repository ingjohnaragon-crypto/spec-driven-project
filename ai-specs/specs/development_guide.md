# Development Guide — Java / Spring Boot

This guide provides step-by-step instructions for setting up the development environment and running tests for the COMPANY backend system.

## Repository layout

| Path | Purpose |
|------|---------|
| `ai-specs/` | Specs, agent definitions, and slash-command workflows (Jira → plan → implement) |
| `openspec/` | OpenSpec `config.yaml` (rules and context for spec-driven work) |
| `src/` | Spring Boot source code (`main` and `test`) |
| `.github/` | CI workflows |

**Quick start:** from the repo root, run `./gradlew build`.  
Sections below that use `./mvnw` describe the **target** full backend (JPA, Flyway, JaCoCo, etc.) once the Gradle build is extended to match `ai-specs/specs/backend-standards.mdc`; substitute the equivalent `./gradlew` tasks when migrating.

---

## 🛠️ Prerequisites

Ensure you have the following installed:

| Tool | Version       | Check |
|---|---------------|---|
| **Java (JDK)** | 17 or higher  | `java -version` |
| **Gradle** | Via wrapper in repository root | `./gradlew -v` |
| **Docker & Docker Compose** | Latest stable | `docker -version` |
| **Git** | Latest stable | `git --version` |

> **Recommended**: Use [SDKMAN](https://sdkman.io/) to manage Java versions:
> ```bash
> sdk install java 17.0.3-tem
> ```

---

## 🚀 Setup Instructions

### 1. Clone the Repository

```bash
git clone git@github.com:your-org/your-repo.git
cd your-repo
```

---

### 2. Environment Configuration

Spring Boot reads configuration from `src/main/resources/application.yml`.  
**Never commit secrets** — use environment variables or a local `.env` file with a tool like [direnv](https://direnv.net/).

**`src/main/resources/application.yml`** (committed, uses env var placeholders):
```yaml
spring:
  datasource:
    url: ${DATABASE_URL:jdbc:postgresql://localhost:5432/LTIdb}
    username: ${DB_USER:LTIdbUser}
    password: ${DB_PASSWORD:D1ymf8wyQEGthFR1E9xhCq}
    driver-class-name: org.postgresql.Driver
  jpa:
    hibernate:
      ddl-auto: validate        # Flyway manages schema — never use 'update' or 'create'
    show-sql: false
    properties:
      hibernate:
        format_sql: true
        dialect: org.hibernate.dialect.PostgreSQLDialect
  flyway:
    enabled: true
    locations: classpath:db/migration

server:
  port: ${PORT:3000}

logging:
  level:
    com.lti: INFO
    org.hibernate.SQL: DEBUG   # Set to INFO in production
```

**`src/main/resources/application-test.yml`** (used automatically during tests):
```yaml
spring:
  datasource:
    url: jdbc:tc:postgresql:15:///LTIdb_test   # Testcontainers — spins up a real DB
    driver-class-name: org.testcontainers.jdbc.ContainerDatabaseDriver
  flyway:
    enabled: true
  jpa:
    hibernate:
      ddl-auto: validate
```

**Local `.env`** (git-ignored, used with direnv or export manually):
```env
DATABASE_URL=jdbc:postgresql://localhost:5432/LTIdb
DB_USER=LTIdbUser
DB_PASSWORD=D1ymf8wyQEGthFR1E9xhCq
PORT=3000
```

Add `.env` to `.gitignore`:
```
.env
*.env
```

---

### 3. Database Setup (PostgreSQL with Docker)

Start the PostgreSQL database using Docker Compose:

```bash
# From the project root
docker-compose up -d postgres

# Verify the container is running
docker-compose ps
```

**`docker-compose.yml`** (backend-relevant excerpt):
```yaml
services:
  postgres:
    image: postgres:15-alpine
    container_name: lti_postgres
    environment:
      POSTGRES_DB: LTIdb
      POSTGRES_USER: LTIdbUser
      POSTGRES_PASSWORD: D1ymf8wyQEGthFR1E9xhCq
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U LTIdbUser -d LTIdb"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

PostgreSQL will be available at:
- **Host**: `localhost`
- **Port**: `5432`
- **Database**: `LTIdb`
- **Username**: `LTIdbUser`

---

### 4. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies and compile
./mvnw clean install -DskipTests

# Run Flyway migrations (applied automatically on startup, or manually):
./mvnw flyway:migrate

# (Optional) Seed the database with sample data
./mvnw spring-boot:run -Dspring-boot.run.profiles=seed

# Start the development server
./mvnw spring-boot:run
```

The backend API will be available at `http://localhost:3000`  
Swagger UI (API docs) will be available at `http://localhost:3000/swagger-ui.html`

> **Hot reload during development**: Add [Spring Boot DevTools](https://docs.spring.io/spring-boot/docs/current/reference/html/using.html#using.devtools) to `pom.xml` for automatic restart on class changes:
> ```xml
> <dependency>
>     <groupId>org.springframework.boot</groupId>
>     <artifactId>spring-boot-devtools</artifactId>
>     <optional>true</optional>
> </dependency>
> ```

---

### 5. Useful Development Scripts

```bash
# Start the application
./mvnw spring-boot:run

# Start with a specific profile (e.g., local, seed)
./mvnw spring-boot:run -Dspring-boot.run.profiles=local

# Compile without running tests
./mvnw clean install -DskipTests

# Run Flyway migrations manually
./mvnw flyway:migrate

# Check Flyway migration status
./mvnw flyway:info

# Repair Flyway checksum (use only if a migration was accidentally modified)
./mvnw flyway:repair

# Build a production JAR
./mvnw clean package -DskipTests
java -jar target/lti-backend-*.jar
```

---

## 🧪 Testing

### Run All Tests

```bash
cd backend

# Run all unit and integration tests
./mvnw test

# Run tests and generate JaCoCo coverage report
./mvnw test jacoco:report

# Run full verify phase (tests + coverage threshold check — fails if below 90%)
./mvnw verify
```

Coverage report will be generated at:
```
target/site/jacoco/index.html
```

---

### Run Specific Tests

```bash
# Run a single test class
./mvnw test -Dtest=CandidateServiceTest

# Run a single test method
./mvnw test -Dtest=CandidateServiceTest#shouldCreateCandidate_whenEmailIsUnique

# Run all tests in a package
./mvnw test -Dtest="com.lti.unit.*"

# Run only integration tests
./mvnw test -Dtest="com.lti.integration.*"
```

---

### Test Types

#### Unit Tests (`src/test/java/com/lti/unit/`)
- No Spring context — fast and isolated
- Use `@ExtendWith(MockitoExtension.class)` with `@Mock` and `@InjectMocks`
- Mock all external dependencies (repositories, services, mappers)

```bash
./mvnw test -Dtest="**/*Test"
```

#### Integration Tests (`src/test/java/com/lti/integration/`)
- Uses `@SpringBootTest` with Testcontainers (real PostgreSQL in Docker)
- Tests the full request/response cycle end-to-end
- Requires Docker running locally

```bash
./mvnw test -Dtest="**/*IntegrationTest"
```

#### Controller (Slice) Tests
- Uses `@WebMvcTest` — loads only the web layer, no full Spring context
- Mocks the service layer with `@MockBean`

```bash
./mvnw test -Dtest="**/*ControllerTest"
```

---

### Coverage Requirements

JaCoCo is configured to **fail the build** if coverage drops below 90% for:
- Branches
- Methods
- Lines
- Instructions

To check thresholds without running the full build:

```bash
./mvnw jacoco:check
```

Coverage reports are stored in:
```
coverage/YYYYMMDD-backend-coverage/
```

---

## � Python / FastAPI Setup

This repository also supports the Python FastAPI base application template used by KAN-6.

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the application

```bash
uvicorn main:app --reload
```

### Environment variables

Create a local `.env` file based on `.env.example` and add the following values:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/openspec
APP_NAME=open-spec-base-app
APP_VERSION=0.1.0
ENVIRONMENT=development
```

### Run database migrations

```bash
alembic upgrade head
```

### Run tests

```bash
pytest
```

### Lint and type check

```bash
ruff check .
mypy src
```

### Validate Vault sandbox restrictions (os-vault-lint)

`os-vault-lint` scans `contracts/*.py` files using Python's `ast` module and reports
any Vault sandbox violations before tests run. It uses only Python standard library —
no additional packages required.

```bash
# Lint the entire contracts/ directory (default)
python .openspec-cli/lib/vault_lint.py contracts/

# Lint a single file
python .openspec-cli/lib/vault_lint.py contracts/savings_product.py

# Via the CLI wrapper (after install)
os-vault-lint
os-vault-lint contracts/savings_product.py
```

**Exit codes**: `0` = no violations, `1` = violations found or target not found.

**Output format** (one line per violation):
```
contracts/foo.py:12 [FORBIDDEN_IMPORT] import 'os' is not allowed
contracts/foo.py:34 [FORBIDDEN_CALL] call to 'eval' is not allowed in contracts
contracts/foo.py:56 [EXCEPTION_CHAINING] 'raise ... from ...' is not allowed in contracts
```

**Rules enforced**:

| Rule ID | Trigger |
|---|---|
| `FORBIDDEN_IMPORT` | `import` or `from ... import` of a banned stdlib module |
| `UNKNOWN_IMPORT` | Any import not from `contracts_api` or `decimal` |
| `FORBIDDEN_CALL` | Call to `eval`, `exec`, `open`, `print`, `getattr`, `setattr`, `hasattr`, `delattr`, `type`, `globals`, `locals`, `vars`, `dir`, `compile`, `__import__`, `input` |
| `EXCEPTION_CHAINING` | `raise X from Y` syntax |
| `MUTABLE_GLOBAL` | Module-level `list`, `dict`, or `set` literal not in the allowed contract metadata names |

`os-vault-test` automatically runs `os-vault-lint` before executing pytest. To run
lint tests with coverage:

```bash
pytest tests/test_vault_lint.py --cov=vault_lint --cov-fail-under=90
```

---

## �🗄️ Database Migrations (Flyway)

Flyway migrations run **automatically** when the application starts. All scripts live under:

```
src/main/resources/db/migration/
├── V1__create_candidates_table.sql
├── V2__create_education_and_work_experience_tables.sql
├── V3__create_resumes_table.sql
├── V4__create_companies_and_employees_tables.sql
├── V5__create_interview_flow_tables.sql
├── V6__create_positions_table.sql
└── V7__create_applications_and_interviews_tables.sql
```

**Rules:**
- **Never modify** an already-applied migration — always create a new file
- File naming: `V{sequential_number}__{descriptive_snake_case_name}.sql`
- Test migrations locally before committing

---

## 🔍 Verify Everything Is Running

```bash
# Check application health
curl http://localhost:3000/actuator/health

# Expected response:
# {"status":"UP","components":{"db":{"status":"UP"},...}}

# Check Swagger UI is accessible
open http://localhost:3000/swagger-ui.html
```

---

## 🧹 Common Issues

| Problem                                         | Solution                                                                                             |
|-------------------------------------------------|------------------------------------------------------------------------------------------------------|
| `Port 5432 already in use`                      | Stop local PostgreSQL: `sudo systemctl stop postgresql` or `brew services stop postgresql`           |
| `Flyway migration failed`                       | Run `./mvnw flyway:info` to see which migration failed, fix and run `./mvnw flyway:repair` if needed |
| `Unable to acquire JDBC Connection`             | Verify Docker is running: `docker-compose ps`                                                        |
| `Tests fail with no Docker`                     | Integration tests require Docker for Testcontainers — ensure Docker Desktop is running               |
| `Build fails on coverage`                       | Run `./mvnw test jacoco:report` and open `target/site/jacoco/index.html` to find uncovered code      |
| `java: error: release version 17 not supported` | Check Java version: `java -version` — must be JDK 17+                                                |