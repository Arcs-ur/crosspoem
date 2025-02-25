import requests
from bs4 import BeautifulSoup

poems = []

url_first_page = 'https://www.gushicimingju.com/gushi/gushisanbaishou/'
response_first = requests.get(url_first_page)
soup_first = BeautifulSoup(response_first.content, 'html.parser')

for content in soup_first.find_all('span', class_='content'):
    poems.append(content.get_text())

for page in range(2, 11):
    url = f'https://www.gushicimingju.com/gushi/gushisanbaishou/page{page}/'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    for content in soup.find_all('span', class_='content'):
        poems.append(content.get_text())

with open('poem.txt', 'w', encoding='utf-8') as file:
    for poem in poems:
        file.write(poem + '\n')