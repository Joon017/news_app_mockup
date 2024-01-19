
import openai
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, urlencode  # Add 'urlencode' here
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

class GPTWebScraper:
    def __init__(self, openai_api_key):
        self.openai_api_key = openai_api_key

    def generate_response(self, text):
        openai.api_key = self.openai_api_key
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=text,
            max_tokens=150
        )
        return response['choices'][0]['text'].strip()

    def generate_google_news_link(self, query, page):
        base_url = "https://www.google.com/search"
        params = {
            "q": query,
            "tbm": "nws",  # Specify the 'news' tab
            "start": (page - 1) * 10
        }
        return f"{base_url}?{urlencode(params)}"

    def extract_article_link(self, html_element):
        soup = BeautifulSoup(html_element, 'html.parser')

        # Extract the link from the 'href' attribute in the 'a' tag
        link_element = soup.find('a', {'class': 'WlydOe'})
        if link_element and 'href' in link_element.attrs:
            link = link_element['href']

            # If the link is a relative path, make it an absolute URL
            parsed_link = urlparse(link)
            if not parsed_link.scheme:
                base_url = "https://www.google.com"  # You may need to change this base URL based on your needs
                link = urljoin(base_url, link)

            return link

        return None

    def scrape_google_news(self, query, num_pages=1):
        articles = []

        # Set up Selenium WebDriver
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run Chrome in headless mode (without GUI)
        driver = webdriver.Chrome(options=chrome_options)

        try:
            for page in range(1, num_pages + 1):
                url = self.generate_google_news_link(query, page)
                print(url)

                # Use Selenium to load the page with dynamic content
                driver.get(url)

                # Wait for a few seconds to allow dynamic content to load
                time.sleep(5)

                # Get the page source after dynamic content has loaded
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, "html.parser")

                # Extract article information using the updated selectors
                title_elements = soup.select('div.n0jPhd.ynAwRc.MBeuO.nDgy9d[role="heading"][aria-level="3"]')
                date_elements = soup.select('span.OSrXXb.rbYSKb.LfVVr')
                description_elements = soup.select('div.GI74Re.nDgy9d')
                link_elements = soup.select('a.WlydOe')

                for i, title_element in enumerate(title_elements):
                    title = title_element.get_text(strip=True) if title_element else "N/A"
                    date = date_elements[i].get_text(strip=True) if date_elements and len(date_elements) > i else "N/A"
                    description = description_elements[i].get_text(strip=True) if description_elements and len(description_elements) > i else "N/A"
                    link = self.extract_article_link(str(link_elements[i])) if link_elements and len(link_elements) > i else "N/A"

                    # Add the article to the list
                    articles.append({
                        "title": title,
                        "date": date,
                        "description": description,
                        "link": link
                    })

        finally:
            # Close the WebDriver
            driver.quit()

        return articles

if __name__ == "__main__":
    # Get OpenAI API key
    openai_api_key = "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"

    # Create a GPTWebScraper instance
    scraper = GPTWebScraper(openai_api_key)

    # Get user input for the search query
    search_query = input("Enter the search query: ")

    # Define the number of pages to scrape
    num_pages_to_scrape = 2

    # Scrape Google News
    result = scraper.scrape_google_news(search_query, num_pages_to_scrape)

    # Output the result
    for idx, article in enumerate(result, start=1):
        print(f"Article {idx}:\nTitle: {article['title']}\nDate: {article['date']}\nDescription: {article['description']}\nLink: {article['link']}\n")
