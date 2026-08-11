package com.salesforce.login.pages;

import com.salesforce.login.util.WaitUtils;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.FindBy;
import org.openqa.selenium.support.PageFactory;

public class LoginPage {
    private final WebDriver driver;

    @FindBy(xpath = "//input[@name='username' or @id='username']")
    private WebElement usernameInput;

    @FindBy(xpath = "//input[@name='pw' or @id='password']")
    private WebElement passwordInput;

    @FindBy(xpath = "//input[@type='submit' and contains(@value,'Log In')]")
    private WebElement loginButton;

    @FindBy(xpath = "//input[@type='checkbox' and contains(@name,'remember')]")
    private WebElement rememberMeCheckbox;

    @FindBy(xpath = "//div[contains(@class,'error') or contains(@class,'slds-has-error') or contains(@id,'error')]")
    private WebElement errorMessage;

    public LoginPage(WebDriver driver) {
        this.driver = driver;
        PageFactory.initElements(driver, this);
    }

    public void enterUsername(String username) {
        try {
            WaitUtils.waitForVisible(driver, By.xpath("//input[@name='username' or @id='username']")).clear();
            usernameInput.clear();
            usernameInput.sendKeys(username);
        } catch (Exception e) {
            throw new RuntimeException("Unable to enter username", e);
        }
    }

    public void enterPassword(String password) {
        try {
            WaitUtils.waitForVisible(driver, By.xpath("//input[@name='pw' or @id='password']")).clear();
            passwordInput.clear();
            passwordInput.sendKeys(password);
        } catch (Exception e) {
            throw new RuntimeException("Unable to enter password", e);
        }
    }

    public void clickLogin() {
        try {
            WaitUtils.waitForClickable(driver, By.xpath("//input[@type='submit' and contains(@value,'Log In')]"));
            loginButton.click();
        } catch (Exception e) {
            throw new RuntimeException("Unable to click login", e);
        }
    }

    public void doLogin(String username, String password) {
        enterUsername(username);
        enterPassword(password);
        clickLogin();
    }

    public boolean isRememberMeSelected() {
        try {
            return rememberMeCheckbox.isSelected();
        } catch (Exception e) {
            return false;
        }
    }

    public boolean isErrorMessageDisplayed() {
        try {
            return errorMessage.isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }

    public String getErrorMessageText() {
        try {
            return errorMessage.getText();
        } catch (Exception e) {
            return "";
        }
    }
}
