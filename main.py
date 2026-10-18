import csv
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException


BASE_URL = "https://books.toscrape.com/"
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def parse_book(book):
    """Extract a book's title, price, rating, and absolute URL from its HTML card."""
    try:
        link_element = book.find("h3").find("a")
        title = link_element["title"]
        price = float(book.find("p", class_="price_color").get_text().replace("£", ""))
        rating_class = book.find("p", class_="star-rating")["class"][1]
        rating = RATING_MAP.get(rating_class)

        if rating is None:
            raise ValueError(f"Неизвестный рейтинг книги: {title}")

        link = urljoin(BASE_URL, link_element["href"])
        return {
            "title": title,
            "price": price,
            "rating": rating,
            "link": link,
        }
    except ValueError:
        # Invalid numeric prices and unknown ratings should be visible to the caller.
        raise
    except (AttributeError, KeyError, IndexError, TypeError) as error:
        print("Не удалось разобрать карточку книги:", error)
        return None


def get_page(page_url):
    """Fetch and parse a page, retrying network failures up to three times."""
    attempt = 0

    while attempt < 3:
        try:
            response = requests.get(page_url, timeout=10)
            response.raise_for_status()
            response.encoding = "utf-8"
            return BeautifulSoup(response.text, "html.parser")
        except RequestException as error:
            print("Ошибка запроса страницы:", page_url, "\n", error)
            attempt += 1

    return None


def parse_page(soup):
    """Parse all book cards on one catalogue page."""
    books = soup.select("article.product_pod")
    books_data = []

    for book in books:
        result = parse_book(book)
        if result is not None:
            books_data.append(result)

    return books_data


def has_next_page(soup):
    """Return True when the catalogue page has a next-page link."""
    return bool(soup.select_one("li.next"))


def scrape_books(max_pages=4):
    """Collect book data from up to max_pages catalogue pages."""
    books_data = []
    page = 1

    while page <= max_pages:
        print(f"Обрабатывается страница {page}")

        if page == 1:
            page_url = BASE_URL
        else:
            page_url = f"{BASE_URL}catalogue/page-{page}.html"

        soup = get_page(page_url)
        if soup is None:
            break

        books_data.extend(parse_page(soup))

        if not has_next_page(soup):
            break

        page += 1

    return books_data


def save_books_to_csv(books_data, filename="result.csv"):
    """Save parsed book records to a UTF-8 CSV file."""
    fieldnames = ["title", "price", "rating", "link"]
    with open(filename, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(books_data)


if __name__ == "__main__":
    books_data = scrape_books()
    save_books_to_csv(books_data)

    print(f"Собрано книг: {len(books_data)}")
    print(
        "Все рейтинги в диапазоне 1–5:",
        all(isinstance(book["rating"], int) and 1 <= book["rating"] <= 5 for book in books_data),
    )
    print(
        "Ссылки уникальны:",
        len(books_data) == len(set(book["link"] for book in books_data)),
    )
    print("Все цены положительные:", all(book["price"] > 0 for book in books_data))
