import time
import traceback
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
prefs = {"profile.managed_default_content_settings.images": 2}  # 이미지 비활성화
chrome_options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(options=chrome_options)
base_url = "https://www.oliveyoung.co.kr/store/display/getCategoryShop.do?dispCatNo=10000010001&gateCd=Drawer&t_page=%EB%93%9C%EB%A1%9C%EC%9A%B0_%EC%B9%B4%ED%85%8C%EA%B3%A0%EB%A6%AC&t_click=%EC%B9%B4%ED%85%8C%EA%B3%A0%EB%A6%AC%ED%83%AD_%EB%8C%80%EC%B9%B4%ED%85%8C%EA%B3%A0%EB%A6%AC&t_1st_category_type=%EB%8C%80_%EC%8A%A4%ED%82%A8%EC%BC%80%EC%96%B4"

driver.get(base_url)
WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.ct-menu > ul.list > li"))
)

columns = [
    "category", "brand", "product_name",
    "origin_price", "sale_price", "usage", "ingredient", "reviews"
]
df = pd.DataFrame(columns=columns)

try:
    # 카테고리 목록 파악
    cats = WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.ct-menu > ul.list > li"))
    )
    total_cats = len(cats)
    print("카테고리 수:", total_cats)
    
    for cat_idx in range(total_cats):
        driver.get(base_url)
        cats = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.ct-menu > ul.list > li"))
        )
        tab = cats[cat_idx].find_element(By.TAG_NAME, "span")
        category_name = tab.text
        driver.execute_script("arguments[0].click();", tab)
        # 카테고리 탭 클릭 후 상품 리스트 로딩 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.prd_name > a"))
        )

        current_group = 1  # 페이지 그룹 추적 변수

        while True:  # 페이지 그룹 루프 (1~10, 11~20 ...)
            try:
                page_links = driver.find_elements(By.CSS_SELECTOR, "div.pageing a:not(.prev):not(.next)")
                strong_links = driver.find_elements(By.CSS_SELECTOR, "div.pageing strong")
                group_pages = [elem.text for elem in strong_links if elem.text.isdigit()] + \
                              [elem.text for elem in page_links if elem.text.isdigit()]
                group_pages = sorted(set(group_pages), key=lambda x: int(x))
                print(f"  - {current_group}그룹 페이지: {', '.join(group_pages)}")
            except TimeoutException:
                print("    ➤ 페이지 번호 요소를 찾을 수 없음")
                break

            for i, page_num in enumerate(group_pages):
                if i != 0:
                    page_btn = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, f"//div[@class='pageing']//a[text()='{page_num}']"))
                    )
                    driver.execute_script("arguments[0].click();", page_btn)
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.prd_name > a"))
                    )

                try:
                    product_links = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.prd_name > a"))
                    )
                    print(f"    - {page_num}페이지 상품 수: {len(product_links)}")

                    for idx, link in enumerate(product_links, 1):
                        try:
                            product_url = link.get_attribute("href")
                            driver.execute_script(f"window.open('{product_url}');")
                            driver.switch_to.window(driver.window_handles[1])
                            # 상세 페이지의 브랜드 요소 등장 대기
                            WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "#moveBrandShop"))
                            )

                            brand = driver.find_element(By.CSS_SELECTOR, "#moveBrandShop").text
                            product_name = driver.find_element(By.CSS_SELECTOR, ".prd_name").text
                            try:
                                origin_price = driver.find_element(By.TAG_NAME, "strike").text
                            except NoSuchElementException:
                                origin_price = ""
                            try:
                                sale_price = driver.find_element(By.CSS_SELECTOR, ".price-2 strong").text
                            except NoSuchElementException:
                                sale_price = ""

                            # 사용법·성분 탭 클릭
                            try:
                                buyinfo_tab = WebDriverWait(driver, 5).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, "li#buyInfo > a.goods_buyinfo"))
                                )
                                driver.execute_script("arguments[0].click();", buyinfo_tab)
                                WebDriverWait(driver, 5).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, "#artcInfo dl.detail_info_list"))
                                )
                            except:
                                pass
                            try:
                                info_list = driver.find_elements(By.CSS_SELECTOR, "#artcInfo dl.detail_info_list")
                            except NoSuchElementException:
                                info_list = ""
                            try:
                                usage = info_list[4].find_element(By.TAG_NAME, "dd").text if len(info_list) > 4 else ""
                            except NoSuchElementException:
                                usage = ""
                            try:
                                ingredient = info_list[7].find_element(By.TAG_NAME, "dd").text if len(info_list) > 7 else ""
                            except NoSuchElementException:
                                ingredient = ""

                            # 리뷰 탭 → 도움순
                            try:
                                driver.find_element(By.CSS_SELECTOR, "#reviewInfo span").click()
                                WebDriverWait(driver, 5).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, "#gdasList > li"))
                                )
                                driver.find_element(By.CSS_SELECTOR, "#gdasSort li:nth-child(2)").click()
                                WebDriverWait(driver, 5).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, "#gdasList > li"))
                                )
                            except:
                                pass

                            reviews = []
                            for page in range(1, 11):
                                try:
                                    items = driver.find_elements(By.CSS_SELECTOR, "#gdasList > li")
                                    for idx in range(len(items)):
                                        try:
                                            item = driver.find_elements(By.CSS_SELECTOR, "#gdasList > li")[idx]
                                            reviews.append(item.find_element(By.CSS_SELECTOR, ".txt_inner").text)
                                        except (NoSuchElementException, StaleElementReferenceException):
                                            continue
                                except Exception as e:
                                    print(f"리뷰 추출 중 에러: {e}")

                                # 다음 리뷰 페이지 이동
                                try:
                                    # 다음 페이지 버튼이 "클릭 가능"할 때까지 wait
                                    nxt = WebDriverWait(driver, 10).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, f".pageing a[data-page-no='{page+1}']"))
                                    )
                                    nxt.click()
                                    # 클릭 후, 리뷰 리스트가 나타날 때까지 wait
                                    WebDriverWait(driver, 5).until(
                                        EC.presence_of_element_located((By.CSS_SELECTOR, "#gdasList > li"))
                                    )
                                except (NoSuchElementException, TimeoutException):
                                    break
                                
                            # DataFrame에 저장
                            df.loc[len(df)] = [
                                category_name, brand, product_name,
                                origin_price, sale_price,
                                usage, ingredient,
                                reviews[:100]
                            ]
                            print(f"      ✅ 저장: {brand} - {product_name}")

                        except Exception as e:
                            print(f"      ❌ 상품 실패: {str(e)}")
                            traceback.print_exc()
                        finally:
                            driver.close()
                            driver.switch_to.window(driver.window_handles[0])
                            # 탭 복귀 후 상품 목록 등장 대기
                            WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "div.prd_name > a"))
                            )

                except Exception as e:
                    print(f"    ❌ {page_num}페이지 처리 실패: {str(e)}")
                    traceback.print_exc()
                    continue

            # 다음 그룹 버튼 확인
            try:
                next_group_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, f"a.next[data-page-no='{(current_group)*10 + 1}']")
                    )
                )
                driver.execute_script("arguments[0].click();", next_group_btn)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.prd_name > a"))
                )
                current_group += 1
            except (NoSuchElementException, TimeoutException):
                print("    ➤ 마지막 페이지 그룹 도달")
                break

except Exception as fatal:
    print("💥 치명적 오류 발생, 즉시 저장 후 종료합니다:")
    traceback.print_exc()

finally:
    print("\n▶ 크롤링 종료 - 지금까지 수집된 데이터를 저장합니다.")
    driver.quit()
    df.to_csv("oliveyoung_products_partial.csv", index=False)
    print("▶ 저장 완료: 'oliveyoung_products_partial.csv'")
