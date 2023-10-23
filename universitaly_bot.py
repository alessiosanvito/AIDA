import json
import os
import random
import re
import shutil
import requests
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType

class Browser:
    def __init__(self):
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--headless")  # Disattiva la visualizzazione GUI

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.get("https://www.universitaly.it/index.php/cercacorsi/universita")

    def get_element_attribute(self, xpath, attribute):
        return self.find_element(xpath).get_attribute(attribute)
    
    def close_tab(self):
        self.driver.close()

    def switch_to_new_tab(self):
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def switch_to_main_tab(self):
        self.driver.switch_to.window(self.driver.window_handles[0])

    def find_elements(self, xpath):
        return self.driver.find_elements(By.XPATH, xpath)

    def find_element(self, xpath):
        return self.driver.find_element(By.XPATH, xpath)

    def sleep(self, seconds):
        time.sleep(seconds)


class DirectoryManager:
        
    def create_directory(self, path_name):
        path = Path(path_name)
        path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def sanitize_directory_name(name):
        sanitized_name = re.sub(r'[<>:"/\\|?*]', '', name)
        return sanitized_name
    
    def file_exists(self, file_path):
        if os.path.exists(file_path):
            print("ALREADY DONE")
            return True
        else:
            return False
    
    def write_to_file(self, path, data):
        if os.path.exists(path):
            print("ALREADY DONE")
            return

        with open(path, "w") as file:
            file.write(data)
    
    def delete_folder_content(self, folder_path):
        try:
            # Check if the folder exists
            if os.path.exists(folder_path):
                # Delete all contents of the folder
                shutil.rmtree(folder_path)
                # Recreate an empty folder
                os.makedirs(folder_path)
                print(f"Successfully deleted the contents of {folder_path}.")
            else:
                print(f"The folder {folder_path} does not exist.")
        except Exception as e:
            print(f"An error occurred while deleting the contents of {folder_path}: {str(e)}")



class CourseInfoExtractor:
    def __init__(self, directory_manager, browser):
        self.directory_manager = directory_manager
        self.browser = browser

    def create_university_tree(self):
        self.directory_manager.create_directory("/universities")

        print("****Start Uni Dir Creation****")

        select_element = self.browser.find_element("/html/body/div[4]/div/div[2]/div[1]/form/div[2]/div[2]/fieldset/select[4]")
        options = select_element.find_elements(By.XPATH, "./option")
        for i in range(1, len(options)):
            option = options[i]
            university_name = option.text
            print(university_name)
            self.directory_manager.create_directory("./universities/"+self.directory_manager.sanitize_directory_name(university_name))

class CourseScraper:
    def __init__(self, directory_manager, browser):
        self.directory_manager = directory_manager
        self.browser = browser

    def scrape(self):
        print("****Start Uni Scraping****")

        main_path = self._get_main_path()

        select_element = self.browser.find_element(main_path+"/div/div[2]/div[1]/form/div[2]/div[2]/fieldset/select[4]")
        search = self.browser.find_element(main_path+"/div/div[2]/div[1]/form/p/input[1]")
        options = select_element.find_elements(By.XPATH, "./option")

        for i in range(1, len(options)):
            self._scrape_option(main_path, options[i], search)
            self._check_scraped_courses(main_path, options[i].text)

    def _get_main_path(self):
        self.browser.sleep(0.5)
        try:
            banner_button = self.browser.find_element("/html/body/div[1]/div/a[1]")
            banner_button.click()
            
            return "/html/body/div[3]"
        except:
            return "/html/body/div[4]"

    def _scrape_option(self, main_path, option, search):
        university_name = option.text
        print(university_name)

        option.click()
        search.click()

        self.browser.sleep(2)
        random_wait_time = random.uniform(2, 3)
        self.browser.sleep(random_wait_time)

        self._scrape_courses(main_path, university_name)

    def _scrape_courses(self, main_path, university_name):
        table_element = self.browser.find_element(main_path+"/div/div[2]/div[2]/div[2]/div/table")
        courses = table_element.find_elements(By.XPATH, "./tbody/tr")
        resume = self.browser.find_element(main_path+"/div/div[2]/div[2]/div[1]/div[1]/h3")
        resume.click()

        for i in range(1, len(courses)):
            self._scrape_course(main_path, courses[i], university_name)

    def _scrape_course(self, main_path, course, university_name):

        


        course_dict = self._extract_course_info(course)
        course_name = course_dict['name']
        sua_code = course_dict['sua_code']
        path = "./universities/"+self.directory_manager.sanitize_directory_name(university_name)+"/"+self.directory_manager.sanitize_directory_name(course_name)+"_"+sua_code


        print("-----"+course_name)

        if(self.directory_manager.file_exists(path+"/"+self.directory_manager.sanitize_directory_name(course_name)+"_"+sua_code+".pdf") and self.directory_manager.file_exists(path+"/metadata.txt")):
            return
        else:
            self.directory_manager.delete_folder_content(path)

        
        self.directory_manager.create_directory(path)

        course.find_element(By.XPATH, "./td[2]/a[1]").click()
        self.browser.switch_to_new_tab()

        self.browser.sleep(2)
        random_wait_time = random.uniform(3, 4)
        self.browser.sleep(random_wait_time)

        url_pdf = self.browser.get_element_attribute(main_path+"/div/div[2]/div[1]/div[4]/a", "href")
        print(url_pdf)
        self._download_pdf(url_pdf, path+"/"+self.directory_manager.sanitize_directory_name(course_name)+"_"+sua_code+".pdf")
        self.browser.sleep(1)
        print("------PDF OK")

        self.browser.close_tab()
        self.browser.switch_to_main_tab()

        self.directory_manager.write_to_file(path+"/metadata.txt", json.dumps(course_dict))

        self.browser.sleep(1)

    

    
    def _download_pdf(self, url, file_path):
        
        print("Download PDF")
        response = requests.get(url, stream=True)
        print("Download PDF done")

        try:
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
        except Exception as e:
            print("Errore durante il salvataggio del file:", str(e))
        
        response.close()

        del response
        print("connessione chiusa")


    def _extract_course_info(self, course):
        course_dict = {}

        title = course.find_element(By.XPATH, "./td[2]/strong")
        levels = course.find_element(By.XPATH, "./td[3]").find_elements(By.XPATH, "./span")
        cities = course.find_element(By.XPATH, "./td[2]")

        language_text = self._extract_language_text(course)
        access_text = self._extract_attribute_text(course, "./td[4]/img")
        test_access_text = self._extract_attribute_text(course, "./td[6]/img")
        mod_text = self._extract_attribute_text(course, "./td[7]/img")
        duration_text = self._extract_duration_text(course)
        degree_text = self._extract_degree_text(course)

        sua_window = course.find_element(By.XPATH, "./td[2]/a[1]")
        sua_href = sua_window.get_attribute("href")
        sua_code = re.sub(r".*/(\d+)$", r"\1", sua_href)

        course_dict["name"] = title.text
        course_dict["cds_codes"] = [level.text for level in levels]
        course_dict["cities"] = self._extract_cities_text(cities.text)
        course_dict["language"] = language_text
        course_dict["type_of_access"] = access_text
        course_dict["test_access"] = test_access_text
        course_dict["mod"] = mod_text
        course_dict["duration"] = duration_text
        course_dict["degree_type"] = degree_text
        course_dict["sua_code"] = sua_code

        return course_dict

    def _extract_language_text(self, course):
        try:
            language = course.find_element(By.XPATH, "./td[10]/img")
            return language.get_attribute("title")
        except:
            return "Corso in lingua italiana"

    def _extract_degree_text(self, course):
        try:
            degree = course.find_element(By.XPATH, "./td[9]/img")
            return degree.get_attribute("title")
        except:
            return "Corso a rilascio titolo singolo"

    def _extract_attribute_text(self, course, xpath):
        element = course.find_element(By.XPATH, xpath)
        return element.get_attribute("title")

    def _extract_duration_text(self, course):
        duration = course.find_element(By.XPATH, "./td[8]/img")
        duration_text = duration.get_attribute("src")
        match = re.search(r'anni(\d+).png', duration_text)
        if match:
            return match.group(1) + " anni"
        return ""

    def _extract_cities_text(self, cities_text):
        match = re.findall(r"(, ([^,\n\[\]]+))(?!\[)(?!.*\bInterateneo\b)", cities_text)
        citta = [m[1].strip() for m in match]
        return citta
    
    def _check_scraped_courses(self, main_path, university_name):
        resume_text = self.browser.find_element(main_path + "/div/div[2]/div[2]/div[1]/div[1]/div/p[1]").text
        match = re.search(r"Trovati (\d+) corsi", resume_text)
        expected = int(match.group(1)) if match else 0
        dire = f"./universities/{self.directory_manager.sanitize_directory_name(university_name)}"
        found = len([name for name in os.listdir(dire) if os.path.isdir(os.path.join(dire, name))])
        if found != expected:
            print(f"ERROR IN {university_name}")
            print(f"FOUND: {found}")
            print(f"EXPECTED: {expected}")
            input("Press Enter to continue...")


# Usage
directory_manager = DirectoryManager()
browser = Browser()
time.sleep(2)
course_info_extractor = CourseInfoExtractor(directory_manager, browser)
course_info_extractor.create_university_tree()
time.sleep(2)
course_extractor = CourseScraper(directory_manager, browser)
course_extractor.scrape()