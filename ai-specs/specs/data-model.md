# Data Model Documentation — Java / Spring Boot / JPA

This document describes the data model for the company application, including entity descriptions, field definitions, JPA annotations, validation rules, relationships, and an entity-relationship diagram.

All entities live under `src/main/java/com/company/domain/model/`.

---

## Technology Mapping

| Original (Prisma/TypeScript) | Java Spring Boot |
|---|---|
| Prisma `model` | `@Entity` class |
| `@id @default(autoincrement())` | `@Id @GeneratedValue(strategy = IDENTITY)` |
| `@unique` | `@Column(unique = true)` |
| `String?` (optional) | `@Column(nullable = true)` / `Optional<>` |
| `@relation` | `@ManyToOne`, `@OneToMany`, `@ManyToMany` |
| `prisma migrate` | Flyway migration scripts |
| `DateTime` | `LocalDate` / `LocalDateTime` |
| `Float` | `BigDecimal` (preferred for money) |
| `Boolean` | `boolean` (primitive) |
| Enum values | Java `enum` + `@Enumerated(EnumType.STRING)` |

---


## Flyway Migration Scripts

All migration scripts live under `src/main/resources/db/migration/`.



---

## Entity Relationship Diagram

---

## Key Design Decisions

### 1. `Long` over `Int` for IDs
Java uses `Long` (64-bit) for all primary keys to align with `BIGSERIAL` in PostgreSQL and avoid overflow in large tables.

### 2. `BigDecimal` over `Float`
`Float` has rounding errors for monetary values. `BigDecimal` with `precision = 10, scale = 2` maps directly to `NUMERIC(10,2)` in PostgreSQL.

### 3. `LocalDate` vs `LocalDateTime`
- `LocalDate` for dates without time (e.g., `startDate`, `applicationDeadline`)
- `LocalDateTime` for timestamps (e.g., `uploadDate`, `interviewDate`, `createdAt`)

### 4. Java `enum`
The `@Enumerated(EnumType.STRING)` annotation stores the literal name in the DB (`OPEN`, `BORRADOR`, etc.) making it readable without lookups.

### 5. Protected no-arg constructors on entities
JPA requires a no-arg constructor. Using `AccessLevel.PROTECTED` (via Lombok) prevents accidental direct construction — all entity creation goes through static factory methods that enforce invariants.

### 6. Cascade and orphanRemoval
`CascadeType.ALL` + `orphanRemoval = true` on owned collections (e.g., `educations`, `workExperiences`) ensures that removing a child from the collection deletes the row from the DB automatically — no orphan records.

### 7. Audit fields via Spring Data JPA Auditing
`@CreatedDate` and `@LastModifiedDate` are populated automatically by Spring when `@EnableJpaAuditing` is enabled in a `@Configuration` class. No manual `new Date()` calls needed.

### 8. `FetchType.LAZY` everywhere
All `@OneToMany` and `@ManyToOne` relationships use `LAZY` loading by default. Use `JOIN FETCH` in specific repository queries when associations are required to avoid N+1 query problems.