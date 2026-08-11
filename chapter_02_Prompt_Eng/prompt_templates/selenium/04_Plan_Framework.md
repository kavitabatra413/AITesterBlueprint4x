# Salesforce Login Automation Framework Plan

## 1. Objective
Build a Selenium + Java + Maven + TestNG framework for Salesforce login automation using the login page at `https://login.salesforce.com/?locale=in`.

The goal is to test both valid and invalid login flows with a clean Page Object Model, robust configuration handling, and reusable base utilities.

---

## 2. Project Goal
Create a maintainable automation framework that can:

- launch the Salesforce login page
- validate successful login
- validate login failure scenarios
- reuse a central configuration file
- keep selectors stable and readable
- avoid hardcoded waits and fragile UI code

---

## 3. Recommended Tech Stack

- Java 11+
- Maven
- Selenium WebDriver 4.x
- TestNG
- WebDriverManager
- Page Object Model (POM)
- XPath-based locators
- `config.properties` for environment data

---

## 4. Project Structure

```text
chapter_02_Prompt_Eng/
└── RICE_POT_SeleniumAdvanceFramework/
    ├── pom.xml
    ├── testng.xml
    ├── src/
    │   ├── test/
    │   │   ├── java/
    │   │   │   └── com/salesforce/login/
    │   │   │       ├── base/
    │   │   │       │   └── BaseTest.java
    │   │   │       ├── pages/
    │   │   │       │   └── LoginPage.java
    │   │   │       ├── tests/
    │   │   │       │   ├── ValidLoginTest.java
    │   │   │       │   └── InvalidLoginTest.java
    │   │   │       └── util/
    │   │   │           ├── ConfigReader.java
    │   │   │           └── WaitUtils.java
    │   │   └── resources/
    │   │       └── config.properties
```

---

## 5. Roles and Responsibilities

### Base Layer
- `BaseTest.java`
- handles browser setup
- initializes WebDriver
- loads URL
- manages cleanup after each test suite

### Utility Layer
- `ConfigReader.java`
- reads values from `config.properties`
- stores runtime configuration like URL, credentials, timeout values

- `WaitUtils.java`
- provides reusable explicit waits
- avoids `Thread.sleep()`
- improves reliability for dynamic page loading

### Page Layer
- `LoginPage.java`
- contains all login page elements and methods
- uses `PageFactory` and `@FindBy(xpath = "...")`
- includes actions like:
  - enter username
  - enter password
  - click login
  - verify error text
  - verify remember me state
  - perform full login flow

### Test Layer
- `ValidLoginTest.java`
- covers successful login behavior

- `InvalidLoginTest.java`
- covers invalid credentials and empty field validation

---

## 6. Core Design Principles

1. Use XPath-based locators only.
2. Do not use `By.id()`, `By.name()`, or CSS selectors for page elements.
3. Avoid `Thread.sleep()`.
4. Use `PageFactory` and `@FindBy` for page object creation.
5. Keep credentials in `config.properties` instead of hardcoding them.
6. Wrap UI interactions in meaningful methods.
7. Keep test methods short and business-focused.
8. Add exception handling for login failures and page state verification.

---

## 7. Selenium Locator Strategy

For Salesforce login pages, use selectors like:

```java
@FindBy(xpath = "//input[@type='email']")
private WebElement emailField;

@FindBy(xpath = "//input[@type='password']")
private WebElement passwordField;

@FindBy(xpath = "//input[@type='submit']")
private WebElement loginButton;

@FindBy(xpath = "//label[contains(.,'Remember me')]")
private WebElement rememberMeCheckbox;
```

The important rule is to keep selectors aligned with Salesforce DOM structure and avoid brittle CSS or ID-based approaches.

---

## 8. File-Level Plan

### 8.1 `pom.xml`
Add dependencies for:

- Selenium Java
- TestNG
- WebDriverManager

Configure Maven Surefire plugin for TestNG execution.

### 8.2 `config.properties`
Example:

```properties
base.url=https://login.salesforce.com/?locale=in
browser=chrome
valid.username=your_valid_email@example.com
valid.password=your_valid_password
implicit.wait=10
explicit.wait=15
```

### 8.3 `ConfigReader.java`
Responsibilities:

- load property file
- provide methods like `getProperty(String key)`
- return default values when missing
- maintain a centralized property access layer

### 8.4 `WaitUtils.java`
Responsibilities:

- wait for element visibility
- wait for clickable state
- wait for URL change or page load
- avoid hardcoded delays

### 8.5 `BaseTest.java`
Responsibilities:

- initialize Chrome/Edge/Firefox driver
- maximize browser window
- navigate to configured base URL
- cleanup after suite execution
- expose `driver` and page objects to test classes

### 8.6 `LoginPage.java`
Responsibilities:

- define page elements
- implement actions such as:
  - `enterUsername(String username)`
  - `enterPassword(String password)`
  - `clickLogin()`
  - `doLogin(String username, String password)`
  - `getErrorMessageText()`
  - `isErrorMessageDisplayed()`
  - `isRememberMeChecked()`

### 8.7 `ValidLoginTest.java`
Suggested test cases:

- valid login succeeds
- user is redirected after successful authentication
- login page elements are present and interactable
- remember me checkbox can be selected

### 8.8 `InvalidLoginTest.java`
Suggested test cases:

- wrong password shows error
- empty username should fail
- empty password should fail
- both fields empty should fail
- invalid email format should trigger validation

---

## 9. Execution Flow

1. Maven loads dependencies from `pom.xml`.
2. `BaseTest` initializes a browser instance.
3. `ConfigReader` loads environment settings from `config.properties`.
4. `LoginPage` is created using `PageFactory`.
5. Tests call page methods to interact with form controls.
6. Assertions validate success or login failure messages.
7. Browser closes in `@AfterTest` or `@AfterSuite`.

---

## 10. Acceptance Criteria

The framework is considered complete when:

- Maven project builds without compilation errors
- Selenium tests run successfully with TestNG
- valid login and invalid login scenarios are covered
- no `Thread.sleep()` remains in Java files
- no CSS/ID-based selectors are used for login page elements
- config values are externalized and not hardcoded
- page object methods are reusable and maintainable

---

## 11. Risks and Notes

- Salesforce can show different DOM states depending on locale, session, or MFA requirements.
- SSO, CAPTCHA, or MFA may block automated login in real environments.
- Some input fields may behave differently in production compared with a demo org.
- Keep the code flexible enough to support environment-specific changes through `config.properties`.

---

## 12. Final Summary
This framework should be implemented as a small but enterprise-style automation project. The focus is on maintainability, reusability, and reliability: a proper base class, centralized configuration, a page object for the Salesforce login workflow, and dedicated valid/invalid test classes.

The final deliverable is a clean, runnable Selenium TestNG framework that demonstrates professional QA automation practices without introducing brittle selectors or poor waiting strategies.
