# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import time

# Django
from django.test import LiveServerTestCase
from django.contrib.auth.models import User

# Selenium
try:
    from selenium.webdriver.firefox.webdriver import WebDriver
except ImportError:
    WebDriver = None

class UITests(LiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        if WebDriver:
            cls.selenium = WebDriver()
        else:
            cls.selenium = None
        super(UITests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        if cls.selenium:
            cls.selenium.quit()
        super(UITests, cls).tearDownClass()

    def delay(self, s=1):
        time.sleep(s)

    def setUp(self):
        if not self.selenium:
            self.skipTest('selenium is not installed')
        self.superuser = User.objects.create_superuser('admin', 'admin@example.com', 'password')

    def test_login(self, username='admin', password='password'):
        if not self.selenium:
            return
        self.selenium.implicitly_wait(10)
        self.selenium.get(self.live_server_url)
        login_dialog = self.selenium.find_element_by_id('login-modal')
        self.assertTrue(login_dialog)
        self.delay()
        username_input = self.selenium.find_element_by_name('login_username')
        username_input.send_keys(username)
        self.delay()
        password_input = self.selenium.find_element_by_name('login_password')
        password_input.send_keys(password)
        self.delay()
        self.selenium.find_element_by_id('login-button').click()
        self.delay()
        alert_dialog = self.selenium.find_element_by_id('alert-modal')
        self.assertTrue(alert_dialog)
        self.delay()
        ok_button = alert_dialog.find_element_by_link_text('OK')
        self.assertTrue(ok_button)
        ok_button.click()
        self.delay()
        logout_link = self.selenium.find_element_by_link_text('Logout')
        self.assertTrue(logout_link)
        self.delay()
        logout_link.click()
        self.delay()
