AlphaLens – Phase 1 PRD (MVP)
    Phase: Phase 1 – MVP
    State: Active
    Extends: prd.base.md
    Scope: This document defines ONLY the MVP-specific goals, features, limits, and delivery plan. All base rules apply implicitly.

1. Phase Objective
Deliver a usable, monetizable, and explainable stock recommendation product that:
    • Works reliably on web and mobile browsers
    • Enforces usage limits from day one
    • Provides admin visibility into users, cost, and system health

2. Phase Goals
    • Users can run explainable stock recommendations
    • Clear differentiation between Free and Paid plans
    • Controlled LLM and data vendor cost
    • Admin can monitor and intervene when needed

3. Phase Non-Goals
    • No guaranteed profit or performance claims
    • No auto-invest or brokerage execution
    • No intraday or real-time trading signals
    • No advanced portfolio optimization

4. Plans & Usage Limits (Phase 1 Specific)
4.1 Free Plan
    • Max 3 recommendation runs / month
    • Max 3 stocks per run
    • Primary horizon: 1 Month (1M)
    • Other horizons view-only (derived projections)
    • Limited explanation depth
    • No alerts or backtests
4.2 Paid Plan (MVP)
    • Max 20 recommendation runs / month
    • Max 5 stocks per run
    • Primary horizon selectable: 1W / 1M / 3M / 6M / 1Y
    • Full explanations
    • Priority processing

5. MVP Screens Introduced
These screens must comply with the Base UI contract.
    • Landing (/)
    • Login & Plan Selection (/login)
    • Dashboard (/dashboard)
    • Run Analysis (/analyze)
    • Results (/results/[run_id])
    • History (/history)
    • Admin Overview (/admin)
    • Admin Users (/admin/users)
    • Admin Cost (/admin/cost)
    • Admin Health (/admin/health)

6. Feature Delivery List (Phase 1)
Features are delivered incrementally and tracked in docs/feature-index.md.
Order	Feature ID	Title
0	F1-0	Project Bootstrap & CI/CD
1	F1-1	OAuth Authentication & Roles
2	F1-2	Recommendation Engine (Basic Scoring)
3	F1-3	Usage Limits Enforcement
4	F1-4	LLM Explainability Layer
5	F1-5	User Dashboard & History
6	F1-6	Admin Dashboard (Users & Usage)
7	F1-7	Cost Tracking (AWS + LLM)
8	F1-8	System Metrics & Health
9	F1-9	Real Data Providers + Caching + UI Display

7. Admin Capabilities (Phase 1)
Admin users must be able to:
    • View total users and active users
    • View per-user plan and usage
    • Override usage limits per user
    • View month-to-date cost (AWS + OpenAI)
    • View system health (latency, error rate)

8. Data Freshness & Caching (Phase 1 Scope)
Phase 1 implements Layer 1 – Data Cache only:
    • Price history
    • Technical indicators
    • Fundamental snapshots
    • News + sentiment
Recommendation result caching is explicitly out of scope for Phase 1.

9. Risks & Mitigations
Risk	Mitigation
High LLM cost	Strict run limits, caching, admin monitoring
Slow response time	Async jobs, precomputed indicators
User confusion	Clear explanations + disclaimers

10. Phase Exit Criteria (Freeze Conditions)
Phase 1 is considered complete and frozen when:
    • All Phase 1 features are marked Completed in Feature Index
    • App runs reliably in Dev and Prod
    • Usage limits enforced correctly
    • Admin dashboards operational
    • Cost per run is within acceptable budget
Once frozen, Phase 1 PRD must not be modified.
