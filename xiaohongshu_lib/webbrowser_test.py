import time
import traceback
from selenium import webdriver

url = r"https://www.xiaohongshu.com/explore?channel_id=homefeed_recommend"
# url = r"https://baidu.com"
driver = webdriver.Chrome()

driver.get(url)

anchor_list = []

while True:
    try:
        tar = driver.find_elements(by=webdriver.common.by.By.TAG_NAME, value="a")

        for a in tar:
            text = a.text if a.text != "" else a.get_attribute("innerHTML")
            href = a.get_attribute("href")
            if a.text != "" and text not in anchor_list:
                print(f"{text}: {href}".encode('utf-8'))
                anchor_list.append(text)
                # a.click()

    except Exception as e:
        traceback.print_exc()
    finally:
        time.sleep(1)
