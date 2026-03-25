# Role

You are an expert software architect with extensive experience in Java/Spring Boot projects applying Domain-Driven Design (DDD).

# Ticket ID

$ARGUMENTS

# Goal

Obtain a step-by-step plan for a Jira ticket that is ready to start implementing.

# Process and rules

1. Adopt the role of `ai-specs/.agents/backend-developer.md`
1. Analyze the Jira ticket mentioned in #ticket using the MCP. If the mention is a local file, then avoid using MCP
2. Propose a step-by-step plan for the backend part, taking into account everything mentioned in the ticket and applying the project’s best practices and rules you can find in  `/ai-specs/specs`. 
3. Apply the best practices of your role to ensure the developer can be fully autonomous and implement the ticket end-to-end using only your plan. 
4. Do not write code yet; provide only the plan in the output format defined below.
5. If you are asked to start implementing at some point, make sure the first thing you do is to move to a branch named after the ticket id (if you are not yet there) and follow the process described in `ai-specs/.commands/develop-backend.md`

# Output format

Markdown document at the path `ai-specs/changes/[jira_id]_backend.md` containing the complete implementation details.
Follow this template:

## Backend Implementation Plan Ticket Template Structure

### 1. **Header**
- Title: `# Backend Implementation Plan: [TICKET-ID] [Feature Name]`

### 2. **Overview**
- Brief description of the feature and architecture principles (DDD, clean architecture)

### 3. **Architecture Context**
- Layers involved (Domain, Application, Presentation)
- Components/files referenced

### 4. **Implementation Steps**
Detailed steps, typically:

#### **Step 0: Create Feature Branch**
- **Action**: Create and switch to a new feature branch following the development workflow. Check if it exists and if not, create it
- **Branch Naming**: Follow the project's branch naming convention (`feature/[ticket-id]-backend`, make it required to use this naming, don't allow to keep on the general task [ticket-id] if it exists to separate concerns)
- **Implementation Steps**:
  1. Ensure you're on the latest `main` or `develop` branch (or appropriate base branch)
  2. Pull latest changes: `git pull origin [base-branch]`
  3. Create new branch: `git checkout -b [branch-name]`
  4. Verify branch creation: `git branch`
- **Notes**: This must be the FIRST step before any code changes. Refer to `ai-specs/specs/backend-standards.mdc` section "Development Workflow" for specific branch naming conventions and workflow rules.

#### **Step N: [Action Name]**
- **File**: Target file path
- **Action**: What to implement
- **Function Signature**: Code signature
- **Implementation Steps**: Numbered list
- **Dependencies**: Required imports
- **Implementation Notes**: Technical details

Common steps:
- **Step 1**: Flyway migration (if schema changes)
- **Step 2**: Domain entity / repository updates
- **Step 3**: Application service + DTOs + mappers
- **Step 4**: REST controller + validation
- **Step 5**: Unit and slice tests (happy path, validation errors, 404, conflict, 500, edge cases)

Example of a good structure:
**Implementation Steps**:

1. **Validate position exists**:
   - Load via `PositionRepository.findById(positionId)` (or domain service)
   - If empty, throw a domain exception mapped to HTTP 404 in `GlobalExceptionHandler`
   - Use the loaded entity for the rest of the use case

#### **Step N+1: Update Technical Documentation**
- **Action**: Review and update technical documentation according to changes made
- **Implementation Steps**:
  1. **Review Changes**: Analyze all code changes made during implementation
  2. **Identify Documentation Files**: Determine which documentation files need updates based on:
     - Data model changes → Update `ai-specs/specs/data-model.md`
     - API endpoint changes → Update `ai-specs/specs/api-spec.yml`
     - Standards/libraries/config changes → Update relevant `*-standards.mdc` files
     - Architecture changes → Update relevant architecture documentation
  3. **Update Documentation**: For each affected file:
     - Update content in English (as per `documentation-standards.mdc`)
     - Maintain consistency with existing documentation structure
     - Ensure proper formatting
  4. **Verify Documentation**: 
     - Confirm all changes are accurately reflected
     - Check that documentation follows established structure
  5. **Report Updates**: Document which files were updated and what changes were made
- **References**: 
  - Follow process described in `ai-specs/specs/documentation-standards.mdc`
  - All documentation must be written in English
- **Notes**: This step is MANDATORY before considering the implementation complete. Do not skip documentation updates.

### 5. **Implementation Order**
- Numbered list of steps in sequence (must start with Step 0: Create Feature Branch and end with documentation update step)

### 6. **Testing Checklist**
- Post-implementation verification checklist

### 7. **Error Response Format**
- JSON structure
- HTTP status code mapping

### 8. **Partial Update Support** (if applicable)
- Behavior for partial updates

### 9. **Dependencies**
- External libraries and tools required

### 10. **Notes**
- Important reminders and constraints
- Business rules
- Language requirements

### 11. **Next Steps After Implementation**
- Post-implementation tasks (documentation is already covered in Step N+1, but may include integration, deployment, etc.)

### 12. **Implementation Verification**
- Final verification checklist:
  - Code Quality
  - Functionality
  - Testing
  - Integration
  - Documentation updates completed
