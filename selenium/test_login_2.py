import unittest
import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# API & Frontend URLs
BASE_URL = "http://localhost:5000/api"
FRONTEND_URL = "http://localhost:3000"

# Test User Credentials
TEST_EMAIL = "testuser@example.com"
TEST_PHONE = "+1234567890"
TEST_PASSWORD = "SecurePass123!"

class TestLogin(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """ Setup Chrome WebDriver & Seed Test User """
        cls.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        cls.driver.get(FRONTEND_URL)
        cls.driver.maximize_window()
        cls.driver.implicitly_wait(5)

        # Seed a test user into MongoDB
        cls.seed_test_user()

    @classmethod
    def tearDownClass(cls):
        """ Close browser after tests """
        cls.driver.quit()

    @classmethod
    def seed_test_user(cls):
        """ Calls the Flask backend to create a test user. """
        response = requests.post(f"{BASE_URL}/seed_user", json={
            "email": TEST_EMAIL,
            "phone": TEST_PHONE,
            "password": TEST_PASSWORD
        })
        print(f"Seeding Test User Response: {response.json()}")

    def wait_for_alert(self, css_class=".alert-danger", timeout=10):
        """ Helper method to wait for and return alert message """
        wait = WebDriverWait(self.driver, timeout)
        message_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_class)))
        return message_element.text

    def test_01_valid_login(self):
        """ ✅ Test Case 1: Valid Email & Password Login """
        self.driver.get(FRONTEND_URL)

        self.driver.find_element(By.ID, "identifier").send_keys(TEST_EMAIL)
        self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        wait = WebDriverWait(self.driver, 10)
        message_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-success")))
        message = message_element.text

        self.assertIn("Login successful", message)

    def test_02_invalid_password(self):
        """ ❌ Test Case 2: Valid Email, Wrong Password """
        self.driver.get(FRONTEND_URL)

        self.driver.find_element(By.ID, "identifier").send_keys(TEST_EMAIL)
        self.driver.find_element(By.ID, "password").send_keys("WrongPassword")
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        wait = WebDriverWait(self.driver, 10)
        message_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-danger")))
        message = message_element.text

        self.assertIn("Invalid password", message)

    def test_03_nonexistent_user(self):
        """ ❌ Test Case 3: Non-existent User """
        self.driver.get(FRONTEND_URL)

        self.driver.find_element(By.ID, "identifier").send_keys("doesnotexist@example.com")
        self.driver.find_element(By.ID, "password").send_keys("randompassword")
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        message = self.wait_for_alert(css_class=".alert-danger")
        self.assertIn("User not found", message)

    def test_04_google_login(self):
        """ 🔄 Test Case 4: Google OAuth Login """
        self.driver.get(FRONTEND_URL)

        self.driver.find_element(By.XPATH, "//button[contains(text(),'Login with Google')]").click()
        
        time.sleep(3)  # Wait for Google login page to load
        
        # Ensure Google OAuth page opens
        self.assertIn("accounts.google.com", self.driver.current_url)

    def test_05_empty_fields(self):
        """ ❌ Test Case 5: Empty Email & Password Fields """
        self.driver.get(FRONTEND_URL)

        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "password").clear()
        
        # Now click the login button (it's NOT disabled anymore in our updated React code)
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        # Expect an alert danger about required fields
        message = self.wait_for_alert(css_class=".alert-danger")
        self.assertIn("Email/Phone and Password are required", message)

    def test_06_sql_injection(self):
        """ 🔥 Test Case 6: SQL Injection Attempt """
        self.driver.get(FRONTEND_URL)

        self.driver.find_element(By.ID, "identifier").send_keys("admin' OR 1=1 --")
        self.driver.find_element(By.ID, "password").send_keys("password")
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        # Backend likely responds "User not found"
        message = self.wait_for_alert(css_class=".alert-danger")
        self.assertIn("User not found", message)

    def test_07_ui_elements(self):
        """ 🎨 Test Case 8 (labeled #07 in code): UI Checks (Button, Password Masking) """
        # We kept the original numbering from your snippet, but you can rename as needed.
        self.driver.get(FRONTEND_URL)

        email_input = self.driver.find_element(By.ID, "identifier")
        password_input = self.driver.find_element(By.ID, "password")
        login_button = self.driver.find_element(By.XPATH, "//button[text()='Login']")

        email_input.clear()
        password_input.clear()

        # Because we removed the "disabled" attribute, the button is always enabled.
        # If you want to test that it's "visually" disabled, you'd have different logic:
        self.assertTrue(login_button.is_enabled(), "Login button should be enabled for the test.")

        password_input.send_keys("password")
        self.assertEqual(password_input.get_attribute("type"), "password", "Password should be masked")

    def test_08_session_persistence(self):
        """ 🔄 Test Case 9: Session Persistence After Refresh """
        self.driver.get(FRONTEND_URL)
        self.driver.find_element(By.ID, "identifier").send_keys(TEST_EMAIL)
        self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()
        
        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-success")))
        
        # Wait for navigation to /welcome
        time.sleep(2)
        self.assertIn("/welcome", self.driver.current_url)

        # Check if welcome text is shown
        welcome_text = self.driver.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Welcome", welcome_text)

        # Refresh
        self.driver.refresh()
        time.sleep(2)

        # We expect to still see the same page
        self.assertIn("/welcome", self.driver.current_url)
        welcome_text = self.driver.find_element(By.TAG_NAME, "h1").text
        self.assertIn("Welcome", welcome_text)

    def test_09_valid_phone_login(self):
        """ ✅ Test Case 10: Valid Phone & Password Login """
        self.driver.get(FRONTEND_URL)

        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys(TEST_PHONE)
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        message = self.wait_for_alert(css_class=".alert-success")
        self.assertIn("Login successful", message, "Phone login did not succeed as expected.")

    def test_10_only_password_provided(self):
        """ ❌ Test Case 11: Only Password Provided (No Email/Phone) """
        self.driver.get(FRONTEND_URL)

        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys("SomeRandomPassword")
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        message = self.wait_for_alert()
        self.assertIn("Email/Phone and Password are required", message)

    def test_11_only_identifier_provided(self):
        """ ❌ Test Case 12: Only Identifier Provided (No Password) """
        self.driver.get(FRONTEND_URL)

        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys(TEST_EMAIL)
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        message = self.wait_for_alert()
        self.assertIn("Email/Phone and Password are required", message)

    def test_12_whitespace_identifier(self):
        """ ❓ Test Case 13: Identifier (Email) With Leading/Trailing Whitespace """
        self.driver.get(FRONTEND_URL)

        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys(f"   {TEST_EMAIL}   ")
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        # If whitespace is trimmed in the backend, this should be a successful login
        try:
            message = self.wait_for_alert(css_class=".alert-success", timeout=5)
            self.assertIn("Login successful", message)
        except:
            # If it's not trimmed, we might get "User not found"
            message = self.wait_for_alert(css_class=".alert-danger", timeout=5)
            self.assertIn("User not found", message)

    def test_13_special_characters_in_email(self):
        """
        ❔ Test Case 14: Special Characters in Email.
        If not seeded, likely gets 'User not found'.
        """
        special_email = "test+label@example.com"
        self.driver.get(FRONTEND_URL)

        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys(special_email)
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        # Expect "User not found"
        try:
            message = self.wait_for_alert(css_class=".alert-danger", timeout=5)
            self.assertIn("User not found", message)
        except:
            self.fail("Expected 'User not found' alert was not displayed")

    def test_14_logout_flow(self):
        """ 🔓 Test Case 15: Logout Functionality (If Implemented) """
        # First login
        self.driver.get(FRONTEND_URL)
        self.driver.find_element(By.ID, "identifier").send_keys(TEST_EMAIL)
        self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()
        
        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-success")))
        time.sleep(2)
        
        # Attempt to find and click the logout button
        try:
            logout_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Logout')]")
            logout_button.click()
            time.sleep(2)
            self.assertIn("login", self.driver.current_url.lower())
        except:
            self.fail("Logout button not found or logout functionality failed.")

    # -- MOVED BRUTE-FORCE TEST TO THE END SO THE USER IS NOT LOCKED OUT FOR OTHERS --
    def test_z07_brute_force_protection(self):
        """ 🔐 Test Case 7: Brute Force Protection (Rate Limiting) - runs LAST """
        for _ in range(6):  # Simulate 6 failed login attempts
            self.driver.get(FRONTEND_URL)
            self.driver.find_element(By.ID, "identifier").clear()
            self.driver.find_element(By.ID, "identifier").send_keys(TEST_EMAIL)
            self.driver.find_element(By.ID, "password").clear()
            self.driver.find_element(By.ID, "password").send_keys("wrongpassword")
            self.driver.find_element(By.XPATH, "//button[text()='Login']").click()
            time.sleep(1)

        message = self.wait_for_alert(css_class=".alert-warning")
        self.assertIn("Too many failed attempts", message)

if __name__ == "__main__":
    unittest.main()
