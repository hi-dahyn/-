from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import requests
import os
from PIL import Image
from io import BytesIO

SUCCESS_TARGET = 5000  
MAX_SCROLLS = 500

def selenium_scroll_option(driver):
    SCROLL_PAUSE_SEC = 5  
    scroll_count = 0
    
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while scroll_count < MAX_SCROLLS:

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_SEC)
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        if new_height == last_height:
            try:
                more_button = driver.find_element('xpath', "//input[@value='더보기']")
                if more_button:
                    more_button.click()
                    time.sleep(SCROLL_PAUSE_SEC)
            except Exception as e:
                print(f"Could not click 'Load more' button: {e}")
                break  
        last_height = new_height
        scroll_count += 1

def save_image(image_url, idx, success_counter):
    retry_count = 3 
    for _ in range(retry_count):
        try:
            response = requests.get(image_url)
            if response.status_code == 200:
                try:
                    image = Image.open(BytesIO(response.content))
                    if image.width >= 100 and image.height >= 100:
                        file_ext = image_url.split('.')[-1].split('?')[0]
                        if file_ext.lower() not in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
                            file_ext = 'jpg'  

                        image_path = f'images/image_{idx}.{file_ext}'
                        with open(image_path, 'wb') as file:
                            file.write(response.content)
                        success_counter.append(1)
                        print(f"Successfully saved {len(success_counter)} images.")
                        return
                    else:
                        print(f"Image {image_url} is smaller than 100x100.")
                except Exception as e:
                    print(f"Failed to open image {image_url}: {e}")
                    continue
            else:
                print(f"Failed to download image {image_url}: status code {response.status_code}")
        except Exception as e:
            print(f"Failed to save image {image_url}: {e}")

def google_image_search(query):
    options = Options()
    options.add_argument('--headless') 
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    search_url = f"https://www.google.com/search?tbm=isch&q={query}"
    driver.get(search_url)
    
    if not os.path.exists('images'):
        os.makedirs('images')
    
    success_counter = []
    idx = 1

    while len(success_counter) < SUCCESS_TARGET:
        selenium_scroll_option(driver)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        for img in soup.select('img'):
            src = img.get('src')
            data_src = img.get('data-src')
            image_url = src if src and src.startswith('http') else data_src
            if image_url and image_url.startswith('http'):
                save_image(image_url, idx, success_counter)
                idx += 1
                if len(success_counter) >= SUCCESS_TARGET:
                    break

    driver.quit()

query = 'face'
google_image_search(query)
