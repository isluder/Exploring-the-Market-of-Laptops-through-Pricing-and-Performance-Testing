'''MIT License

Copyright (c) 2023 Yafeth Tandi Bendon

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.'''

# NOTES:
# Note this python script was adapted from the github repository of https://github.com/yafethtb/Geekbench-Web-Scraping-Project.git
# This script only contains the functions that will be used for scraping Geekbench

import numpy as np
import pandas as pd
import re
from time import sleep
from random import uniform

import requests
from bs4 import BeautifulSoup


# This function parses url_list and collects all pages for each CPU
def find_max_page(url_list):
    pages = []

    # Check pages
    for url in url_list:
        sleep(uniform(1.5, 2.5))
        html_page = requests.get(url).content
        soup = BeautifulSoup(html_page, 'html.parser')
        # check if the page have contents  
        if soup.find('div', class_= 'col-12 list-col') is None:
            pages.append(0)
            print(f"{url} has no matches")
        else:
            # check if the page is single or mutiple
            if soup.find('a', class_= 'page-link') is None:
                pages.append(1)
                print(f"{url} has 1 page")
            else:
                nav_page = int([nav.text for nav in soup.find_all('a', class_= 'page-link')][-2])
                pages.append(nav_page)
                print(f"{url} has {nav_page} pages")
    url_dict = {}
    # url_dict = {url : page for url, page in zip(url_list, pages)}
    for url, page in zip(url_list, pages):
            url_dict[url] = page
    return url_dict

def ryzen_geekbench_url_pages(url_dict):
    '''A function to create all URL pages for each URL in dataframe.
    The result will be another list that can be use directly for scraping.'''
    # Declaring URL container
    url_list = []
    url_dict_4_tracking = {}  
    
    # Using for loop on the dictionary...
    for url in url_dict:
        url_dict_4_tracking[url] = []
        # ... we change the URL based on observed pattern in GeekBench website...
        change_url = re.sub(r'search\?', '{}', url)

        # ... And insert new pattern.
        for num in range(1, url_dict[url] + 1):
            # num represent all page numbers of each respected URL.
            # ryzen_dict[url], or 'Pages' column in dataframe, is the latest page of each respected URL.
            add_url = f'search?page={num}&'
            # We use curly bracket to URL. Using .format() make it possible to insert strings into the URL. 
            new_url = change_url.format(add_url)
            url_list.append(new_url)
            url_dict_4_tracking[url].append(new_url)
    
    return url_list, url_dict_4_tracking


def scraping_function(url_dict_4_tracking):
    '''Scraping all URL pages in the URL list.
    The result will be a list consist of the content of Response objects.'''
    scrape_result = {}
    for i, main_url in enumerate(url_dict_4_tracking):
        scrape_result[main_url] = []
        for url in url_dict_4_tracking[main_url]:
            sleep(uniform(1.5, 2.5))
            scrape = requests.get(url).content
            scrape_result[main_url].append(scrape)
        print(f"{main_url} success {i}, out of {len(url_dict_4_tracking)}. {i/len(url_dict_4_tracking)*100} % Complete")
    return scrape_result

def page_extractor(scrape_result):
    '''A function to parsing a scraped result'''

    quarry = []
    cpu_name =[]
    time = []
    platform = []
    single_core = []
    multi_core = []
    for main_url in scrape_result:
        scrape_list = scrape_result[main_url]
        for scraped in scrape_list:
            soup = BeautifulSoup(scraped, 'html.parser')
            
            # CPU Name data  
            cpu_data = [cpu.find('span', class_= 'list-col-model')
                            .text.strip().replace('\n', ' ') 
                            for cpu in 
                            soup.find_all('div', class_= 'col-12 col-lg-4')]

            cpu_name += cpu_data  
        
            # # Date/Time data                                          # @isluder removed time due to error, datetimes were not being returned, so time was an empty list
            # datetimes = [date_time.text 
            #                  for date_time 
            #                  in soup.find_all('span', class_= 'timestamp-to-local-short')]

            # time += datetimes

            # OS Name data
            platform_name = [platform.text.strip().replace('\n', ' ') 
                                for platform 
                                in soup.find_all('span', class_= 'list-col-text')]

            platforms = [platform_name[n] for n in range(0, len(platform_name)) if n % 2 == 1]

            platform += platforms
      
            # Benchmark data
            # Both single core and multi core data using the same tag
            # Thus, when scraping the tag, both values are extracted with pattern:
            # [single-core, multi-core, single-core, multi-core,... etc]
            core_score = soup.find_all('span', class_= 'list-col-text-score')
        
            # Single-core benchmark data
            # All single-core data are in even python index ([0, 2, 4, 6, ...])
            single_core_data = [core_score[n].text.strip() 
                                    for n in range(0, len(core_score)) if n % 2 == 0]
            
            single_core += single_core_data

            # Multi-core benchmark data
            # ALl multi-core data are in odd python index ([1, 3, 5, 7, ...])
            multi_core_data = [core_score[n].text.strip() 
                        for n in range(0, len(core_score)) if n % 2 == 1]
            
            multi_core += multi_core_data
            
            quarry += [main_url for _ in range(len(multi_core_data))]

    # Create dataframe:
    data_lib = {                
                'CPU Name'         : cpu_name,
                # 'Upload Date'      : time,                        # @isluder removed time due to error
                'Platform Name'    : platform,
                'Single-core Score': single_core,
                'Multi-core Score' : multi_core,
                'quarry'           : quarry
                }
    
    print(len(data_lib))
    print(len(cpu_name))
    print(len(single_core))
    print(len(multi_core))
    print(len(quarry))
    geekbench_data = pd.DataFrame(data_lib).drop_duplicates()
    
    # Assuring that each columns in dataframe are in correct dtypes:
    newtype = {
        'CPU Name': 'string',
        # 'Upload Date': 'datetime64',                              # @isluder removed time due to error
        'Platform Name': 'string',
        'Single-core Score': 'int',
        'Multi-core Score': 'int',
        'quarry': 'string'
    }
    
    geekbench_data = geekbench_data.astype(newtype)
    return geekbench_data


if __name__ == "__main__":
    df = pd.read_csv('laptops.csv')

    full_quarry = []

    for model in df['Model']:
        details = model.split(" ")
        brand = details[0]
        count = 0
        for det in details:
        
            if det.startswith("("):
                st_placement = count
            if det.endswith("/"):
                et_placement = count
                break
            if det == 'Laptop':
                Lp_placement = count
            count += 1

        if brand == 'Apple':
            quarry = []
            quarry.append(brand)
            for det in details[1:Lp_placement]:
                if det == 'MGND3HN':
                    pass
                else:
                    quarry.append(det)
            for det in details[st_placement:et_placement+1]:
                quarry.append(det.strip("()/"))
            name = ""
            for det in quarry:
                name += str(det) + " "
            
            full_quarry.append(name)
        else:
            quarry = []
            quarry.append(brand)
            for det in details[st_placement:et_placement+1]:
                quarry.append(det.strip("()/"))
            
            name =""
            for det in quarry:
                name += str(det) + " "
            
            full_quarry.append(name)
            
    print(f"Quarry Finish: \n{quarry[0:4]}")
    
    df['quarry'] = full_quarry

    URL_NAME = 'https://browser.geekbench.com/search?q='

    all_url = [URL_NAME+(re.sub('\s', '+', element))  for element in df['quarry']]
    df['urls_quarry'] = all_url

    url_quarry_num = len(set(df['urls_quarry']))
    print(f'Running -find_max_page- on {url_quarry_num}')
    num_url_dict = find_max_page(set(df['urls_quarry']))
    
    pages = []
    for url in df['urls_quarry']:
        try:
            pages.append(num_url_dict[url])
        except:
            print('Does not exist')
    df['num_pages'] = pages
    
    count = 0
    for num in df['num_pages']:
        if num > 0:
            count +=1
            
    print(f"This scraping method accounts for {count} of {len(df['num_pages'])} \nlaptops yielding {(count/len(df['num_pages']))*100:.3f}% scraping success. ")

    urls_to_scrape = {}
    for url, num in zip(num_url_dict.keys(), num_url_dict.values()):
        if num > 0:
            urls_to_scrape[url] = num
    print(f"There are {len(urls_to_scrape)} urls to be formatted for scraping.")
    
    url_list, url_dict_4_tracking = ryzen_geekbench_url_pages(urls_to_scrape)
    
    print(f"There are {len(url_list)} urls to scrap. \nthis will take around {len(url_list)*2.5/60} minutes to complete.")
    
    scrape_result = scraping_function(url_dict_4_tracking)
    print(f'Scraping Done')
    
    geekbench_data = page_extractor(scrape_result)
    
    geekbench_data.to_csv('geekbench_data_full_quarry.csv')
    
    df.to_csv('laptops_quarry_full_quarry.csv')