from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()

driver.get('https://coos.kr/ingredients')
time.sleep(1)

results = []

while True:
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.MuiBox-root.css-apds8n"))
        )
    except:
        print("페이지 로딩 실패")
        break

    boxes = driver.find_elements(By.CSS_SELECTOR, "div.MuiBox-root.css-apds8n")

    for box in boxes:
        try:
            title = box.find_element(By.CSS_SELECTOR, 'h5.MuiTypography-root.MuiTypography-h5.MuiTypography-noWrap.css-1xbj0nv').text
            content = box.find_element(By.CSS_SELECTOR, 'div.MuiBox-root.css-m3enaf').text
            results.append({'ingredient': title, 'description':content})
            print(title, content)
            print('-'*50)
        except:
            print("내용을 찾을 수 없음")
    
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, 'div.MuiBox-root.css-1jpm9pd nav.MuiPagination-root ul > li:nth-child(9) > button')
        if "disabled" in next_button.get_attribute("class"):
            print("다음 페이지 없음")
            break
        else:
            next_button.click()
            time.sleep(1)
    except:
        print('다음 버튼 없음')
        break

driver.quit()

with open('ingredients.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['ingredient', 'description'])
    writer.writeheader()
    writer.writerows(results)

print("CSV 저장 완료")