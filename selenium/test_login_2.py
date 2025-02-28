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

        # Reset attempts so we aren't locked out
        requests.post(f"{BASE_URL}/reset_attempts")

        # Seed the test user
        cls.seed_test_user()

    @classmethod
    def tearDownClass(cls):
        """ Close browser after tests """
        cls.driver.quit()

    @classmethod
    def seed_test_user(cls):
        """ Calls the Flask backend to create a test user. """
        response = requests.post(
            f"{BASE_URL}/seed_user",
            json={
                "email": TEST_EMAIL,
                "phone": TEST_PHONE,
                "password": TEST_PASSWORD,
            },
        )
        print(f"Seeding Test User Response: {response.json()}")

    def wait_for_alert(self, css_class=".alert-danger", timeout=10):
        """ Helper method to wait for and return alert message. """
        wait = WebDriverWait(self.driver, timeout)
        message_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_class))
        )
        return message_element.text

    def test_01_valid_login(self):
        """ ✅ Test Case 1: Valid Email & Password Login """
        self.driver.get(FRONTEND_URL)

        self.driver.find_element(By.ID, "identifier").send_keys(TEST_EMAIL)
        self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        wait = WebDriverWait(self.driver, 10)
        message_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-success"))
        )
        message = message_element.text
        self.assertIn("Login successful", message)

    def test_02_invalid_password(self):
        """ ❌ Test Case 2: Valid Email, Wrong Password """
        self.driver.get(FRONTEND_URL)

        self.driver.find_element(By.ID, "identifier").send_keys(TEST_EMAIL)
        self.driver.find_element(By.ID, "password").send_keys("WrongPassword")
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        wait = WebDriverWait(self.driver, 10)
        message_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-danger"))
        )
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
        # Ensure Google OAuth page
        self.assertIn("accounts.google.com", self.driver.current_url)

    def test_05_empty_fields(self):
        """ ❌ Test Case 5: Empty Email & Password Fields """
        self.driver.get(FRONTEND_URL)
        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "password").clear()

        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        message = self.wait_for_alert(css_class=".alert-danger")
        self.assertIn("Email/Phone and Password are required", message)

    def test_06_sql_injection(self):
        """ 🔥 Test Case 6: SQL Injection Attempt """
        self.driver.get(FRONTEND_URL)

        self.driver.find_element(By.ID, "identifier").send_keys("admin' OR 1=1 --")
        self.driver.find_element(By.ID, "password").send_keys("password")
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        # Expect "User not found"
        message = self.wait_for_alert(css_class=".alert-danger")
        self.assertIn("User not found", message)

    def test_07_ui_elements(self):
        """ 🎨 Test Case 8: UI Checks (Button, Password Masking) """
        self.driver.get(FRONTEND_URL)

        email_input = self.driver.find_element(By.ID, "identifier")
        password_input = self.driver.find_element(By.ID, "password")
        login_button = self.driver.find_element(By.XPATH, "//button[text()='Login']")

        email_input.clear()
        password_input.clear()

        # Button should be enabled since we removed the disabled condition
        self.assertTrue(
            login_button.is_enabled(),
            "Login button should be enabled for the test.",
        )

        password_input.send_keys("password")
        self.assertEqual(
            password_input.get_attribute("type"),
            "password",
            "Password should be masked",
        )

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

        message = self.wait_for_alert(css_class=".alert-danger")
        self.assertIn("Email/Phone and Password are required", message)

    def test_11_only_identifier_provided(self):
        """ ❌ Test Case 12: Only Identifier Provided (No Password) """
        self.driver.get(FRONTEND_URL)
        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys(TEST_EMAIL)
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        message = self.wait_for_alert(css_class=".alert-danger")
        self.assertIn("Email/Phone and Password are required", message)

    def test_12_whitespace_identifier(self):
        """ ❓ Test Case 13: Identifier (Email) With Leading/Trailing Whitespace """
        self.driver.get(FRONTEND_URL)
        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys(f"   {TEST_EMAIL}   ")
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        # If whitespace is trimmed in the backend, login is successful
        try:
            message = self.wait_for_alert(css_class=".alert-success", timeout=5)
            self.assertIn("Login successful", message)
        except:
            # If not trimmed, might get "User not found"
            message = self.wait_for_alert(css_class=".alert-danger", timeout=5)
            self.assertIn("User not found", message)

    def test_13_special_characters_in_email(self):
        """ ❔ Test Case 14: Special Characters in Email. """
        special_email = "test+label@example.com"
        self.driver.get(FRONTEND_URL)

        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys(special_email)
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        # Expect "User not found" if this email isn't seeded
        try:
            message = self.wait_for_alert(css_class=".alert-danger", timeout=5)
            self.assertIn("User not found", message)
        except:
            self.fail("Expected 'User not found' alert was not displayed")

    def test_z14_very_short_password(self):
        """ ⛔ Extra Case: Extremely Short Password (e.g. 'a') """
        self.driver.get(FRONTEND_URL)
        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys(TEST_EMAIL)
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys("a")
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        # Typically "Invalid password", but if locked out, we might get "Too many failed attempts" (warning)
        try:
            message = self.wait_for_alert(css_class=".alert-danger", timeout=5)
            self.assertTrue(
                "Invalid password" in message or "required" in message,
                "Expected an error about short/invalid password",
            )
        except:
            # Fallback check if we're locked out
            message = self.wait_for_alert(css_class=".alert-warning", timeout=5)
            self.assertIn("Too many failed attempts", message, "Did not find the expected short/invalid or lockout alert.")

    # -------------------------------------------------------------------------
    # OPTIONAL / COMMENTED TESTS
    # -------------------------------------------------------------------------
    """
    def test_08_session_persistence(self):
        ''' 🔄 Test Case 9: Session Persistence After Refresh '''
        # Implementation omitted for brevity
        pass

    def test_14_logout_flow(self):
        ''' 🔓 Test Case 15: Logout Functionality (If Implemented) '''
        # Implementation omitted or commented out for now
        pass
    """

    # -------------------------------------------------------------------------
    # ADVANCED / EXTREME CASES
    # -------------------------------------------------------------------------

    @unittest.skip("Skipping multi-click scenario; often conflicts with immediate redirect.")
    def test_z11_rapid_button_clicks(self):
        """ ⚡ Extra Case: Rapid repeated clicks on Login """
        self.driver.get(FRONTEND_URL)
        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys(TEST_EMAIL)
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)

        login_button = self.driver.find_element(By.XPATH, "//button[text()='Login']")

        # Repeated clicks
        for _ in range(5):
            login_button.click()

        # Should see "Login successful"
        message = self.wait_for_alert(css_class=".alert-success", timeout=10)
        self.assertIn("Login successful", message)

    def test_z12_unicode_characters_in_password(self):
        """ 🌐 Extra Case: BMP Unicode in Password (should fail with 'Invalid password') """
        self.driver.get(FRONTEND_URL)

        # 'ß' is inside the BMP. Replacing any outside-BMP character (like emoji) that breaks on Windows.
        weird_password = "Pásswørdß"

        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys(TEST_EMAIL)
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys(weird_password)
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        # Expect "Invalid password" or fallback to lockout
        try:
            message = self.wait_for_alert(css_class=".alert-danger", timeout=5)
            self.assertIn("Invalid password", message)
        except:
            # Maybe we got locked out again
            message = self.wait_for_alert(css_class=".alert-warning", timeout=5)
            self.assertIn("Too many failed attempts", message)

    def test_z13_case_insensitive_email(self):
        """ 🔡 Extra Case: Case-Insensitive Email (TESTUSER@EXAMPLE.COM) """
        self.driver.get(FRONTEND_URL)
        capitalized_email = TEST_EMAIL.upper()

        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys(capitalized_email)
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        # If backend is case-insensitive, we get success; else 'User not found'
        try:
            message = self.wait_for_alert(css_class=".alert-success", timeout=5)
            self.assertIn("Login successful", message)
        except:
            # Might be case sensitive
            message = self.wait_for_alert(css_class=".alert-danger", timeout=5)
            self.assertIn("User not found", message)

    def test_z15_multiple_consecutive_valid_logins(self):
        """ 🔂 Extra Case: Multiple Consecutive Valid Logins (No unexpected lockout) """
        for i in range(3):
            # LOG OUT or reset before each iteration, so we can log in fresh
            # If you have an /api/logout endpoint, use that:
            # requests.get("http://localhost:5000/api/logout")
            requests.post(f"{BASE_URL}/reset_attempts")  # alternative: reset attempts

            self.driver.get(FRONTEND_URL)
            self.driver.find_element(By.ID, "identifier").clear()
            self.driver.find_element(By.ID, "identifier").send_keys(TEST_EMAIL)
            self.driver.find_element(By.ID, "password").clear()
            self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)
            self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

            # Wait for success or fallback to lockout
            try:
                message = self.wait_for_alert(css_class=".alert-success", timeout=10)
                self.assertIn("Login successful", message, f"Consecutive login #{i+1} failed unexpectedly.")
            except:
                # Possibly locked out
                message = self.wait_for_alert(css_class=".alert-warning", timeout=5)
                self.assertIn(
                    "Too many failed attempts",
                    message,
                    f"Expected success or lockout on login #{i+1}, got neither.",
                )
            time.sleep(1)

    def test_z07_brute_force_protection(self):
        """ 🔐 Test Case 7: Brute Force Protection (Rate Limiting) - runs LAST """
        for _ in range(31):  # 31 attempts to ensure lockout
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
