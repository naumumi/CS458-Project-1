import unittest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TestLogin(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """ Setup Chrome WebDriver """
        cls.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        cls.driver.get("http://localhost:3000/")  # Adjust to your frontend URL
        cls.driver.maximize_window()
        cls.driver.implicitly_wait(5)  # Default implicit wait

    @classmethod
    def tearDownClass(cls):
        """ Close browser after tests """
        cls.driver.quit()

    def test_01_valid_login(self):
        """ Test Case 1: Valid Email & Password Login """
        self.driver.get("http://localhost:3000/")

        self.driver.find_element(By.ID, "identifier").send_keys("test@example.com")
        self.driver.find_element(By.ID, "password").send_keys("12345")
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        # ✅ Use WebDriverWait to ensure the message appears
        wait = WebDriverWait(self.driver, 10)
        message_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-danger")))
        message = message_element.text

        self.assertIn("Login successful", message)

    def test_02_invalid_password(self):
        """ Test Case 2: Valid Email, Wrong Password """
        self.driver.get("http://localhost:3000/")

        self.driver.find_element(By.ID, "identifier").send_keys("test@example.com")
        self.driver.find_element(By.ID, "password").send_keys("wrongpassword")
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        wait = WebDriverWait(self.driver, 10)
        message_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-danger")))
        message = message_element.text

        self.assertIn("Invalid password", message)

    def test_03_nonexistent_user(self):
        """ Test Case 3: Non-existent User """
        self.driver.get("http://localhost:3000/")

        self.driver.find_element(By.ID, "identifier").send_keys("doesnotexist@example.com")
        self.driver.find_element(By.ID, "password").send_keys("randompassword")
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        wait = WebDriverWait(self.driver, 10)
        message_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-danger")))
        message = message_element.text

        self.assertIn("User not found", message)

    def test_04_google_login(self):
        """ Test Case 4: Google Login """
        self.driver.get("http://localhost:3000/")
        
        self.driver.find_element(By.XPATH, "//button[contains(text(),'Login with Google')]").click()
        
        time.sleep(3)  # Wait for Google login page to load
        
        # Ensure Google OAuth page opens (assuming login credentials are stored)
        self.assertIn("accounts.google.com", self.driver.current_url)

    def test_05_empty_fields(self):
        """ Test Case 5: Empty Email & Password Fields """
        self.driver.get("http://localhost:3000/")

        # Click login without entering credentials
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        # ✅ Wait for the alert message to appear
        wait = WebDriverWait(self.driver, 10)
        message_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-danger")))
        message = message_element.text

        # ✅ Assert error message appears
        self.assertIn("Email/Phone and Password are required", message)


if __name__ == "__main__":
    unittest.main()
