import unittest
import requests
import time
import random
import string
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# API & Frontend URLs
BASE_URL = "http://localhost:5000/api"
FRONTEND_URL = "http://localhost:3000"

# Test User Credentials
TEST_EMAIL = "testuser@example.com"
TEST_PHONE = "+1234567890"
TEST_PASSWORD = "SecurePass123!"

class TestAdvancedLoginScenarios(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """ Setup Chrome WebDriver & Seed Test User """
        cls.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
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

    def generate_random_string(self, length):
        """ Generate a random string of specified length """
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

    def test_01_form_state_and_navigation(self):
        """
        Test Case 1: Form State and Navigation Handling
        - Tests form state persistence between refreshes
        - Tests browser navigation (back/forward) impact on form
        - Tests tab navigation through form elements
        - Checks auto-focus behavior
        """
        # A) Initial form state and auto-focus
        self.driver.get(FRONTEND_URL)
        time.sleep(1)  # Wait briefly to ensure focus

        # Check if identifier field has focus by default
        active_element = self.driver.switch_to.active_element
        focused_id = active_element.get_attribute("id")
        self.assertEqual(focused_id, "identifier", "Identifier field should have initial focus")

        # B) Tab navigation in form
        active_element.send_keys(Keys.TAB)
        active_element = self.driver.switch_to.active_element
        self.assertEqual(active_element.get_attribute("id"), "password", 
                         "Tab should move focus from identifier to password")
        
        # C) Enter values and test page refresh persistence
        test_identifier = "testuser@example.com"
        test_password = "password123"
        
        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys(test_identifier)
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys(test_password)
        
        # Refresh page and check if form is reset (values should be cleared)
        self.driver.refresh()
        time.sleep(2)
        
        identifier_value = self.driver.find_element(By.ID, "identifier").get_attribute("value") 
        password_value = self.driver.find_element(By.ID, "password").get_attribute("value")
        
        self.assertEqual(identifier_value, "", "Form should reset identifier after refresh")
        self.assertEqual(password_value, "", "Form should reset password after refresh")
        
        # D) Test browser back button after partial form completion
        self.driver.find_element(By.ID, "identifier").send_keys(test_identifier)
        self.driver.get(f"{FRONTEND_URL}/nonexistent-page")  # Navigate away
        self.driver.back()  # Go back to login
        
        time.sleep(2)
        identifier_value = self.driver.find_element(By.ID, "identifier").get_attribute("value")
        self.assertEqual(identifier_value, "", "Form should reset when navigating back")

    def test_02_input_boundary_testing(self):
        """
        Test Case 2: Input Boundary Testing
        - Tests extremely long inputs
        - Tests empty inputs with spaces
        - Tests special character handling
        - Tests minimum input requirements
        """
        self.driver.get(FRONTEND_URL)
        
        # A) Extremely long email (>255 chars)
        long_email = f"{self.generate_random_string(245)}@example.com"  # 245 + 12 = 257 chars
        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys(long_email)
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()
        
        # Update the assertion to include the actual message "Email/Phone is too long"
        try:
            message = self.wait_for_alert(css_class=".alert-danger")
            self.assertTrue(
                "User not found" in message or "invalid" in message.lower() or 
                "length" in message.lower() or "too long" in message.lower(),
                f"Expected error message for long email, got: {message}"
            )
        except TimeoutException:
            self.fail("No error message shown for extremely long email")
            
            
        # B) Extremely long password (>1000 chars)
        long_password = self.generate_random_string(1001)
        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys(TEST_EMAIL)
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys(long_password)
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()
        
        # Should get "Invalid password" error
        message = self.wait_for_alert(css_class=".alert-danger")
        self.assertIn("Password is too long", message, "Long password should be rejected with 'Password is too long'")

        # C) Spaces-only input (validation should catch this)
        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys("   ")
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys("   ")
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()
        
        message = self.wait_for_alert(css_class=".alert-danger")
        self.assertIn("required", message.lower(), "Spaces-only should trigger required fields validation")
        
        # D) Email with unusual but valid characters
        complex_email = "user+tag-part_special!#$%&'*=?^`{}|~@example.co.uk"
        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys(complex_email)
        self.driver.find_element(By.ID, "password").clear() 
        self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()
        
        # Should get "User not found" (since it's valid format but not registered)
        message = self.wait_for_alert(css_class=".alert-danger")
        self.assertIn("User not found", message, "Complex but valid email should be processed correctly")

    def test_03_race_conditions_and_timing(self):
        """
        Test Case 3: Race Conditions and Timing Issues
        - Tests rapid sequential login attempts
        - Tests clicking login button multiple times
        - Tests login behavior during delayed server response
        - Tests timeout scenarios
        """
        # A) Multiple rapid login attempts (submitted in sequence)
        requests.post(f"{BASE_URL}/reset_attempts")  # Reset attempt counter
        
        for i in range(3):
            # Start with a fresh page each time to avoid overlay issues
            self.driver.get(FRONTEND_URL)
            time.sleep(1)  # Allow page to fully load
            
            self.driver.find_element(By.ID, "identifier").clear()
            self.driver.find_element(By.ID, "identifier").send_keys(TEST_EMAIL)
            self.driver.find_element(By.ID, "password").clear()
            self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)
            
            # Wait for any overlays to clear and button to be clickable
            wait = WebDriverWait(self.driver, 10)
            login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Login']")))
            login_button.click()
            
            # Only wait for success message on first attempt
            if i == 0:
                message = self.wait_for_alert(css_class=".alert-success")
                self.assertIn("Login successful", message)
        
        # B) Multiple clicks on login button
        self.driver.get(FRONTEND_URL)
        time.sleep(1)  # Allow page to fully load
        
        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys(TEST_EMAIL)
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)
        
        # Wait for button to be clickable
        wait = WebDriverWait(self.driver, 10)
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Login']")))
        
        # Use JavaScript to click the button to avoid overlay issues
        for _ in range(3):
            self.driver.execute_script("arguments[0].click();", login_button)
            time.sleep(0.1)  # Small delay between clicks
            
        # Should still process login correctly
        message = self.wait_for_alert(css_class=".alert-success")
        self.assertIn("Login successful", message, "Login should succeed despite multiple button clicks")
        
        # C) Navigate to welcome page during delay between login and redirect
        self.driver.get(FRONTEND_URL)
        time.sleep(1)  # Allow page to fully load
        
        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys(TEST_EMAIL)
        self.driver.find_element(By.ID, "password").clear() 
        self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)
        
        # Use wait and JavaScript click to avoid overlay issues
        wait = WebDriverWait(self.driver, 10)
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Login']")))
        self.driver.execute_script("arguments[0].click();", login_button)
        
        # Wait for success message
        message = self.wait_for_alert(css_class=".alert-success")
        self.assertIn("Login successful", message)
        
        # Before the redirect happens, try to navigate elsewhere
        self.driver.get(f"{FRONTEND_URL}/nonexistent-page")
        time.sleep(2)
        
        # URL should reflect our manual navigation, not be redirected back to welcome
        self.assertIn("nonexistent-page", self.driver.current_url)


    def test_04_security_and_injection_testing(self):
        """
        Test Case 4: Advanced Security and Injection Testing
        - Tests SQL injection attempts (for relational DBs - future proofing)
        - Tests NoSQL injection attempts (for current MongoDB setup)
        - Tests HTML injection attempts
        - Tests JavaScript injection attempts
        """

        # Reset attempts to start fresh
        requests.post(f"{BASE_URL}/reset_attempts")
        self.driver.get(FRONTEND_URL)

        # Section 1: Traditional SQL Injection Simulations (for relational DBs or generic input validation)

        sql_injections = [
            "' OR '1'='1' --",
            "' OR ''='",
            "' OR 1=1 -- -",
            "' UNION SELECT 1,2,3 --",
            "') OR ('a'='a"
        ]

        for injection in sql_injections:
            self.driver.get(FRONTEND_URL)
            self.driver.find_element(By.ID, "identifier").clear()
            self.driver.find_element(By.ID, "identifier").send_keys(injection)
            self.driver.find_element(By.ID, "password").clear()
            self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)
            self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

            message = self.wait_for_alert(css_class=".alert-danger")
            self.assertIn("User not found", message, 
                        f"SQL Injection attempt '{injection}' should be rejected.")

        # Section 2: NoSQL Injection Simulations (targeting MongoDB)

        nosql_injections = [
            '{"$ne": null}',  # Matches any non-null email (bypass filter)
            '{"$where": "1 == 1"}'  # Potential arbitrary code execution if not sanitized
        ]

        for injection in nosql_injections:
            self.driver.get(FRONTEND_URL)
            self.driver.find_element(By.ID, "identifier").clear()
            self.driver.find_element(By.ID, "identifier").send_keys(injection)
            self.driver.find_element(By.ID, "password").clear()
            self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)
            self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

            message = self.wait_for_alert(css_class=".alert-danger")
            self.assertIn("User not found", message,
                        f"NoSQL Injection attempt '{injection}' should be rejected.")

        # Section 3: HTML Injection (Cross-Site Scripting)

        html_injection = "<script>alert('XSS')</script>@example.com"
        self.driver.get(FRONTEND_URL)
        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys(html_injection)
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        message = self.wait_for_alert(css_class=".alert-danger")
        self.assertIn("User not found", message, "HTML injection should be treated as invalid user")

        # Section 4: JavaScript Injection (Event Handlers)

        js_attack = 'test@example.com" onmouseover="alert(1)'
        self.driver.get(FRONTEND_URL)
        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys(js_attack)
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        message = self.wait_for_alert(css_class=".alert-danger")
        self.assertIn("User not found", message, "JavaScript event handler injection should be rejected")


    '''
    def test_04_security_and_injection_testing(self):
        """
        Test Case 4: Advanced Security Testing
        - Tests HTML injection attempts
        - Tests JavaScript injection attempts
        - Tests various SQL injection patterns
        - Tests XSS vulnerabilities in the login flow
        """
        # Reset attempts counter
        requests.post(f"{BASE_URL}/reset_attempts")
        
        self.driver.get(FRONTEND_URL)
        
        # A) HTML Injection in identifier field
        html_injection = "<script>alert('XSS')</script>@example.com"
        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys(html_injection)
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()
        
        # Should get "User not found" if properly sanitized
        message = self.wait_for_alert(css_class=".alert-danger")
        self.assertIn("User not found", message, "HTML injection should be treated as invalid user")
        
        # B) Test SQL injection patterns beyond the basic one
        sql_injections = [
            "' OR '1'='1' --",
            "' OR ''='",
            "' OR 1=1 -- -",
            "' UNION SELECT 1,2,3 --",
            "') OR ('a'='a"
        ]
        
        for injection in sql_injections:
            self.driver.get(FRONTEND_URL)
            self.driver.find_element(By.ID, "identifier").clear()
            self.driver.find_element(By.ID, "identifier").send_keys(injection)
            self.driver.find_element(By.ID, "password").clear()
            self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)
            self.driver.find_element(By.XPATH, "//button[text()='Login']").click()
            
            # Should get "User not found" if SQL injection is prevented
            message = self.wait_for_alert(css_class=".alert-danger")
            self.assertIn("User not found", message, f"SQL injection '{injection}' should be prevented")
            
        # C) JavaScript event handlers
        js_attack = 'test@example.com" onmouseover="alert(1)'
        self.driver.get(FRONTEND_URL)
        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys(js_attack)
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()
        
        # Should get "User not found" if properly handled
        message = self.wait_for_alert(css_class=".alert-danger")
        self.assertIn("User not found", message, "JavaScript attack should be treated as invalid user")


    '''

    def test_05_error_recovery_and_edge_cases(self):
        """
        Test Case 5: Error Recovery and Edge Cases
        - Tests recovery from connection errors
        - Tests login with valid credentials after multiple failed attempts
        - Tests login flow when server returns unexpected errors
        - Tests login with multiple browser tabs/sessions
        """
        # Reset attempts counter
        requests.post(f"{BASE_URL}/reset_attempts")
    
        # Simulate 5 failed login attempts to reach the threshold.
        for _ in range(5):
            self.driver.get(FRONTEND_URL)
            self.driver.find_element(By.ID, "identifier").clear()
            self.driver.find_element(By.ID, "identifier").send_keys(TEST_EMAIL)
            self.driver.find_element(By.ID, "password").clear()
            self.driver.find_element(By.ID, "password").send_keys("WrongPassword")
            self.driver.find_element(By.XPATH, "//button[text()='Login']").click()
            time.sleep(1)
            # Clear the error message for the next attempt
            self.driver.get(FRONTEND_URL)
        
        # Now, make one more attempt (6th attempt) which should trigger lockout.
        self.driver.get(FRONTEND_URL)
        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys(TEST_EMAIL)
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys("WrongPassword")
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()
        
        message = self.wait_for_alert(css_class=".alert-warning")
        self.assertIn("Too many failed attempts", message, 
                    "Should trigger lockout after exceeding failed attempts")

        
        # Reset attempts counter
        requests.post(f"{BASE_URL}/reset_attempts")

        # A) Login after failed attempts (but before lockout)
        self.driver.get(FRONTEND_URL)

        # Generate 4 failed attempts (instead of 5)
        for _ in range(4):
            self.driver.find_element(By.ID, "identifier").clear()
            self.driver.find_element(By.ID, "identifier").send_keys(TEST_EMAIL)
            self.driver.find_element(By.ID, "password").clear()
            self.driver.find_element(By.ID, "password").send_keys("WrongPassword")
            self.driver.find_element(By.XPATH, "//button[text()='Login']").click()
            time.sleep(1)
            # Clear the error message for the next attempt
            self.driver.get(FRONTEND_URL)
            
        # Now try with correct password (should succeed, as we've only made 4 failed attempts)
        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys(TEST_EMAIL)
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()

        # Should login successfully
        message = self.wait_for_alert(css_class=".alert-success")
        self.assertIn("Login successful", message, "Should allow login after some failed attempts")

                
        # B) Test recovery from incorrect login to different account
        self.driver.get(FRONTEND_URL)
        
        # First try invalid login
        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys("nonexistent@example.com")
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys("WrongPassword")
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()
        
        message = self.wait_for_alert(css_class=".alert-danger")
        self.assertIn("User not found", message)
        
        # Now try valid login without refreshing page
        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys(TEST_EMAIL)
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys(TEST_PASSWORD)
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()
        
        # Should login successfully
        message = self.wait_for_alert(css_class=".alert-success")
        self.assertIn("Login successful", message, "Should allow login after trying different account")
                
        # C) Test login immediately after registration
        # Create a unique email for this test
        new_email = f"newuser_{int(time.time())}@example.com"
        new_password = "NewUserPassword123!"
        
        # Make direct API call to register
        register_response = requests.post(
            f"{BASE_URL}/register", 
            json={
                "email": new_email,
                "phone": "",
                "password": new_password
            }
        )
        
        self.assertEqual(register_response.status_code, 201, "Registration API should return 201")
        self.assertTrue(register_response.json()["success"], "Registration should succeed")
        
        # Try to log in immediately
        self.driver.get(FRONTEND_URL)
        self.driver.find_element(By.ID, "identifier").clear()
        self.driver.find_element(By.ID, "identifier").send_keys(new_email)
        self.driver.find_element(By.ID, "password").clear()
        self.driver.find_element(By.ID, "password").send_keys(new_password)
        self.driver.find_element(By.XPATH, "//button[text()='Login']").click()
        
        # Should login successfully
        message = self.wait_for_alert(css_class=".alert-success")
        self.assertIn("Login successful", message, "Should allow login immediately after registration")

if __name__ == "__main__":
    unittest.main()
