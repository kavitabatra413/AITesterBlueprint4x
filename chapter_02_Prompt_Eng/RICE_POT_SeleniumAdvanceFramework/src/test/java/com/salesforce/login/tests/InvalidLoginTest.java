package com.salesforce.login.tests;

import com.salesforce.login.base.BaseTest;
import org.testng.Assert;
import org.testng.annotations.Test;

public class InvalidLoginTest extends BaseTest {

    @Test
    public void shouldShowErrorForWrongPassword() {
        loginPage.doLogin("testuser@example.com", "WrongPassword123");
        Assert.assertTrue(loginPage.isErrorMessageDisplayed() || driver.getPageSource().contains("Please check"),
                "Wrong password should show an error message");
    }

    @Test
    public void shouldShowErrorForEmptyUsername() {
        loginPage.doLogin("", "TestPassword123");
        Assert.assertTrue(loginPage.isErrorMessageDisplayed() || driver.getPageSource().contains("Please enter"),
                "Empty username should show a validation error");
    }

    @Test
    public void shouldShowErrorForEmptyPassword() {
        loginPage.doLogin("testuser@example.com", "");
        Assert.assertTrue(loginPage.isErrorMessageDisplayed() || driver.getPageSource().contains("Please enter"),
                "Empty password should show a validation error");
    }

    @Test
    public void shouldShowErrorForBothEmptyFields() {
        loginPage.doLogin("", "");
        Assert.assertTrue(loginPage.isErrorMessageDisplayed() || driver.getPageSource().contains("Please enter"),
                "Empty username and password should show validation errors");
    }

    @Test
    public void shouldShowErrorForInvalidEmailFormat() {
        loginPage.doLogin("invalid-email", "TestPassword123");
        Assert.assertTrue(loginPage.isErrorMessageDisplayed() || driver.getPageSource().contains("Please check"),
                "Invalid email format should show an error");
    }
}
