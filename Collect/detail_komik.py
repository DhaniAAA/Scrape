import requests
from bs4 import BeautifulSoup
import json
import time
import re

def scrape_komikcast():
    """
    This function scrapes a list of comics from all available pages,
    extracts the title, link, image, and type,
    and then saves the data to a JSON file.
    """
    # Base URL pattern with a placeholder for the page number
    # Change 'Manhwa' to 'Manga' or 'Manhua' as needed
    base_url_pattern = "https://komikindo.ch/daftar-manga/page/{}/?status=&type=Manhwa&format=&order=&title="

    # Default komik type from URL filter
    komik_type = "Manhwa"

    # Headers to mimic a browser to avoid being blocked
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # List to hold all comic data from all pages
    all_data = []
    seen_slugs = set()  # Track slugs to avoid duplicates
    page_number = 1

    # --- PAGE LIMIT ---
    # Set to None to scrape all pages, or a number to limit
    max_pages = None

    # The loop will continue as long as it finds comic data on the page
    while True:
        # Stop the loop if the maximum page limit is reached
        if max_pages and page_number > max_pages:
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

            # Find listupd > film-list (main manga list A-Z, NOT the sidebar!)
            listupd = soup.find('div', class_='listupd')
            if not listupd:
                print(f"No listupd found on page {page_number}. Scraping process finished.")
                break

            film_list = listupd.find('div', class_='film-list')
            if not film_list:
                print(f"No film-list found on page {page_number}. Scraping process finished.")
                break

            # Find all animepost elements (each comic item)
            animeposts = film_list.find_all('div', class_='animepost')

            # If no more comic items are found on the page, stop the loop
            if not animeposts:
                print(f"No more data found on page {page_number}. Scraping process finished.")
                break

            comics_added_this_page = 0

            # Iterate through each comic item found
            for post in animeposts:
                try:
                    # Find animposx container
                    animposx = post.find('div', class_='animposx')
                    if not animposx:
                        continue

                    # Extract link and title from anchor
                    link_element = animposx.find('a', href=True)
                    if not link_element:
                        continue

                    komik_url = link_element.get('href', '')

                    # Skip if not a komik link
                    if '/komik/' not in komik_url:
                        continue

                    # Extract slug for duplicate checking
                    slug_match = re.search(r'/komik/([^/]+)/?$', komik_url)
                    slug = slug_match.group(1) if slug_match else ''

                    # Remove leading numbers from slug
                    slug = re.sub(r'^\d+-', '', slug)

                    # Skip if already seen
                    if slug in seen_slugs:
                        continue
                    seen_slugs.add(slug)

                    # Get title from anchor's title attribute or from h3
                    title = link_element.get('title', '')
                    if not title:
                        h3 = animposx.find('h3')
                        if h3:
                            title = h3.get_text(strip=True)

                    # Remove "Komik " prefix
                    if title.startswith('Komik '):
                        title = title[6:]

                    # Clean title - replace apostrophe and special characters with space
                    # \ufffd is the Unicode replacement character, \u2019 is right single quote
                    title = title.replace('\ufffd', ' ').replace('\u2019', ' ').replace('\u2018', ' ')
                    title = title.replace("'", ' ')
                    # Remove any remaining problematic characters
                    title = title.replace('\u00e2\u0080\u0099', ' ')  # UTF-8 encoded apostrophe
                    # Remove all non-ASCII characters (ä, ö, ü, etc.)
                    title = ''.join(c if ord(c) < 128 else ' ' for c in title)
                    # Clean up multiple spaces
                    title = ' '.join(title.split())

                    # Extract the cover image URL
                    img_element = animposx.find('img')
                    image_url = ''
                    if img_element:
                        image_url = img_element.get('src') or img_element.get('data-src') or ''

                    # Extract type from typeflag span
                    typeflag = post.find('span', class_='typeflag')
                    manga_type = komik_type
                    if typeflag:
                        # Class is like 'typeflag Manhwa' or 'typeflag Manga'
                        classes = typeflag.get('class', [])
                        for cls in classes:
                            if cls in ['Manhwa', 'Manga', 'Manhua']:
                                manga_type = cls
                                break

                    # Add the extracted data to the list
                    all_data.append({
                        'Title': title,
                        'Link': komik_url,
                        'Slug': slug,
                        'Image': image_url,
                        'Type': manga_type
                    })
                    comics_added_this_page += 1

                except Exception as e:
                    print(f"Error while processing an item: {e}")

            # If no new comics were added, we've reached the end
            if comics_added_this_page == 0:
                print(f"Page {page_number}: No new comics found (end of pagination)")
                break

            print(f"  +{comics_added_this_page} comics (total: {len(all_data)})")

            # Move to the next page
            page_number += 1
            # Add a short delay between requests to avoid overloading the server
            time.sleep(0.5)

        except requests.exceptions.RequestException as e:
            print(f"Failed to retrieve web page {page_number}. Error: {e}")
            break # Stop if a connection error occurs
        except Exception as e:
            print(f"An error occurred: {e}")
            break

    # Save all the collected data to a JSON file
    if all_data:
        output_file = 'komikindo_scrape_results.json'
        print(f"\nSaving a total of {len(all_data)} items to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(all_data, file, ensure_ascii=False, indent=4)
        print("Save successful!")
    else:
        print("No data was successfully scraped.")

    # Print the first few results for verification
    print("\nSample of scraped results:")
    for item in all_data[:5]:
        print(f"  - {item['Title']} ({item['Type']})")


if __name__ == "__main__":
    # Make sure you have the required libraries installed:
    # pip install requests beautifulsoup4
    scrape_komikcast()