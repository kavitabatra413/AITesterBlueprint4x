# Salesforce Login Automation Framework (Playwright)

This project is a starter Playwright implementation for Salesforce login automation based on the framework plan.

## Setup

1. Install dependencies:
   npm install
2. Update values in `.env` with valid Salesforce credentials.
3. Run tests:
   npm test

## Useful commands

- `npm test` – run all tests
- `npm run test:headed` – run in headed browser mode
- `npm run test:debug` – debug a Playwright test
- `npm run report` – open HTML report

## Notes

- Keep all credentials in `.env` and do not hardcode them in test code.
- Salesforce can require MFA or SSO depending on the environment.
