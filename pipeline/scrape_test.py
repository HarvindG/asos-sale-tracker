from os import environ
import re
import json

from dotenv import load_dotenv

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
import requests


from extract import get_domain_name

PRODUCT_URL = "https://www.asos.com/adidas-originals/adidas-originals-handball-spezial-trainers-in-black-with-gum-sole/prd/201264723?ctaref=more+colours+swatches&featureref1=more+colours+swatches"

PRICE_REGEX = "[^£]*$"


def scrape_data(url: str, options: Options) -> dict:
    """Scrapes data from an ASOS product url."""

    product_data = dict()

    driver = webdriver.Chrome(options=options)

    driver.get(url)

    metadata = driver.find_element(
        by=By.XPATH, value='//*[@id="split-structured-data"]')
    metadata = metadata.get_attribute('innerHTML')
    metadata = json.loads(metadata)

    header = {
        'user-agent': environ["USER_AGENT"]
    }

    image = metadata.get('image')
    name = metadata.get('name')

    product_data['url'] = url

    if name:
        product_data['name'] = name
    else:
        name = get_name(url, header)
        product_data['name'] = name['name']

    if image:
        product_data['image'] = image
    else:

        image = get_image(url, header)

        product_data['image'] = image["image"]

    price = driver.find_element(
        By.XPATH, '//*[@id="pdp-react-critical-app"]/span[2]/div[1]/span[2]')
    price = re.findall(PRICE_REGEX, price.text)[0]
    product_data['price'] = round(float(price), 2)

    try:
        sizes = driver.find_element(by=By.ID, value="variantSelector")
        size_list = sizes.text.splitlines()[1:]
        # size_list = [size.replace(" - Out of stock", "") for size in size_list]
        if size_list:
            product_data['sizes'] = size_list
        else:
            product_data['sizes'] = "One Size"

    except NoSuchElementException:
        product_data['sizes'] = "One Size"

    try:
        driver.find_element(by=By.XPATH, value='//*[@id="jwe_q"]')
        product_data['availability'] = False
    except NoSuchElementException:
        product_data['availability'] = True

    domain_name = get_domain_name(url)

    product_data["website_name"] = domain_name

    driver.close()

    return product_data


def get_image(url, header):

    page = requests.get(url, headers=header, timeout=5)
    soup = BeautifulSoup(page.text, "html.parser").find(
        "script", type="application/ld+json")

    product_data = json.loads(soup.string)
    wanted_prod_data = {}

    if "image" in product_data.keys():
        wanted_prod_data["image"] = product_data["image"]
    else:
        wanted_prod_data["image"] = product_data['@graph'][0]["image"]

    return wanted_prod_data


def get_name(url, header):
    page = requests.get(url, headers=header, timeout=5)
    soup = BeautifulSoup(page.text, "html.parser").find(
        "script", type="application/ld+json")

    product_data = json.loads(soup.string)
    wanted_prod_data = {}

    if "name" in product_data.keys():
        wanted_prod_data["name"] = product_data["name"]
    else:
        wanted_prod_data["name"] = product_data['@graph'][0]["name"]

    return wanted_prod_data


if __name__ == "__main__":

    load_dotenv()

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument(f'user-agent={environ["USER_AGENT"]}')

    print(scrape_data(PRODUCT_URL, chrome_options))
