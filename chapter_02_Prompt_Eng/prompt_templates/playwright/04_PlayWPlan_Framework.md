# Salesforce Login Automation Framework Plan (Playwright)

## 1. Objective
Build a Playwright + JavaScript/TypeScript + Node.js framework for Salesforce login automation using the login page at `https://login.salesforce.com/?locale=in`.

The goal is to test both valid and invalid login flows with a clean Page Object Model, reusable fixtures, robust configuration handling, and reliable waiting strategies.

---

## 2. Project Goal
Create a maintainable automation framework that can:

- launch the Salesforce login page
- validate successful login
- validate login failure scenarios
- reuse a central configuration file
- keep selectors stable and readable
- avoid flaky waits and brittle UI code
- support cross-browser execution with Playwright

---

## 3. Recommended Tech Stack

- Node.js 18+
- Playwright
- JavaScript or TypeScript
- Test Runner: Playwright Test
- dotenv for environment variables
- Page Object Model (POM)
- Playwright locators (`getByRole`, `getByLabel`, `locator`)
- `config` or `.env` for environment data

---

## 4. Project Structure

```text
chapter_02_Prompt_Eng/
└── PlaywrightSalesforceFramework/
    ├── package.json
    ├── playwright.config.ts
    ├── tsconfig.json
    ├── .env
    ├── tests/
    │   ├── login/
    │   │   ├── valid-login.spec.ts
    │   │   └── invalid-login.spec.ts
    └── src/
        ├── pages/
        │   └── LoginPage.ts
        ├── fixtures/
        │   └── test.ts
        ├── utils/
        │   ├── config.ts
        │   └── helpers.ts
        └── data/
            └── credentials.ts
```

---

## 5. Roles and Responsibilities

### Base Layer
- `playwright.config.ts`
- configures browser projects, test retries, timeouts, and base URL
- sets test execution defaults
- manages reporter and environment settings

### Utility Layer
- `config.ts`
- reads values from `.env` or configuration files
- stores runtime settings like URL, credentials, and timeout values

- `helpers.ts`
- provides reusable logic for waiting, navigation, assertions, and element interactions
- centralizes custom helper methods to avoid duplication

### Page Layer
- `LoginPage.ts`
- contains all login page selectors and methods
- uses Playwright locators such as `page.getByLabel()`, `page.locator()`, and `getByRole()`
- includes actions like:
  - enter username
  - enter password
  - click login
  - verify error text
  - verify remember me state
  - perform full login flow

### Test Layer
- `valid-login.spec.ts`
- covers successful login behavior

- `invalid-login.spec.ts`
- covers invalid credentials and empty field validation

---

## 6. Core Design Principles

1. Use Playwright locators rather than raw XPath when possible.
2. Prefer semantic selectors such as role, label, and text-based locators.
3. Avoid hardcoded waits like `setTimeout()` or manual sleep logic.
4. Use page objects to keep tests readable and maintainable.
5. Keep credentials in `.env` instead of hardcoding them.
6. Wrap UI interactions in meaningful page methods.
7. Keep test methods short and scenario-focused.
8. Add proper assertions for login states and validation messages.

---

## 7. Playwright Locator Strategy

For Salesforce login pages, use selectors like:

```ts
const emailField = page.getByLabel('Username');
const passwordField = page.getByLabel('Password');
const loginButton = page.getByRole('button', { name: 'Log In' });
const rememberMeCheckbox = page.locator("//label[contains(., 'Remember me')]");
```

If the Salesforce DOM changes, prefer stable semantic selectors first, then fallback to locator strategies like text or XPath when necessary.

---

## 8. File-Level Plan

### 8.1 `package.json`
Add dependencies for:

- `@playwright/test`
- `dotenv`

Configure scripts for:

- running all tests
- running headed mode
- running a specific spec
- generating reports

### 8.2 `.env`
Example:

```env
BASE_URL=https://login.salesforce.com/?locale=in
BROWSER=chromium
VALID_USERNAME=your_valid_email@example.com
VALID_PASSWORD=your_valid_password
HEADLESS=true
```

### 8.3 `config.ts`
Responsibilities:

- load environment variables from `.env`
- provide centralized config access for URL, credentials, and timeout values
- return fallback/default values when a key is missing

### 8.4 `helpers.ts`
Responsibilities:

- wait for page navigation
- wait for visible elements
- handle login failures gracefully
- provide consistent assertions and utility wrappers

### 8.5 `playwright.config.ts`
Responsibilities:

- define browser projects
- set common timeout values
- configure retries
- manage base URL and reporter
- enable screenshots and trace collection when needed

### 8.6 `LoginPage.ts`
Responsibilities:

- define page elements and selectors
- implement actions such as:
  - `enterUsername(username: string)`
  - `enterPassword(password: string)`
  - `clickLogin()`
  - `login(username: string, password: string)`
  - `getErrorMessage()`
  - `isErrorVisible()`
  - `isRememberMeChecked()`

### 8.7 `valid-login.spec.ts`
Suggested test cases:

- valid login succeeds
- user is redirected after successful authentication
- login page elements are visible and usable
- remember me checkbox can be toggled

### 8.8 `invalid-login.spec.ts`
Suggested test cases:

- wrong password shows error
- empty username should fail
- empty password should fail
- both fields empty should fail
- invalid email format should trigger validation

---

## 9. Execution Flow

1. Node loads the Playwright package and configuration.
2. `config.ts` reads environment values from `.env`.
3. `playwright.config.ts` initializes the browser context and base URL.
4. `LoginPage` is instantiated with the page object.
5. Tests call page methods to interact with login controls.
6. Assertions validate successful login or failure states.
7. Playwright automatically handles cleanup and browser closure after each test or suite.

---

## 10. Acceptance Criteria

The framework is considered complete when:

- the Playwright project installs and builds without errors
- tests run successfully with Playwright Test
- valid and invalid login scenarios are covered
- no manual sleep/wait hacks remain in the test automation layer
- selectors are stable and readable
- config values are externalized and not hardcoded
- page object methods are reusable and maintainable
- tests are easy to run across different browsers

---

## 11. Risks and Notes

- Salesforce can display different DOM states depending on locale, session, or MFA requirements.
- SSO, CAPTCHA, or MFA may block automated login in real environments.
- Some input fields may behave differently in production compared with a demo org.
- Keep the code flexible enough to support environment-specific changes through `.env` or config files.

---

## 12. Final Summary
This framework should be implemented as a professional Playwright automation project. The focus is on maintainability, reusability, and reliability: a proper configuration layer, page object model, reusable test utilities, and dedicated valid/invalid login specs.

The final deliverable is a clean, runnable Playwright framework that demonstrates modern QA automation practices without introducing brittle selectors or poor waiting strategies.
