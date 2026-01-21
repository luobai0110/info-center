import csv

import requests
from bs4 import BeautifulSoup

base_url = "https://www.nmc.cn/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
}


def get_province_list():
    weather_url = base_url + "publish/forecast.html"
    response = requests.get(weather_url, headers=headers)
    response.encoding = response.apparent_encoding
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        data = []
        el = soup.find('select', id="provinceList")
        options = el.find_all('option')

        for option in options:
            value = option.get('value')
            text = option.get_text()
            data.append([value, text])

        with open('province_list.csv', mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name'])
            writer.writerows(data)
    else:
        print(f"Request failed with status code: {response.status_code}")


if __name__ == "__main__":
    get_province_list()
