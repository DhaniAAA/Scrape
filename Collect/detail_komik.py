import requests
from bs4 import BeautifulSoup
import json
import time

def scrape_komikcast():
    """
    This function scrapes a list of comics from all available pages,
    extracts the title, link, image, latest chapter, and rating,
    and then saves the data to a JSON file.
    """
    # Base URL pattern with a placeholder for the page number
    base_url_pattern = "https://komikcast03.com/daftar-komik/page/{}/?status&type=manhwa&orderby=popular"

    # Headers to mimic a browser to avoid being blocked
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # List to hold all comic data from all pages
    all_data = []
    page_number = 1

    # --- PAGE LIMIT ---
    # Change the value of this variable to limit the number of pages to scrape.
    # For example, max_pages = 5 will fetch data from pages 1 to 5.
    max_pages = 5

    # The loop will continue as long as it finds comic data on the page
    while True:
        # Stop the loop if the maximum page limit is reached
        if page_number > max_pages:
            print(f"Reached the maximum limit of {max_pages} pages. Scraping process stopped.")
            break

        # Form the complete URL with the page number using the new pattern
        current_url = base_url_pattern.format(page_number)
        print(f"Scraping data from page: {page_number} -> {current_url}")

        try:
            # Send a GET request to the URL
            response = requests.get(current_url, headers=headers)
            response.raise_for_status()

            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all div elements with the class 'list-update_item'
            komik_list = soup.find_all('div', class_='list-update_item')

            # If no more comic items are found on the page, stop the loop
            if not komik_list:
                print(f"No more data found on page {page_number}. Scraping process finished.")
                break

            # Iterate through each comic item found
            for komik in komik_list:
                try:
                    # Extract the comic URL
                    link_element = komik.find('a')
                    komik_url = link_element['href'] if link_element else 'N/A'

                    # Extract the comic title
                    title_element = komik.find('h3', class_='title')
                    title = title_element.get_text(strip=True) if title_element else 'N/A'

                    # Extract the cover image URL
                    image_element = komik.find('img', class_='ts-post-image')
                    image_url = image_element.get('src') or image_element.get('data-src') or 'N/A'

                    # # Extract the latest chapter
                    # chapter_element = komik.find('div', class_='chapter')
                    # latest_chapter = chapter_element.get_text(strip=True) if chapter_element else 'N/A'

                    # Extract the rating score
                    rating_element = komik.find('div', class_='numscore')
                    rating = rating_element.get_text(strip=True) if rating_element else 'N/A'

                    # Add the extracted data to the list
                    all_data.append({
                        'Title': title,
                        'Link': komik_url,
                        'Image': image_url,
                        # 'Latest Chapter': latest_chapter,
                        'Rating': rating
                    })

                except Exception as e:
                    print(f"Error while processing an item: {e}")

            # Move to the next page
            page_number += 1
            # Add a short delay between requests to avoid overloading the server
            time.sleep(1)

        except requests.exceptions.RequestException as e:
            print(f"Failed to retrieve web page {page_number}. Error: {e}")
            break # Stop if a connection error occurs
        except Exception as e:
            print(f"An error occurred: {e}")
            break

    # Remove duplicates by converting to a set of tuples and back to a list of dicts
    # Dictionaries are not hashable, so convert to tuples of key-value pairs
    unique_data = []
    seen = set()
    for item in all_data:
        # Create a hashable representation of the dictionary
        item_tuple = tuple(sorted(item.items()))
        if item_tuple not in seen:
            seen.add(item_tuple)
            unique_data.append(item)


    # Save all the collected data to a JSON file
    if unique_data:
        output_file = 'komikcast_scrape_results.json'
        print(f"\nSaving a total of {len(unique_data)} unique items to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(unique_data, file, ensure_ascii=False, indent=4)
        print("Save successful!")
    else:
        print("No unique data was successfully scraped.")

    # Print the first few results for verification
    print("\nSample of scraped results:")
    for item in unique_data[:5]:
        print(item)


if __name__ == "__main__":
    # Make sure you have the required libraries installed:
    # pip install requests beautifulsoup4
    scrape_komikcast()