#coding=utf-8

# todo 需要检查是否支持
# Chrome Firfox
# 计划是直接使用Chrome59 headless
from core.parsecmd import StartCommend
from core.coreutils import is_linux
from selenium import webdriver


DRIVER_STATUS = {}
# 检查
# Chrome:	https://sites.google.com/a/chromium.org/chromedriver/downloads
# Edge:	https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/
# Firefox:	https://github.com/mozilla/geckodriver/releases
# Safari:	https://webkit.org/blog/6900/webdriver-support-in-safari-10/
if StartCommend.debug():
    try:
        chrome_options = webdriver.ChromeOptions()
        # 不加载图片，每种浏览器设置方式都不一样
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        if is_linux():
            chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(chrome_options=chrome_options)
        driver.close()
        DRIVER_STATUS['chrome'] = chrome_options
    except:
        pass

    #暂时先放弃火狐吧
else:
    # 这里必然是在安装好的环境下
    if is_linux():
        # 没有在linux下启动生产模式肯定是不对的
        try:
            chrome_options = webdriver.ChromeOptions()
            # 不加载图片，每种浏览器设置方式都不一样
            prefs = {"profile.managed_default_content_settings.images": 2}
            chrome_options.add_experimental_option("prefs", prefs)
            chrome_options.add_argument("--headless")
            driver = webdriver.Chrome(chrome_options=chrome_options)
            driver.close()
            DRIVER_STATUS['chrome'] = chrome_options
        except:
            pass
