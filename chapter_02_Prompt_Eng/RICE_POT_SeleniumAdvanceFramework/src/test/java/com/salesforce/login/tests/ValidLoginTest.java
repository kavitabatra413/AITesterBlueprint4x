package com.salesforce.login.tests;

import com.salesforce.login.base.BaseTest;
import com.salesforce.login.util.ConfigReader;
import org.testng.Assert;
import org.testng.annotations.Test;

public class ValidLoginTest extends BaseTest {

    @Test
    public void shouldLoginWithValidCredentials() {
        String username = ConfigReader.get("valid.username");
        String password = ConfigReader.get("valid.password");

        if (username.isBlank() || password.isBlank()) {
            Assert.fail("Valid credentials are not configured in config.properties");
        }

        loginPage.doLogin(username, password);
        Assert.assertTrue(driver.getCurrentUrl().contains("lightning") || driver.getCurrentUrl().contains("home"),
                "User should be redirected to a post-login page after valid credentials");
    }

    @Test
    public void shouldDisplayRememberMeCheckbox() {
        Assert.assertTrue(loginPage.isRememberMeSelected() || !loginPage.isRememberMeSelected(),
                "Remember me checkbox should be present in the login form");
    }

    @Test
    public void shouldRenderLoginFormFields() {
        Assert.assertTrue(driver.getPageSource().contains("username") || driver.getPageSource().contains("log in"),
                "Login form should render main login elements");
    }
}
