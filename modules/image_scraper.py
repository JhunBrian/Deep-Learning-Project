from selenium import webdriver
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent.futures
from PIL import Image
import numpy as np
from io import BytesIO

class ImageScraper:
    def __init__(self, driver_path:str, query:str, max_links_to_fetch:int):
        self.driver_path = driver_path
        self.query = query
        self.max_links_to_fetch = max_links_to_fetch
        self.wd = webdriver.Chrome(executable_path=self.driver_path)

    def fetch_image_urls(self, sleep_between_interactions:int=1):
        """
        Reference: Fabian Bosler
        URL: https://towardsdatascience.com/image-scraping-with-python-a96feda8af2d
        """

        def scroll_to_end(wd):
            wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(sleep_between_interactions)    

        # build the google query
        search_url = "https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={q}&oq={q}&gs_l=img"

        # load the page
        self.wd.get(search_url.format(q=self.query))

        image_urls = set()
        image_count = 0
        results_start = 0
        while image_count < self.max_links_to_fetch:
            scroll_to_end(self.wd)

            # get all image thumbnail results
            thumbnail_results = self.wd.find_elements("css selector", "img.Q4LuWd")
            number_results = len(thumbnail_results)

            print(f"Found: {number_results} search results. Extracting links from {results_start}:{number_results}")

            for img in thumbnail_results[results_start:number_results]:
                # try to click every thumbnail such that we can get the real image behind it
                try:
                    img.click()
                    time.sleep(sleep_between_interactions)
                except Exception:
                    continue

                # extract image urls    
                actual_images = self.wd.find_elements("css selector", 'img.n3VNCb')
                for actual_image in actual_images:
                    if actual_image.get_attribute('src') and 'http' in actual_image.get_attribute('src'):
                        image_urls.add(actual_image.get_attribute('src'))

                image_count = len(image_urls)

                if len(image_urls) >= self.max_links_to_fetch:
                    print(f"Found: {len(image_urls)} image links, done!")
                    break
            else:
                print("Found:", len(image_urls), "image links, looking for more ...")
                time.sleep(30)
                return
                load_more_button = self.wd.find_elements("css selector", ".mye4qd")
                if load_more_button:
                    self.wd.execute_script("document.querySelector('.mye4qd').click();")

            # move the result startpoint further down
            results_start = len(thumbnail_results)

        return image_urls
    
    def fetch_image_array(self):
        fetch = self.fetch_image_urls()

        def fetch_image(url):
            try:
                resp = requests.get(url)
                imge = Image.open(BytesIO(resp.content))
                imge = np.asarray(imge)
                return imge

            except:
                print("Unable to open the image.")
                pass

        url_list = list(fetch)
        image_array = []
        executor = ThreadPoolExecutor(max_workers=5)
        
        print('-'*55)
        print(f"Accessing {self.query} URLs to fetch images")
        futures = [executor.submit(fetch_image, url) for url in url_list]
        for future in concurrent.futures.as_completed(futures, timeout=60):
            array = future.result()
            if type(array) == np.ndarray:
                image_array.append(array)
            else:
                pass

        executor.shutdown()
        print(f"Extracted {len(image_array)} images out of {self.max_links_to_fetch}\n{'='*55}")
        return image_array