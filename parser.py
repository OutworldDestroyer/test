from lxml import html
import re 
import json
import os 
import requests

new_data = {}
new_ads = []

XPATHES = {"title":'//div[@id="content-container-root"]/div[2]/div[1]/div/h1'
	,"price":'//div[@id="content-container-root"]/div[2]/div[2]/div[2]/div[1]/div[1]/div[1]/div[1]/h2',
	"mileage":'//div[@class="itemval"][contains(text(),"km")]',
	"color":'//div[@class="sc-font-bold"][contains(text(),"Farbe")]/following-sibling::div',
	"power":'//div[@class="sc-font-bold"][contains(text(),"Leistung")]/following-sibling::div'}

URL_PART= "https://www.truckscout24.de/transporter/gebraucht/kuehl-iso-frischdienst/renault?currentpage=" #link without page number

CURRENT_DIR  = os.getcwd()
DATA_DIR = os.path.join(CURRENT_DIR,"data")
JSON_DIR = os.path.join(DATA_DIR,"data.json")
	

def process(ad):
	ad["price"] = re.sub(r'[^0-9]+', "", ad["price"]) #data processing
	if ad["price"]:
		ad["price"] = int(ad["price"].strip(',-'))
	else:
		ad["price"] = 0
	if ad["mileage"] != 0:
		ad["mileage"] = re.sub(r'[^0-9.]+', "" ,ad["mileage"])
		ad["mileage"] = int(float(ad["mileage"].strip()))
	if ad["power"] != 0:
		ad["power"] = int(ad["power"][:ad["power"].find('k')].strip())


def get_by_xpath(tree,name,xpath,ad): #return the text of the element by xpath
 	try:
 		elem= tree.xpath(xpath)[0].text_content()
 	except IndexError:
 		if isinstance(ad[name], str):
 			return ""
 		return 0
 	return elem

def get_description(tree):
	description = ""
	label =  tree.xpath('//label[@for="moredata"]')[0]
	description += label.text_content() + " "
	description_elements = tree.xpath('//div[@data-type="description"]')
	for paragraph in description_elements: 
		description += paragraph.text_content()
	replace_dict = {'\xa0\n':' ','\u00a0\r\n':' ','\r\n':''} #data processing
	for k,v in replace_dict.items():
		description = description.replace(k,v)
	description = description.removesuffix('\xa0')
	return description

def download_images(tree,ad):
	image_dir = os.path.join(DATA_DIR,str(ad["id"]))
	if not os.path.exists(image_dir):
		os.mkdir(image_dir)
		images = []
		for i in range(1,4): #get src of first 3 images
			images.append(tree.xpath(f'//*[@id="detpics"]/as24-pictures/div/div[2]/div/as24-carousel[1]/div[1]/div[{i}]/div/img/@data-src'))
		num = 1
		for image in images:  # download images
			response = requests.get(image[0])
			if response.status_code == 200:
				with open(os.path.join(image_dir,"image"+str(num)+".jpg"), 'wb') as f:
					f.write(response.content)
			num += 1

def dump_data():
	new_data["ads"] = new_ads
	if os.path.exists(JSON_DIR):
		with open(JSON_DIR,"r",encoding="utf-8") as file:
			data = json.load(file)
			data.update(new_data)
		with open(JSON_DIR,"w",encoding="utf-8") as file:
			json.dump(data,file)
	else:
		with open(JSON_DIR,"w",encoding="utf-8") as file:
			json.dump(new_data,file)

def main(start_page=1,end_page=4):
	if not os.path.exists(DATA_DIR):
		os.mkdir(DATA_DIR)
	for i in range (start_page,end_page+1):
		ad = {"id":i,"href":"","title":"","price":0,"mileage":0,"color":"","power":0,"description":""} #empty initial ad
		response = requests.get(URL_PART+str(i),stream=True)  #get link + page number
		response.raw.decode_content = True
		tree = html.parse(response.raw)
		item = tree.xpath('//a[@data-item-name="detail-page-link"]')[0] #find first ad on the page
		href = 'https://www.truckscout24.de' + item.get('href')
		response = requests.get(href,stream=True) #get first ad
		response.raw.decode_content = True
		tree = html.parse(response.raw)
		ad["href"] = href
		ad["description"] = get_description(tree)
		for name,xpath in XPATHES.items():
			ad[name] = get_by_xpath(tree,name,xpath,ad)
		process(ad)
		download_images(tree,ad)
		new_ads.append(ad)
	dump_data()

if __name__ == '__main__':
	main()
