# Backend Implementation Plan: KAN-1 Spring Boot Base Project

## 1. Overview

This ticket establishes a backend foundation for future features by delivering a runnable Java 17 Spring Boot project with a basic health endpoint, initial layered structure, and CI validation.  
Implementation follows DDD-friendly clean architecture boundaries (Domain, Application, Presentation), while keeping scope minimal and production-ready for incremental growth.

## 2. Architecture Context

- Layers involved:
  - Domain: package baseline and future business core boundary.
  - Application: DTO/service boundary for use cases (minimal for this ticket).
  - Presentation: health-check HTTP endpoint.
- Main components/files:
  - `build.gradle`
  - `src/main/java/com/fabric/open_spec/OpenSpecApplication.java`
  - `src/main/java/com/fabric/open_spec/presentation/controller/HealthController.java`
  - `src/main/java/com/fabric/open_spec/application/dto/HealthResponse.java`
  - `src/test/java/com/fabric/open_spec/OpenSpecApplicationTests.java`
  - `src/test/java/com/fabric/open_spec/presentation/controller/HealthControllerTest.java`
  - `.github/workflows/ci.yml`
  - `ai-specs/specs/api-spec.yml` (if endpoint contract is documented there)
  - `ai-specs/specs/development_guide.md` (update if commands or setup changed)

## 3. Implementation Steps

### Step 0: Create Feature Branch

- Action: Create and switch to dedicated backend branch.
- Branch naming (required): `feature/KAN-1-backend`
- Implementation steps:
  1. Checkout base branch (`main` or `develop`, team convention).
  2. Pull latest changes from remote.
  3. Create branch: `git checkout -b feature/KAN-1-backend`
  4. Verify active branch before edits.
- Notes: This is mandatory before any code changes.

### Step 1: Align Build Baseline for Spring Boot Backend

- File: `build.gradle`
- Action: Ensure backend baseline supports web endpoint and tests.
- Function signature: N/A (build config step)
- Implementation steps:
  1. Confirm Java toolchain remains set to 17.
  2. Add/verify `spring-boot-starter-web` dependency for REST endpoint support.
  3. Keep `spring-boot-starter-test` for test execution.
  4. Ensure Gradle tasks run with `useJUnitPlatform()`.
  5. Keep configuration minimal; avoid adding unused production dependencies.
- Dependencies:
  - `org.springframework.boot:spring-boot-starter-web`
  - `org.springframework.boot:spring-boot-starter-test`
- Implementation notes:
  - Do not introduce Flyway/JPA in this ticket unless explicitly required.
  - Keep foundation lean for incremental evolution.

### Step 2: Add Presentation Health Endpoint

- File: `src/main/java/com/fabric/open_spec/presentation/controller/HealthController.java`
- Action: Create a minimal HTTP health endpoint.
- Function signature:
  - `public ResponseEntity<HealthResponse> getHealth()`
- Implementation steps:
  1. Create controller package if missing.
  2. Define `@RestController` + `@RequestMapping("/api/v1")`.
  3. Add `@GetMapping("/health")`.
  4. Return HTTP 200 with stable payload fields (`status`, `service`, `timestamp` optional).
- Dependencies:
  - Spring Web annotations (`@RestController`, `@GetMapping`, `ResponseEntity`)
- Implementation notes:
  - Endpoint must be deterministic enough for CI smoke checks.
  - Keep business logic out of controller.

### Step 3: Add Response DTO in Application Layer

- File: `src/main/java/com/fabric/open_spec/application/dto/HealthResponse.java`
- Action: Create response DTO for endpoint contract.
- Function signature:
  - Java record or class, e.g. `HealthResponse(String status, String service)`
- Implementation steps:
  1. Create application DTO package if missing.
  2. Define immutable payload type (record preferred).
  3. Use explicit field names that can remain stable over time.
- Dependencies: Java language types only.
- Implementation notes:
  - This enforces early separation between presentation contract and internals.

### Step 4: Keep Application Bootstrap Minimal and Stable

- File: `src/main/java/com/fabric/open_spec/OpenSpecApplication.java`
- Action: Verify bootstrap remains clean and compiles with new endpoint.
- Function signature:
  - `public static void main(String[] args)`
- Implementation steps:
  1. Keep existing Spring Boot entrypoint unchanged unless required.
  2. Verify package structure supports component scanning for new controller.

### Step 5: Add Automated Tests

- Files:
  - `src/test/java/com/fabric/open_spec/OpenSpecApplicationTests.java`
  - `src/test/java/com/fabric/open_spec/presentation/controller/HealthControllerTest.java`
- Action: Cover context boot and health endpoint behavior.
- Function signature:
  - `void contextLoads()`
  - `void shouldReturn200AndHealthPayload()`
- Implementation steps:
  1. Keep/verify context load smoke test.
  2. Add controller test with `@WebMvcTest` and `MockMvc`.
  3. Assert HTTP 200 and expected JSON fields.
  4. Use AAA pattern and descriptive test names.
- Dependencies:
  - JUnit 5
  - Spring Boot Test / MockMvc
- Implementation notes:
  - Target practical baseline coverage for this ticket scope.

### Step 6: Validate CI Pipeline for PRs

- File: `.github/workflows/ci.yml`
- Action: Ensure CI runs build/tests from repository root.
- Function signature: N/A
- Implementation steps:
  1. Verify trigger on `push` and `pull_request` to active base branches.
  2. Ensure Java 17 setup and Gradle cache are configured.
  3. Run `./gradlew build --no-daemon` with working directory `open-spec`.
  4. Confirm workflow is green for branch updates.

### Step 7: Update Technical Documentation

- Action: Update affected docs before closing ticket.
- Implementation steps:
  1. Update `ai-specs/specs/api-spec.yml` if `/api/v1/health` is part of API contract.
  2. Update `ai-specs/specs/development_guide.md` if setup/test commands changed.
  3. Keep docs in English and consistent with current Gradle-based structure.
  4. Mention CI and endpoint verification commands.
- Notes: Mandatory completion step.

## 4. Implementation Order

1. Step 0: Create feature branch.
2. Step 1: Align build baseline.
3. Step 2: Add health controller.
4. Step 3: Add response DTO.
5. Step 4: Verify bootstrap.
6. Step 5: Add tests.
7. Step 6: Validate CI workflow.
8. Step 7: Update documentation.

## 5. Testing Checklist

- `./gradlew test` passes in repository root.
- `./gradlew build` passes in repository root.
- Health endpoint test verifies:
  - HTTP 200
  - expected JSON contract fields
- Spring context loads successfully.
- CI workflow succeeds on branch PR.

## 6. Error Response Format

For this ticket, `/api/v1/health` should always return `200` in normal operation.  
No custom error mapping is required unless future dependencies are introduced.

Reference project standard for other endpoints:

```json
{
  "success": false,
  "code": "ERROR_CODE",
  "message": "Human-readable description",
  "details": [
    "field: validation message"
  ]
}
```

HTTP mapping baseline:
- `400` VALIDATION_ERROR
- `404` NOT_FOUND
- `409` CONFLICT
- `422` BUSINESS_RULE_VIOLATION
- `500` INTERNAL_ERROR

## 7. Partial Update Support

Not applicable for this ticket (no PATCH/PUT domain resource updates).

## 8. Dependencies

- Java 17
- Spring Boot (project version in `build.gradle`)
- `spring-boot-starter-web`
- `spring-boot-starter-test`
- GitHub Actions (CI)

## 9. Notes

- Keep implementation scope constrained to foundation requirements in KAN-1.
- Do not add persistence/migration layers unless requested by a follow-up ticket.
- Use branch naming convention `feature/KAN-1-backend`.
- Keep all code and documentation in English.

## 10. Next Steps After Implementation

- Open PR with title/key including `KAN-1`.
- Request review for architecture baseline compliance.
- After merge, use this base to create next tickets (domain entities, services, repositories).

## 11. Implementation Verification Checklist

- Code Quality:
  - Compiles without warnings/errors.
  - Clean package organization for layered architecture.
- Functionality:
  - `/api/v1/health` is reachable and returns expected payload.
- Testing:
  - Context and controller tests pass.
- Integration:
  - CI pipeline executes successfully.
- Documentation:
  - Relevant spec/docs updated and consistent with delivered behavior.
