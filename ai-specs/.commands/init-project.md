# Command: Init Project (Multi-Stack Orchestrator)

## Goal
Initialize a new project environment by creating the mandatory directory structure and selecting the appropriate AI "Drivers" based on the chosen language and framework. This ensures that all future developments follow the Open-Spec-Driven pattern.

## Input Parameters
- **PROJECT_NAME**: Name of the project/module.
- **LANG**: Target language (java, python, php, go, angular, react).
- **FRAMEWORK**: (Optional) Specific framework (spring-boot, fastapi, laravel, nextjs).

## Execution Steps

### 1. Core Specification Setup
Create the agnostic specification layer if it doesn't exist:
- `mkdir -p ai-specs/specs/`
- `mkdir -p ai-specs/changes/`
- `touch ai-specs/specs/api-spec.yml`
- `touch ai-specs/specs/data-model.md`

### 2. Implementation Layer Setup (Source Code)
Create the source directories based on the **LANG** parameter:
- **If Java**: `mkdir -p src/main/java/com/fabric/open_spec/` (plus application, domain, infrastructure folders).
- **If Python**: `mkdir -p src/app/{api,models,schemas,services}`[cite: 1].
- **If PHP**: `mkdir -p app/{Http/Controllers,Models,Services}`[cite: 1].
- **If Go**: `mkdir -p internal/{api,domain,repository}`[cite: 1].
- **If Angular**: `mkdir -p src/app/core/{models,services}`[cite: 1].
- **If React**: `mkdir -p src/{components,hooks,services,types}`[cite: 1].

### 3. AI Driver Activation
Link the specific driver rules from `ai-specs/.agents/drivers/` to the project's active context[cite: 1]:
- Load `generic-translator.md` as the primary translation logic[cite: 1].
- Load the specific agent (e.g., `python-developer.md` or `angular-developer.md`) for code generation[cite: 1].

### 4. Configuration Update
Update `openspec/config.yaml` with the project metadata[cite: 1]:
```yaml
project_name: "{{PROJECT_NAME}}"
stack:
  language: "{{LANG}}"
  framework: "{{FRAMEWORK}}"
paths:
  specs: "ai-specs/specs/"
  drivers: "ai-specs/.agents/drivers/{{LANG}}/"