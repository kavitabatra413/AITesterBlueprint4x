| Test ID | Description | Pre-Conditions | Steps | Expected Result | Priority |
|---|---|---|---|---|---|
| TC-001 | Verify login with valid credentials | User is on the login page | 1. Navigate to the login page. 2. Provide valid username and password.  | User is redirected to the dashboard | High |
| TC-002 | Verify Forgot Password functionality | User is on the login page | 1. Enter a registered email address. 2. Click on the “Forgot Password” link. | A password reset form appears.  | High |
| TC-003 | Verify successful reset of password | User enters a new password | 1. Enter a new password in the password field. 2. Click “Reset” | A success message appears indicating the password has been successfully reset. The user is redirected to the dashboard. | High |
| TC-004 | Test Password Reset Email | User clicks on link to reset password | 1. User confirms to reset password | Email should be displayed. | High |
| TC-005 | Verify error handling for invalid credentials | User enters invalid credentials - incorrect username/password. | 1. Enter invalid username and password. 2. Click the reset link |  "Oops! We failed." message displayed to User. | High |
| TC-006 | Test form validation in password recovery page | User clicks "Forgot Password" link.  | 1.  User clicks the password recovery link | Form shows, but validation message is shown to User, informing them the form must be filled. | Medium |
| TC-007 | Verify error messages are displayed.  | User inputs incorrect password. | 1. Input an incorrect password | A "Incorrect Password" error is displayed to the user | High |
| TC-008 | Test User redirection for "Forgot Password" | User enters a registered email on the password recovery page. | 1. User enters a registered email address.| User is redirected to the password recovery page. | High |
| TC-009 | Verify correct email confirmation | User enters registered email address in Password recovery form. | 1. User inputs a registered email address | Email confirmation successfully sent to User | High|
| TC-0010| Successful password reset| User enters a valid and registered email address for password reset  | User confirms to verify the password after a temporary reset | User is redirected to the dashboard   | High |
| TC-0011| Reset password by email for logged in user. | User is logged into the application. | 1. User chooses the Reset password option  | System will ask for required information   | Medium|
| TC-0012| Simulate reset failure | User clicks reset button after incorrect email | Login should display a relevant message error | Login Error Message is displayed to the user | High |
| TC-0013| Password recovery process | User chooses a forgotten password | 1. User selects a forgotten password | A message informing the user that they are given the option to reset the password | High |
| TC-0014| Password recovery - Validation message | User provides a correct address | 1. User enters the correct password | Valid error message is displayed to the user | High |
| TC-0015| Validation and test | User enters a valid password, successfully reset Password | Login must show message indicating that password reset was successful | Login should appear with a note that the password was set | High|
| TC-0016| Test email not received for password reset | User selects password reset | User clicks submit| Test email not received | Medium|
| TC-0017| Test email not received for password reset |User enters a valid email address | Test email is displayed | Error displayed in log - failure | High |
| TC-0018| Verification of email link | User enters a valid email | Link is active | User confirms their email access | Medium |