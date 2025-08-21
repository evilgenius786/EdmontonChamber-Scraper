import json
import logging
import time
from os import makedirs
from os.path import isfile
from random import shuffle

from bs4 import BeautifulSoup
from curl_cffi import requests
import pandas as pd
import glob
from threading import Thread, Semaphore

# import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
thread_count=10
semaphore = Semaphore(thread_count)
def process_company(company_url):
    file_name= './json_/'+company_url.split('/')[-1] + '.json'
    if isfile(file_name):
        logging.debug(f"File already exists: {file_name}, skipping processing.")
        return
    logging.info(f"Processing company: {company_url}")
    company_soup = get_soup(company_url)
    if not company_soup:
        logging.error(f"Failed to retrieve company page: {company_url}")
        return
    data={
        'url': company_url,
        'logo': company_soup.find('img', {'itemprop': 'logo'})['src'] if company_soup.find('img', {'itemprop': 'logo'}) else None,
        'name': company_soup.find('meta',{'itemprop':'name'}).get('content', '').strip() if company_soup.find('meta',{'itemprop':'name'}) else None,
        'streetAddress': company_soup.find('span', {'itemprop': 'streetAddress'}).text.strip() if company_soup.find('span', {'itemprop': 'streetAddress'}) else None,
        'addressLocality': company_soup.find('span', {'itemprop': 'addressLocality'}).text.strip() if company_soup.find('span', {'itemprop': 'addressLocality'}) else None,
        'addressRegion': company_soup.find('span', {'itemprop': 'addressRegion'}).text.strip() if company_soup.find('span', {'itemprop': 'addressRegion'}) else None,
        'postalCode': company_soup.find('span', {'itemprop': 'postalCode'}).text.strip() if company_soup.find('span', {'itemprop': 'postalCode'}) else None,
        'telephone': ', '.join([telephone.find('a')['href'].replace('tel:','') for telephone in company_soup.find_all('li', {'class': 'list-group-item gz-card-phone'})]),
        'faxNumber': ', '.join([fax.find('a')['href'].replace('tel:','') for fax in company_soup.find_all('li', {'class': 'list-group-item gz-card-fax'})]) if company_soup.find_all('li', {'class': 'list-group-item gz-card-fax'}) else None,
        'website': company_soup.find('li', {'class': 'list-group-item gz-card-website'}).find('a')['href'] if company_soup.find('li', {'class': 'list-group-item gz-card-website'}) else None,
        'linkedin': company_soup.find('a', {'class': 'gz-social-linkedin'})['href'] if company_soup.find('a', {'class': 'gz-social-linkedin'}) else None,
        'twitter': company_soup.find('a', {'class': 'gz-social-twitter'})['href'] if company_soup.find('a', {'class': 'gz-social-twitter'}) else None,
        'youtube': company_soup.find('a', {'class': 'gz-social-youtube'})['href'] if company_soup.find('a', {'class': 'gz-social-youtube'}) else None,
        'instagram': company_soup.find('a', {'class': 'gz-social-instagram'})['href'] if company_soup.find('a', {'class': 'gz-social-instagram'}) else None,
        'facebook': company_soup.find('a', {'class': 'gz-social-facebook'})['href'] if company_soup.find('a', {'class': 'gz-social-facebook'}) else None,
        'cat': ", ".join([cat.text.strip() for cat in company_soup.find_all('span', {'class': 'gz-cat'})]),
        'description': company_soup.find('div', {'itemprop': 'description'}).text.strip() if company_soup.find('div', {'itemprop': 'description'}) else None,
        'repname': company_soup.find('div', {'class': 'gz-member-repname gz-member-pointer'}).text.strip() if company_soup.find('div', {'class': 'gz-member-repname gz-member-pointer'}) else None,
        'reptitle': company_soup.find('div', {'class': 'gz-member-reptitle'}).text.strip() if company_soup.find('div', {'class': 'gz-member-reptitle'}) else None,
        'repphone': company_soup.find('span', {'class': 'gz-rep-phone-num'}).text.strip() if company_soup.find('span', {'class': 'gz-rep-phone-num'}) else None,
    }
    logging.info(json.dumps(data))
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def main():
    logo()
    makedirs('json_', exist_ok=True)
    logging.info("Starting to process listings...")
    threads = []
    alphabets = ['0-9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    shuffle(alphabets)
    for alpha in alphabets:
        logging.info(f"Processing listings for letter: {alpha}")
        listing_soup = get_soup(f'https://business.edmontonchamber.com/list/searchalpha/{alpha}')
        if not listing_soup:
            logging.error(f"Failed to retrieve listings for letter: {alpha}")
            continue
        for h5 in listing_soup.find_all('h5'):
            company_url = h5.find('a').get('href')
            if company_url:
                # process_company(company_url)
                thread  = Thread(target=process_company, args=(company_url,))
                thread.start()
                threads.append(thread)
        for thread in threads:
            thread.join()
        export_csv()
def export_csv():
    files = glob.glob('./json_/*.json')
    logging.info(f"Found {len(files)} JSON files to export to CSV.")
    if not files:
        logging.warning("No JSON files found to export.")
        return
    data = []
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            data.append(json.load(f))
    df = pd.DataFrame(data)
    df.to_csv('edmonton_chamber_of_commerce.csv', index=False, encoding='utf-8-sig')
    logging.info("CSV export completed: edmonton_chamber_of_commerce.csv")


def get_soup(url):
    return BeautifulSoup(get_request(url).text, 'html.parser')


def get_request(url):
    with semaphore:
        return requests.get(
            url=url,
            impersonate='chrome'
            )

def logo():
    print(rf"""
 _____      _                           _                   _____  _                        _                 
|  ___|    | |                         | |                 /  __ \| |                      | |                
| |__    __| | _ __ ___    ___   _ __  | |_   ___   _ __   | /  \/| |__    __ _  _ __ ___  | |__    ___  _ __ 
|  __|  / _` || '_ ` _ \  / _ \ | '_ \ | __| / _ \ | '_ \  | |    | '_ \  / _` || '_ ` _ \ | '_ \  / _ \| '__|
| |___ | (_| || | | | | || (_) || | | || |_ | (_) || | | | | \__/\| | | || (_| || | | | | || |_) ||  __/| |   
\____/  \__,_||_| |_| |_| \___/ |_| |_| \__| \___/ |_| |_|  \____/|_| |_| \__,_||_| |_| |_||_.__/  \___||_|   
===============================================================================================================
                            edmontonchamber.com - Edmonton Chamber of Commerce
                                scraper by github.com@evilgeniua786
===============================================================================================================
[+] JSON Based response
[+] CSV Export
[+] Data Scraped from https://business.edmontonchamber.com/list/searchalpha/
[+] Resumable
_______________________________________________________________________________________________________________
""")
    time.sleep(1)
if __name__ == '__main__':
    main()
