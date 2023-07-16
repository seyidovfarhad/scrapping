'''
Kod xəta versə yenidən cəhd edin
connectə və ya reklama görə xəta verə bilər
'''
import pandas as pd
import re
from bs4 import BeautifulSoup
import requests
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),options=options)
# sayta girib Nərimanov sözünü seçirik
url= requests.get('https://bina.az/')
soup_m=BeautifulSoup(url.content, 'html.parser')
for i in soup_m.find_all('div', 'footer__locations-list footer__locations-list--baku bz-d-grid')[0]:
  if i.get_text() == 'Nərimanov':
    link = 'https://bina.az/'+i.get('href')
    break
# ondan sonra yeni tikili üçün açılan list düyməsini basırıq
driver.get(link)
dropdwon_x_path = '//*[@id="new_q"]/div[1]/div[2]/div[1]/div[2]/span[2]'
dropdown = driver.find_element(By.XPATH, dropdwon_x_path)
dropdown.click()
time.sleep(5)
# həmin yeni tikilinin üstünə basırıq
variant_x_path = '//*[@id="new_q"]/div[1]/div[2]/div[1]/div[3]/div/ul/li[2]/span'

variant = WebDriverWait(driver, 20).until(EC.visibility_of_element_located(
        (By.XPATH,variant_x_path)))
variant.click()
time.sleep(5)
# basılmanın olub-olmadığını yoxlamaq üçün başlığa baxırıq
header_x_path = '//*[@id="js-search-results"]/div[1]'

print(driver.find_element(By.TAG_NAME, 'h1').get_attribute("innerText"))
# səhifədəki bütün elanların linklərini alırıq
urls = []
# Eyni zamanda elanın agentlik və ya agentlik olmağını təyin etmək üçün lazım olan obyekti alırıq
agency = []
# Burada cəmi 5 səhifədən linklər almışıq. Bunu daha çox çoxaltmaq olar
for n in range(5):
        item_list_x_path = '//*[@id="js-items-search"]/div[2]'
        item_list = driver.find_element(By.XPATH, item_list_x_path)
        for i in item_list.find_elements(By.TAG_NAME, 'div'):
                if i.get_attribute('data-item-id') != None:
                        urls.append('https://bina.az/items/' + i.get_attribute('data-item-id'))
        for t in item_list.find_elements(By.CSS_SELECTOR, 'div.preview'):
                if len(t.find_elements(By.CLASS_NAME, 'products-label')) != 0:
                        agency.append(t.find_elements(By.CLASS_NAME, 'products-label')[0].text)
                else:
                        agency.append('Yoxdur')
        # Hər səhifənin axırında növbəti düyməsini basırıq
        next = driver.find_element(By.XPATH, "//a[./text()='Növbəti']")
        next.click()
        time.sleep(5)
# linklər olan datanı yığırıq
links = pd.DataFrame([urls, agency])
links = links.T
# Hər yerdə olduğu kimi burada da komplekslərdən azad olmaq lazımdır çünki xəta verirlər
links = links[links[1] != 'Kompleks']
links = links.reset_index(drop=True)
# Datanın linklərini alıb əsas data yaratmaq
data = pd.DataFrame()
keys_list = []
values_list = []
for link in links[0]:
  url=requests.get(link)
  soup=BeautifulSoup(url.content, 'html.parser')
  keys = soup.find('div', 'product-properties__column').find_all('label')
  values = soup.find('div', 'product-properties__column').find_all('span')
  for key_value in range(len(keys)):
    keys_list.append(keys[key_value].get_text())
    values_list.append(values[key_value].get_text())
  price = soup.find('span', 'price-val').get_text()
  price = int(price.replace(' ', ''))
  unit = soup.find_all('div', 'product-price__i')[1].get_text()
  unit = re.findall(r'\d+', unit)
  unit = int(''.join(unit))
  keys_list.extend(['Price', 'Anz/kv.m'])
  values_list.extend([price, unit])
  exp_data = pd.DataFrame([values_list], columns = keys_list)
  data = pd.concat([data, exp_data])
  keys_list = []
  values_list = []
data = data.reset_index(drop=True)
# agentliyin birləşdirilməsi
data = pd.concat([data, links[1]], axis=1)

# Data preprocessing
data.rename(columns = {'Mərtəbə':'mertebe'}, inplace = True)
data['Mərtəbə'] = data['mertebe'].str.split(' ', expand = True)[0]
data['Mərtəbə_sayı'] = data['mertebe'].str.split(' ', expand = True)[2]
data.drop('mertebe', inplace = True, axis=1)
data.Sahə = data.Sahə.str.replace(' m²','')
data.drop(['Kateqoriya'], axis = 1, inplace = True)
data.rename(columns = {'Price':'Qiymət(azn)', 1:'Vasitəçi'}, inplace = True)
data.fillna('yoxdur', inplace = True)
data['Vasitəçi'].replace('Yoxdur', 'Digər', inplace = True)
# Digər olan yerlərdə də agentlik də ola bilər
data['Sahə'] = data['Sahə'].astype(float)
data[['Mərtəbə', 'Mərtəbə_sayı']] = data[['Mərtəbə', 'Mərtəbə_sayı']].astype(int)
# Excel formatında yaddaşda saxlayırıq
data.to_excel('Ev_qiymetleri.xlsx')
