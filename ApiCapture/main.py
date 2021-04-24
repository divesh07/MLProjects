# pylint: disable-all

import re

from seleniumwire import webdriver
from webdriver_manager.firefox import GeckoDriverManager


from DbDriver import DbUtils

if __name__ == "__main__":
    host = 'http://172.18.14.22:8088/#/login'
    driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())
    driver.response_interceptor = DbUtils.interceptor
    driver.request_interceptor = DbUtils.mock_server
    driver.maximize_window()
    #Need to call this only once or check if table already exists
    #Driver.create_table()

    try:
        driver.get(host)
        driver.get('http://172.18.14.22:8088/#/data/tables')
        DbUtils.unset_interceptor(driver)
        driver.close()
    except Exception as exp:
        print(exp)
        DbUtils.unset_interceptor(driver)
        driver.close()
