import unittest
import time
import requests
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

    def test_01_valid_login(self):
        """ ✅ Test Case 1: Valid Email & Password Login """
        self.driver.get(f"{FRONTEND_URL}/login")

        self.driver.find_element(By.ID, "identifier").send_keys(TEST_EMAIL)
        self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        wait = WebDriverWait(self.driver, 10)
        message_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-success")))
        message = message_element.text

        self.assertIn("Login successful", message)

    def test_02_invalid_password(self):
        """ ❌ Test Case 2: Valid Email, Wrong Password """
        self.driver.get(f"{FRONTEND_URL}/login")

        self.driver.find_element(By.ID, "identifier").send_keys(TEST_EMAIL)
        self.driver.find_element(By.ID, "password").send_keys("WrongPassword")
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        wait = WebDriverWait(self.driver, 10)
        message_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-danger")))
        message = message_element.text

        self.assertIn("Invalid password", message)

    def test_03_nonexistent_user(self):
        """ ❌ Test Case 3: Non-existent User """
        self.driver.get(f"{FRONTEND_URL}/login")

        self.driver.find_element(By.ID, "identifier").send_keys("doesnotexist@example.com")
        self.driver.find_element(By.ID, "password").send_keys("randompassword")
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        wait = WebDriverWait(self.driver, 10)
        message_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-danger")))
        message = message_element.text

        self.assertIn("User not found", message)

    def test_04_google_login(self):
        """ 🔄 Test Case 4: Google OAuth Login """
        self.driver.get(f"{FRONTEND_URL}/login")

        self.driver.find_element(By.XPATH, "//button[contains(text(),'Login with Google')]").click()
        
        time.sleep(3)  # Wait for Google login page to load
        
        # Ensure Google OAuth page opens
        self.assertIn("accounts.google.com", self.driver.current_url)

    def test_05_empty_fields(self):
        """ ❌ Test Case 5: Empty Email & Password Fields """
        self.driver.get(f"{FRONTEND_URL}/login")

        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        wait = WebDriverWait(self.driver, 10)
        message_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-danger")))
        message = message_element.text

        self.assertIn("Email/Phone and Password are required", message)

    def test_06_sql_injection(self):
        """ 🔥 Test Case 6: SQL Injection Attempt """
        self.driver.get(f"{FRONTEND_URL}/login")

        self.driver.find_element(By.ID, "identifier").send_keys("admin' OR 1=1 --")
        self.driver.find_element(By.ID, "password").send_keys("password")
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        wait = WebDriverWait(self.driver, 10)
        message_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-danger")))
        message = message_element.text

        self.assertIn("Invalid email or password", message)

    def test_07_brute_force_protection(self):
        """ 🔐 Test Case 7: Brute Force Protection (Rate Limiting) """
        for _ in range(6):  # Simulate 6 failed login attempts
            self.driver.get(f"{FRONTEND_URL}/login")

            self.driver.find_element(By.ID, "identifier").send_keys(TEST_EMAIL)
            self.driver.find_element(By.ID, "password").send_keys("wrongpassword")
            self.driver.find_element(By.XPATH, "//button[text()='Login']").click()
            time.sleep(1)

        wait = WebDriverWait(self.driver, 10)
        message_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-warning")))
        message = message_element.text

        self.assertIn("Too many failed attempts", message)

    def test_08_ui_elements(self):
        """ 🎨 Test Case 8: UI Checks (Disabled Button, Password Masking) """
        self.driver.get(f"{FRONTEND_URL}/login")

        email_input = self.driver.find_element(By.ID, "identifier")
        password_input = self.driver.find_element(By.ID, "password")
        login_button = self.driver.find_element(By.XPATH, "//button[text()='Login']")

        email_input.clear()
        password_input.clear()

        self.assertFalse(login_button.is_enabled())  # Button should be disabled initially

        password_input.send_keys("password")
        self.assertEqual(password_input.get_attribute("type"), "password")  # Should be masked

    def test_09_session_persistence(self):
        """ 🔄 Test Case 9: Session Persistence After Refresh """
        self.test_01_valid_login()  # Log in first
        self.driver.refresh()  # Refresh the page

        # Check if the session is still valid (User should still be logged in)
        wait = WebDriverWait(self.driver, 10)
        profile_icon = wait.until(EC.presence_of_element_located((By.ID, "profile-icon")))

        self.assertTrue(profile_icon.is_displayed())


if __name__ == "__main__":
    unittest.main()
