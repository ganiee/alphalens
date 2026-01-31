AlphaLens – Base Product Requirements Document (PRD Base)
    Status: Canonical / Mostly Frozen
    This Base PRD defines the non-negotiable product constitution, architecture, governance, and core rules for AlphaLens. All Phase PRDs EXTEND this document and MUST NOT override it.

1. Purpose
AlphaLens is an AI-powered stock analysis and recommendation platform that helps users identify investment opportunities using technical indicators, fundamental analysis, and news sentiment.
The platform is designed to deliver transparent, explainable investment insights, with strict cost controls, observability, and extensibility for future capabilities (alerts, backtesting, broker integrations).

2. Product Principles (Invariant)
    • Explainability over black-box predictions
    • Deterministic scoring + AI summarization (LLM never decides)
    • Cost-aware by design (usage limits, caching, metering)
    • Incremental, feature-by-feature delivery
    • Mobile-friendly first, native apps later

3. Target Users
End Users
    • Retail investors
    • Long-term and swing investors
    • Users seeking explainable AI-driven stock ideas
Admin Users
    • Product owner / operator
    • Needs visibility into users, usage, cost, health, and overrides

4. High-Level Architecture (Base)
Frontend
    • Next.js (TypeScript, React)
    • Responsive, mobile-first UI
    • Hosted on Vercel
Backend
    • Python FastAPI
    • Hosted on AWS (ECS Fargate)
    • Stateless API layer
Authentication
    • Amazon Cognito (User Pools)
    • OAuth: Google
    • Email/password registration
    • Roles: user, admin

5. Core Platform Capabilities (Always-On)
    • OAuth authentication & role-based access
    • Usage metering and enforcement
    • Cost tracking (AWS + LLM)
    • Observability & monitoring
    • Feature flags

6. Plans & Usage Model (Base Rules)
Usage Accounting
    • Each recommendation run consumes exactly 1 run
    • Viewing history or derived projections consumes 0 runs
Admin Overrides
    • Admin may adjust per-user limits
    • Admin may grant temporary unlimited access

7. UI/UX Global Contract (Base)
These rules apply to all phases.
    • Mobile-first responsive design
    • Calm, professional UI (no trading/gambling visuals)
    • Progressive disclosure for advanced details
    • Clear disclaimers (educational only)

8. Explainability Contract (Base)
    • LLMs summarize computed evidence
    • LLMs are NOT decision-makers
    • Evidence packets must be stored per run
    • Derived horizons reuse evidence (no recompute)

9. Caching & Data Freshness (Base)
Mandatory Layer
    • Data cache for prices, indicators, fundamentals, sentiment
    • Shared across users
Rules
    • Never bypass usage limits
    • Never hide stale data
    • Always disclose data freshness

10. Monitoring & Observability (Base)
Metrics
    • Latency (p50 / p95)
    • Error rates
    • Throughput
    • Cache hit rate
    • Cost per run
Tooling
    • OpenTelemetry
    • CloudWatch dashboards

11. Modularity & Extensibility Strategy (MANDATORY)
Architectural Style
Ports & Adapters (Clean Architecture)
Required Interfaces
    • MarketDataProvider
    • FundamentalsProvider
    • NewsProvider
    • SentimentAnalyzer
    • LLMClient
    • RecommendationEngine
    • CostMeter
    • AuthVerifier
Backend Layering
routers/
domain/
services/
adapters/
repo/

12. Recommendation Engine Contract (Base)
Pipeline steps:
FetchData → ComputeFeatures → Score → Rank → Allocate → Explain
Rules:
    • Each step deterministic & testable
    • Steps must be reusable as LangGraph nodes later

13. Feature Governance System (MANDATORY)
Feature Index
    • /docs/feature-index.md is source of truth
    • Immutable feature IDs: F###
PRD Index
    • /docs/prd.index.md tracks phases & states
Per-Feature Contract
docs/features/F###-short-name/
spec.md
tasks.md
tests.md
acceptance.md
rollback.md

“Feature status cannot be set to Complete unless tests pass and acceptance criteria are verified.”

14. Phase Lifecycle Rules (Base)
    • One active phase at a time
    • Completed phases are Frozen
    • New capabilities require Phase PRD
    
    Phase Activation Rule
    When the user explicitly instructs to “start Phase X development”, Claude MUST:
        1. Create or update docs/prd.index.md to mark:
            ○ Phase X → Active
            ○ All earlier phases → Frozen (if applicable)
        2. Initialize or update docs/feature-index.md with:
            ○ All features listed in the active Phase PRD
            ○ Status set to Planned
        3. Only then begin Feature F000 or the first feature of that phase.
    

15. Compliance & Disclaimers
    • Educational purposes only
    • No financial advice
    • No guaranteed returns

16.Feature ID Governance (MANDATORY – AlphaLens)
16. Feature Identification & Numbering Scheme (Canonical)
All features MUST follow a Phase-qualified Feature ID format.
16.1 Feature ID Format

F<phase>-<feature_number>
Examples
    • F1-1 → Phase 1, Feature 1
    • F1-2 → Phase 1, Feature 2
    • F1.5-1 → Phase 1.5, Feature 1
    • F1.5-2 → Phase 1.5, Feature 2
    • F2-3 → Phase 2, Feature 3
    Phase identifiers MUST exactly match the Phase PRD label
    (e.g., 1, 1.5, 2.0 → stored as 1, 1.5, 2 unless explicitly stated otherwise)

16.2 Immutability Rules
    • Feature IDs are immutable once assigned
    • Feature IDs MUST NEVER be:
        ○ Renumbered
        ○ Reused
        ○ Reassigned to a different phase
    • Deleted features must remain in feature-index.md with status Removed or Deprecated

16.3 Feature Index Contract (Updated)
/docs/feature-index.md MUST include the following columns in this order:

| Column | Description |
|--------|-------------|
| Feature ID | Immutable ID in format F<phase>-<number> |
| Phase | Phase number (1, 1.5, 2, etc.) |
| Status | Planned, In Progress, Blocked, In Review, Complete |
| Title | Short descriptive name |
| PRD Reference | Link to phase PRD file |
| Spec | Link to spec.md (or "-" if not yet created) |
| Tasks | Link to tasks.md (or "-" if not yet created) |
| Acceptance | Link to acceptance.md (or "-" if not yet created) |
| Tests | Link to tests.md (or "-" if not yet created) |
| Rollback | Link to rollback.md (or "-" if not yet created) |

Example header:
```
| Feature ID | Phase | Status | Title | PRD Reference | Spec | Tasks | Acceptance | Tests | Rollback |
```

Example entry:
```
| F1-2 | 1 | In Progress | Recommendation Engine | [prd.phase-1.md](prd.phase-1.md) | [spec](features/F1-2-recommendation-engine/spec.md) | [tasks](features/F1-2-recommendation-engine/tasks.md) | [acceptance](features/F1-2-recommendation-engine/acceptance.md) | [tests](features/F1-2-recommendation-engine/tests.md) | [rollback](features/F1-2-recommendation-engine/rollback.md) |
```

Note: Feature documentation links are populated when a feature transitions to "In Progress". Planned features use "-" as placeholder.

16.4 Feature Folder Naming (Mandatory)
Each feature’s documentation folder MUST be named using the full Feature ID:

docs/features/F<phase>-<feature_number>-short-name/
Example:

docs/features/F1.5-2-news-sentiment/
├── spec.md
├── tasks.md
├── tests.md
├── acceptance.md
└── rollback.md


16.5 Phase Activation Rule (Clarified with Feature IDs)
When a phase is activated:
    1. Claude MUST read the Phase PRD and extract all features
    2. Claude MUST assign Feature IDs using:
        ○ Sequential numbering within that phase only
        ○ Starting from 1
    3. Claude MUST update docs/feature-index.md with:
        ○ Feature ID
        ○ Phase
        ○ Initial status = Planned
Feature numbering resets per phase
(e.g., Phase 1 → F1-1, Phase 1.5 → F1.5-1)

16.6 One-Feature-at-a-Time Enforcement (ID-aware)
    • Claude may only work on one Feature ID at a time
    • The active feature is always:
        ○ The lowest-numbered Planned feature in the Active phase
        ○ OR a user-explicitly selected Feature ID
    • Claude MUST reference the Feature ID in:
        ○ Commits
        ○ Docs
        ○ Test descriptions
        ○ Status updates

16.7 Test-Gated Completion (ID-scoped)
A feature F<phase>-<n> may be marked Complete only when:
    • Tests associated with that Feature ID pass
    • Acceptance criteria for that Feature ID are met
    • Feature index status is updated atomically


17. Claude Development Governance (MANDATORY)
This section defines how development proceeds, not product behavior.
17.1 Canonical Index Files
    • Phase index: docs/prd.index.md
    • Feature index: docs/feature-index.md
These files are the single source of truth for development state.

17.2 Phase Lifecycle Enforcement
    • Only one phase may be Active at a time
    • Phase states: Planned → Active → Frozen
    • Completed phases MUST be Frozen
Phase Activation Rule
When instructed to “start Phase X development”, the system MUST:
    1. Update docs/prd.index.md
    2. Mark Phase X = Active
    3. Freeze earlier phases
    4. Initialize feature entries for Phase X as Planned
    5. Only then allow feature development to begin

17.3 One-Feature-at-a-Time Rule
    • During an Active phase, only one feature may be In Progress
    • Features must be completed sequentially unless explicitly overridden by the user

17.4 Feature Status Model
Valid statuses:
    • Planned
    • In Progress
    • Blocked
    • In Review
    • Complete

17.5 Test-Gated Completion (Non-Negotiable)
A feature may be marked Complete only if:
    • Feature-scoped tests exist
    • Tests pass
    • Acceptance criteria are explicitly verified

17.6 Mandatory Feature Documentation
Each feature MUST have:

docs/features/F<phase>-<n>-short-name/
├── spec.md
├── tasks.md
├── tests.md
├── acceptance.md
└── rollback.md


17.7 Index Update Requirements
Indexes MUST be updated:
    • At phase activation
    • When a feature starts
    • When a feature completes or is blocked


18. Testing & Mocking Contract (MANDATORY)
18.1 Testability Requirement
    • Every feature MUST be independently testable.
    • Each feature folder MUST include tests.md describing test coverage and mapping to code tests.
18.2 Definition of Done (DoD)
A feature may be marked Done only when:
    • Automated tests for the feature exist and pass
    • Acceptance criteria are verified
    • Feature index status updated to Done
18.3 Mocking Policy
    • External boundaries MUST be mocked/faked in unit tests:
        ○ Market data provider
        ○ Fundamentals provider
        ○ News provider
        ○ Sentiment analyzer
        ○ LLM client
        ○ Auth verifier / Cognito
        ○ Cost meter / usage enforcement
    • Domain logic MUST be tested without network calls.
    • Prefer dependency injection via interfaces/ports so mocks are straightforward.
18.4 Types of Tests
    • Unit tests: fast, deterministic; heavy use of mocks for ports/adapters.
    • Integration tests: can use test containers or local fakes; still no real paid/external APIs by default.
    • Contract tests (optional): verify adapter behavior against provider schemas (recorded fixtures allowed).
18.5 Test Data & Fixtures
    • Use fixed, versioned fixtures for prices/news responses.
    • Freeze time for indicator calculations where relevant.
    • No flaky tests (no reliance on "current market time" or live endpoints).

19. UI Architecture & Contracts (Invariant)

- UI is defined using **screen-level contracts**, not pixel specifications.
- Each user-facing route MUST define:
  - Purpose
  - Required UI states (loading, error, empty, success)
  - Allowed user actions
  - Routing rules
  - Data contract (inputs / outputs)
  - Explicit constraints (what the screen must NOT do)

- Visual layout, styling, and component composition are implementation details
  and MAY vary, but contracts MUST be honored.

- Phase PRDs define which screens exist.
- Feature PRDs define the contract for each screen they touch.

20. Infrastructure as Code Governance (MANDATORY)

20.1 IaC Tooling (Strict)
    • All AWS infrastructure MUST be provisioned using AWS CDK.
    • Manual AWS Console changes are prohibited except for emergency debugging.
    • Any emergency manual change MUST be captured back into CDK within 48 hours.

20.2 Infra Folder Contract (Feature-Scoped)
    • All infrastructure code MUST live under /infra.
    • Infra is organized as:
        ○ /infra/shared/ → shared platform infra (VPC, base IAM, logging)
        ○ /infra/features/<FeatureID>-<short-name>/ → feature-owned infra
    • Each Feature ID owns its infra module exclusively.
    • Feature infra MUST NOT modify shared infra directly.

20.3 Stack Naming Convention
    • All stacks MUST follow:
        alphalens-<env>-<FeatureID>-<purpose>
    • Examples:
        ○ alphalens-dev-F1-1-cognito
        ○ alphalens-prod-F3-2-dynamodb
    • Environments allowed:
        ○ dev
        ○ stage
        ○ prod

20.4 Infra Ownership Rule
    • Every infra stack MUST be owned by exactly one Feature ID.
    • Infra stacks MAY NOT be modified by unrelated features without explicit documentation.

20.5 Canonical Infra Mapping Index
    • docs/infra/infra-index.md is the single source of truth mapping:
        Feature ID → Infra module → Stack(s) → Outputs → Consumers
    • The file MUST contain the following table columns:

| Column | Description |
|--------|-------------|
| Feature ID | Owner feature in format F<phase>-<number> |
| Stack Name | Full stack name following naming convention |
| Module Path | Path to CDK module under /infra |
| Purpose | Brief description of what the stack provisions |
| Key Outputs | CloudFormation outputs or SSM parameters |
| Consumed By | Features or components that use these outputs |
| Deploy Command | make command to deploy |
| Rollback Command | make command to destroy/rollback |

    • Any feature that creates or modifies infrastructure MUST add or update an entry.
    • Infra changes are invalid if this index is not updated.

20.6 Infra Outputs & Config Hydration Contract
    • Infra stacks MUST expose required values via:
        ○ CloudFormation Outputs
        ○ AWS SSM Parameter Store (preferred)
    • Application config files (auth.yaml, .env) MUST derive values from infra outputs.
    • Manual copy/paste of infra identifiers is discouraged long-term.
    • Config hydration from SSM via scripts is the recommended pattern.
    • Example SSM output paths:
        /alphalens/<env>/auth/userPoolId
        /alphalens/<env>/auth/clientId
        /alphalens/<env>/auth/issuer
        /alphalens/<env>/auth/domain

20.7 Infra-to-Feature Governance (Hard Gating)
    • Any feature introducing or modifying infra MUST:
        ○ Declare its infra module path
        ○ Add/update its entry in docs/infra/infra-index.md
        ○ Reference infra in spec.md and rollback.md
    • A feature may NOT be marked Complete unless infra mapping is present.
    • Optionally, an Infra column MAY be added to docs/feature-index.md.

20.8 Infrastructure CI Enforcement (MANDATORY)
CI Validation Rules
    • CI MUST fail if:
        ○ Infra code under /infra/features/<FeatureID>/ is modified
        ○ AND docs/infra/infra-index.md is not updated
    • CI MUST fail if:
        ○ A feature is marked Complete
        ○ AND required infra documentation is missing

CI Responsibilities
    • CI MUST verify:
        ○ Stack naming follows convention
        ○ Infra module path matches Feature ID
        ○ Feature docs reference infra where applicable

CI Is Authoritative
    • CI failures BLOCK merge
    • CI enforcement applies equally to humans and AI agents

20.9 Deterministic Infra Execution Interface
    • Standardized infra commands:
        make infra-synth ENV=<env> FEATURE=<FeatureID>
        make infra-diff ENV=<env> FEATURE=<FeatureID>
        make infra-deploy ENV=<env> FEATURE=<FeatureID>
        make infra-destroy ENV=<env> FEATURE=<FeatureID>
    • Infra MUST be deployable using these commands.
    • Claude MUST NOT invent custom deployment steps.

20.10 Non-Normative Example: F1-1 Cognito (Reference Only)
    Feature F1-1 (OAuth Authentication & Roles) owns:
        • Cognito User Pool
        • Public App Client (PKCE)
        • Hosted UI Domain
        • OAuth Providers (Google optional)

    Example stack: alphalens-dev-F1-1-cognito

    Outputs consumed by frontend login flow and backend JWT verification.

    This example is illustrative and non-normative.

21. Pull Request & CI Governance (MANDATORY)

21.1 Feature Branch & PR Workflow
    • Every feature MUST be developed on a dedicated branch.
    • Branch naming convention: F<phase>-<n>-<short-name>
        ○ Example: F1-1-Oauth, F1-2-recommendation-engine
    • Upon feature completion, a Pull Request MUST be created to merge into main.
    • Direct commits to main are prohibited.

21.2 Pull Request Requirements
    • PR title format: F<phase>-<n>: <Feature Title>
        ○ Example: F1-1: OAuth Authentication & Roles
    • PR body MUST include:
        ○ Summary: Brief description of changes (bullet points)
        ○ Test Plan: How to verify the changes
        ○ Acceptance Checklist: Key acceptance criteria verified
    • PR template (.github/pull_request_template.md) MUST be used.

21.3 CI Pipeline Requirements (MANDATORY)
    • CI pipeline MUST run on:
        ○ Every PR targeting main
        ○ Every push to main
    • CI pipeline MUST include:
        ○ Backend: Install dependencies, run pytest, run ruff lint
        ○ Frontend: Install dependencies, run eslint, run build
        ○ Infra validation (if /infra modified): Verify infra-index.md updated
    • CI configuration lives in .github/workflows/ci.yml

21.4 CI Pass Required for Merge (Non-Negotiable)
    • All CI jobs MUST pass (green) before PR can be merged.
    • Branch protection on main MUST require:
        ○ CI status checks to pass
        ○ At least one approval (if team > 1)
    • Failed CI BLOCKS merge - no exceptions.

21.5 Feature Completion Gating
    • A feature may only be marked Complete when:
        ○ PR is created
        ○ CI passes
        ○ PR is merged to main
    • Feature index status update to Complete MUST happen after merge.

21.6 Standardized PR Commands
    • Create PR: make pr FEATURE=<FeatureID>
    • Run CI locally: make ci
    • Commands are defined in Makefile.

21.7 CI Enforcement Scope
    CI MUST verify:
        • Backend tests pass (pytest)
        • Backend lint passes (ruff)
        • Frontend lint passes (eslint)
        • Frontend builds successfully (next build)
        • Infra index updated (if infra changed)
        • Feature docs exist (if feature marked Complete)

