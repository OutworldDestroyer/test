from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
import re 
import json
import os 
import requests

data = {}
new_ads = []

xpathes = {"title":'//*[@id="content-container-root"]/div[2]/div[1]/div/h1'
	,"price":'//*[@id="content-container-root"]/div[2]/div[2]/div[2]/div[1]/div[1]/div[1]/div[1]/h2',
	"mileage":'//*[@class="itemval"][contains(text(),"km")]',
	"color":'//*[@class="sc-font-bold"][contains(text(),"Farbe")]/following-sibling::div',
	"power":'//*[@class="sc-font-bold"][contains(text(),"Leistung")]/following-sibling::div'}

url_part = "https://www.truckscout24.de/transporter/gebraucht/kuehl-iso-frischdienst/renault?currentpage="

current_dir  = os.getcwd()
data_dir = os.path.join(current_dir,"data")
json_dir = os.path.join(data_dir,"data.json")
	
options = Options()
options.add_argument("--headless")
options.add_argument('--ignore-certificate-errors')
	
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def process(ad):
	ad["price"] = re.sub(r'[^0-9]+', r"", ad["price"])
	ad["color"] = str(ad["color"])
	if ad["price"]:
		ad["price"] = int(ad["price"].strip(',-'))
	else:
		ad["price"] = 0
	if ad["mileage"] != 0:
		ad["mileage"] = re.sub(r'[^0-9.]+', r'',ad["mileage"])
		ad["mileage"] = int(float(ad["mileage"].strip()))
	if ad["power"] != 0:
		ad["power"] = int(ad["power"][:ad["power"].find('k')].strip())


def get_by_xpath(name,xpath,ad):
	try:
		elem=driver.find_element(By.XPATH,xpath).get_attribute('innerText')
	except NoSuchElementException:
		if isinstance(ad[name], str):
			return ""
		return 0
	return elem

def get_description():
	description = ""
	raw_description = driver.find_elements(By.CSS_SELECTOR,'[data-type="description"]')
	if raw_description:
		for paragraph in raw_description: #\xa0\n
			paragraph = paragraph.get_attribute("innerText")
			description += paragraph
	description = description.replace('\xa0\n', ' ')
	description = description.removesuffix('\xa0')
	return description

def download_images(ad):
	image_dir = os.path.join(data_dir,str(ad["id"]))
	if not os.path.exists(image_dir):
		os.mkdir(image_dir)
		images = []
		for i in range(1,4):
			images.append(driver.find_element(By.XPATH,f'//*[@id="detpics"]/as24-pictures/div/div[2]/div/as24-carousel[1]/div[1]/div[{i}]/div/img'))
		num = 1
		for image in images:
			image_src = image.get_attribute("data-src")
			response = requests.get(image_src)
			if response.status_code == 200:
				with open(os.path.join(image_dir,"image"+str(num)+".jpg"), 'wb') as f:
					f.write(response.content)
			num += 1

def dump_data():
	data["ads"] = new_ads
	if os.path.exists(json_dir):
		with open(json_dir,"r") as file:
			old_data = json.load(file)
			data.update(old_data)
	with open(json_dir,"w") as file:
		json.dump(data,file)


def main(start_page=1,end_page=4):
	if not os.path.exists(data_dir):
		os.mkdir(data_dir)
	count = 0
	for i in range (start_page,end_page+1):
		ad = {"id":i,"href":"","title":"","price":0,"mileage":0,"color":"","power":0,"description":""}
		driver.get(url_part+str(i))
		item = driver.find_element(By.XPATH,'//*[@class="ls-titles"]/a')
		href = item.get_attribute('href')
		driver.get(href)
		ad["href"] = href
		ad["description"] = get_description()
		download_images(ad)
		for name,xpath in xpathes.items():
			ad[name] = get_by_xpath(name,xpath,ad)
		count += 1
		process(ad)
		new_ads.append(ad)
	dump_data()
	driver.close()

if __name__ == '__main__':
	main()



