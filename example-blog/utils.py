import os
import json
import asyncio
import requests
from bs4 import BeautifulSoup
import requests

from crawl4ai import AsyncWebCrawler
from config import MILELION_SITEMAP_URL, OPENAI_API_KEY

assert OPENAI_API_KEY, "Please set the OPENAI_API_KEY environment variable"

def get_urls_from_sitemap(url) -> list:
    print("Getting Sitemap for " + url)
    #Send our GET requests and parse the response with BS4
    try:
        r = requests.get(url)
    except requests.exceptions.RequestException:
        return([])
    soup = BeautifulSoup(r.text, 'xml')
    #Set up list for all links
    website_links = []
    #Find all <loc> tags that have a .xml extension
    for item in soup.find_all('loc'):
        try:
            if '.xml' in item.text:
                #Send another GET request to the .xml link
                r = requests.get(item.text)
                new_soup = BeautifulSoup(r.text, 'xml')
                for new_item in new_soup.find_all('loc'):
                    website_links.append(new_item.text)
            #If the link doesn't have a .xml extension, add it to the list
            else:
                website_links.append(item.text)
        except TypeError:
            pass
    print("Found " + str(len(website_links)) + " links")
    return(website_links)

# def generate_milelion_urls(years: list[int], months: list[int]):
#     return [f"{MILELION_SITEMAP_URL}{year}/{month}" for year in years for month in months]

def get_milelion_urls():
    urls = get_urls_from_sitemap(MILELION_SITEMAP_URL)
    return urls

async def extract_milelion(urls: list[str], extraction_strategy=None, out_dir=None):
    async with AsyncWebCrawler(verbose=True) as crawler:
        tasks = [crawler.arun(
            url=url,
            word_count_threshold=1,
            extraction_strategy=extraction_strategy,
            bypass_cache=True
        ) for url in urls]
        results = await asyncio.gather(*tasks)

    for i, result in enumerate(results):
        if result.success:
            content = json.loads(result.extracted_content)
            filename = f"{out_dir}/{result.url.replace('https://milelion.com/', '').replace('/', '_')}.json"
            os.makedirs(out_dir, exist_ok=True)
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2)

            print(f"Extracted {len(content)} items from {result.url}")
        else:
            print(f"Failed to extract from {result.url}. Error: {result.error_message}")

# urls = get_urls_from_sitemap("https://milelion.com/post-sitemap1.xml")
# asyncio.run(extract_milelion(urls))
