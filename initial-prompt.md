This is a Claude Connector that integrates with YNAB so that I can have insights into my budget through Claude.

Tech stack:
- Backend: Python + Flask (To Discuss with me)
- Tests: Unsure what is the best practice on this front for python

TDD is REQUIRED (non-negotiable):
- Follow Red–Green–Refactor.
- For every behavior in the specs, write tests FIRST (failing), then implement.
- The task list must explicitly sequence: tests → implementation → refactor.
- Always RUN tests after each implementation to ensure they pass.

Include a comprehensive README.md file in the root of the project that explains how to run the application and how to run the tests.

Documentation
- https://claude.com/docs/connectors/building
- https://api.ynab.com/

Extra
- Use the repo located on the local filesystem `/Users/cference/Code/claude-toolkit` for relevant skills and agents.

Features (minimal, more features to be added later, this is just to get started). Features will be described as Acceptance Criteria, use these for your TDD tests, additionally, think of at least two edge cases for the tests:
1. Basic Github Project Scaffolding with CICD on Github using Github Actions
   - Version Control should follow semantic versioning schema
   - `main` branch has the latest major release (this builds and ships the main package via CICD)
   - `development` branch has the latest dev changes (experimental builds)
   - Feel free to propose a different strategy (and update this spec as needed)
2. Basic Python Project that can be built through CICD, no YNAB features yet
3. Build the basic integration into YNAB (Auth for a YNAB single user, GET queries for example)
   - YNAB Credentials are to be stored locally, and NEVER in any capacity find itself on git
4. Implementation of all endpoints under the "User" Category.
5. Implementation of all endpoints under the "Plans" Category.
6. Implementation of all endpoints under the "Categories" Category
7. Implementation of all endpoints under the "Payees" Category
8. Implementation of all endpoints under the "Payee Locations" Category
9. Implementation of all endpoints under the "Months" Category
10. Implementation of all endpoints under the "Money Movements" Category

More features to come.

Constraints / non-goals:
- This is a connector, so no UI
- Provide Given/When/Then acceptance criteria with at least 2 edge cases per feature.
- Functional Programming highly desired over imperative style
- Python Best practices encouraged
- Using type hints in python highly encouraged
- Clean Code is a must
