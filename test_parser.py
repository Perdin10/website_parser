from unittest.mock import Mock, patch

import pytest
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

from main import (
    get_page,
    has_next_page,
    parse_book,
    parse_page,
    scrape_books,
    save_books_to_csv,
)


@pytest.fixture
def make_book():
    def _make_book(rating="Four", price="£51.77", include_rating=True):
        rating_html = (
            f'<p class="star-rating {rating}"></p>' if include_rating else ""
        )
        price_html = (
            f'<p class="price_color">{price}</p>' if price is not None else ""
        )
        html = f"""
        <article class="product_pod">
            <h3><a href="example.html" title="Test Book">Test Book</a></h3>
            {price_html}
            {rating_html}
        </article>
        """
        soup = BeautifulSoup(html, "html.parser")
        return soup.select_one("article.product_pod")

    return _make_book


def make_page(*books, has_next=False):
    next_html = '<li class="next"><a href="page-2.html">next</a></li>' if has_next else ""
    return BeautifulSoup(
        f'<html><body>{"".join(books)}{next_html}</body></html>',
        "html.parser",
    )


def book_html(title="Test Book", href="catalogue/test-book.html", rating="Four", price="£51.77"):
    return f"""
    <article class="product_pod">
        <h3><a href="{href}" title="{title}">{title}</a></h3>
        <p class="price_color">{price}</p>
        <p class="star-rating {rating}"></p>
    </article>
    """


def test_parse_book_returns_expected_fields(make_book):
    result = parse_book(make_book())

    assert result == {
        "title": "Test Book",
        "price": 51.77,
        "rating": 4,
        "link": "https://books.toscrape.com/catalogue/example.html",
    }


def test_parse_book_returns_none_when_price_is_missing(make_book):
    assert parse_book(make_book(price=None)) is None


def test_parse_book_returns_none_when_rating_element_is_missing(make_book):
    assert parse_book(make_book(include_rating=False)) is None


def test_parse_book_raises_for_unknown_rating(make_book):
    with pytest.raises(ValueError, match="Неизвестный рейтинг книги"):
        parse_book(make_book(rating="Six"))


def test_parse_book_raises_for_invalid_price(make_book):
    with pytest.raises(ValueError):
        parse_book(make_book(price="not-a-price"))


@pytest.mark.parametrize(
    ("rating_name", "expected_rating"),
    [
        ("One", 1),
        ("Two", 2),
        ("Three", 3),
        ("Four", 4),
        ("Five", 5),
    ],
)
def test_parse_book_converts_all_ratings(make_book, rating_name, expected_rating):
    assert parse_book(make_book(rating=rating_name))["rating"] == expected_rating


def test_get_page_returns_soup_on_success():
    response = Mock()
    response.text = "<html><body><h1>Catalogue</h1></body></html>"
    response.raise_for_status.return_value = None

    with patch("main.requests.get", return_value=response) as get:
        soup = get_page("https://example.com")

    assert soup.select_one("h1").text == "Catalogue"
    get.assert_called_once_with("https://example.com", timeout=10)
    assert response.encoding == "utf-8"


def test_get_page_retries_three_times_then_returns_none():
    with patch("main.requests.get", side_effect=RequestException("network error")) as get:
        result = get_page("https://example.com")

    assert result is None
    assert get.call_count == 3


def test_get_page_returns_none_after_http_error():
    response = Mock()
    response.raise_for_status.side_effect = RequestException("server error")

    with patch("main.requests.get", return_value=response) as get:
        result = get_page("https://example.com")

    assert result is None
    assert get.call_count == 3


def test_has_next_page_true():
    soup = BeautifulSoup('<li class="next"><a href="next.html">next</a></li>', "html.parser")
    assert has_next_page(soup) is True


def test_has_next_page_false():
    soup = BeautifulSoup("<html><body></body></html>", "html.parser")
    assert has_next_page(soup) is False


def test_parse_page_returns_empty_list_for_empty_page():
    soup = BeautifulSoup("<html><body></body></html>", "html.parser")
    assert parse_page(soup) == []


def test_parse_page_parses_one_book():
    soup = BeautifulSoup(book_html(), "html.parser")
    result = parse_page(soup)

    assert len(result) == 1
    assert result[0]["title"] == "Test Book"


def test_parse_page_parses_multiple_books():
    html = book_html(title="First", rating="Two") + book_html(
        title="Second", href="catalogue/second.html", rating="Five"
    )
    soup = BeautifulSoup(html, "html.parser")

    result = parse_page(soup)

    assert len(result) == 2
    assert [book["title"] for book in result] == ["First", "Second"]
    assert [book["rating"] for book in result] == [2, 5]


def test_scrape_books_collects_books_from_two_pages():
    page_one = BeautifulSoup(
        book_html(title="Book Two", rating="Two")
        + '<li class="next"><a href="page-2.html">next</a></li>',
        "html.parser",
    )
    page_two = BeautifulSoup(book_html(title="Book Four", rating="Four"), "html.parser")

    with patch("main.get_page", side_effect=[page_one, page_two]) as get_page_mock:
        result = scrape_books(max_pages=4)

    assert len(result) == 2
    assert [book["rating"] for book in result] == [2, 4]
    assert get_page_mock.call_count == 2


def test_scrape_books_stops_when_page_request_fails():
    with patch("main.get_page", return_value=None) as get_page_mock:
        result = scrape_books()

    assert result == []
    get_page_mock.assert_called_once()


def test_scrape_books_respects_max_pages():
    page = BeautifulSoup(
        book_html() + '<li class="next"><a href="page-2.html">next</a></li>',
        "html.parser",
    )

    with patch("main.get_page", return_value=page) as get_page_mock:
        result = scrape_books(max_pages=2)

    assert len(result) == 2
    assert get_page_mock.call_count == 2


def test_scrape_books_stops_when_no_next_page():
    page = BeautifulSoup(book_html(), "html.parser")

    with patch("main.get_page", return_value=page) as get_page_mock:
        result = scrape_books(max_pages=4)

    assert len(result) == 1
    assert get_page_mock.call_count == 1


def test_save_books_to_csv_writes_header_and_rows(tmp_path):
    output_file = tmp_path / "books.csv"
    records = [
        {
            "title": "Test Book",
            "price": 51.77,
            "rating": 4,
            "link": "https://books.toscrape.com/catalogue/test-book.html",
        }
    ]

    save_books_to_csv(records, output_file)

    content = output_file.read_text(encoding="utf-8")
    assert "title,price,rating,link" in content
    assert "Test Book" in content
    assert "51.77" in content
