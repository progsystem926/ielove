import csv
import re

import requests
from bs4 import BeautifulSoup

PREFECTURE_MAPPING = {
    "osaka": "大阪府",
    "hyogo": "兵庫県",
}


def get_urls(base_url, page):
    url = f"{base_url}/?pg={page}"
    print(f"Fetching URLs from: {url}")
    try:
        res = requests.get(url)
        res.raise_for_status()  # HTTPエラーがあれば例外を発生させる
        soup = BeautifulSoup(res.text, "lxml")
        links = soup.find_all(
            lambda tag: tag.name == "a"
            and tag.parent.name == "p"
            and "ttl" in tag.parent.get("class", [])
        )
        return ["https://www.ielove.co.jp" + link.get("href") for link in links]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URLs from {url}: {e}")
        return []


def fetch_soup(url):
    try:
        res = requests.get(url)
        res.raise_for_status()
        return BeautifulSoup(res.text, "lxml")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def extract_company_name(soup):
    company_name_element = soup.find(id="dc_info_title") or soup.find(
        class_="company-header__name"
    )
    return (
        company_name_element.get_text(strip=True)
        if company_name_element
        else "Not found"
    )


def extract_address_info(soup):
    try:
        postcode_address = (
            soup.find("th", string="住所")
            .find_parent("tr")
            .find("td")
            .get_text(strip=True)
        )
        postcode_pattern = r"\d{3}-\d{4}"
        postcode_match = re.search(postcode_pattern, postcode_address)
        postcode = postcode_match.group() if postcode_match else ""
        address = (
            re.sub(postcode_pattern, "", postcode_address)
            .strip()
            .replace("地図を表示", "")
            .strip()
        )
        address = re.sub(r"^〒", "", address).strip()  # 〒を削除する
        return postcode, address
    except AttributeError:
        print("Address information not found")
        return "", ""


def extract_contact_info(soup, info_type):
    try:
        elements = soup.find_all("th", string=info_type)
        for element in elements:
            if element and element.next_sibling.name == "td":
                return element.next_sibling.get_text(strip=True)
        return "Not found"
    except AttributeError:
        print(f"{info_type} information not found")
        return ""


def extract_company_data(url, prefecture_jp):
    soup = fetch_soup(url)
    if soup:
        company_name = extract_company_name(soup)
        postcode, address = extract_address_info(soup)
        tel = extract_contact_info(soup, "TEL")
        fax = extract_contact_info(soup, "FAX")
        ceo = extract_contact_info(soup, "代表者名")
        return [
            company_name,
            "いえらぶ不動産会社検索",
            prefecture_jp,
            tel,
            fax,
            postcode,
            "",
            "",
            address,
            ceo,
        ]
    else:
        return None


def get_detail(base_url, pages, prefecture_jp):
    data = []
    for page in pages:
        urls = get_urls(base_url, page)
        for i, url in enumerate(urls):
            company_data = extract_company_data(url, prefecture_jp)
            if company_data:
                data.append(company_data)
                print(f"Page {page}, Item {i + 1}")
    return data


def output_csv(data):
    with open("data.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(data)


def main():
    prefecture_en = input("都道府県を指定してください（例：osaka）: ")
    location = input("URLの場所の部分を指定してください（例：osaka_miyakojima-city）: ")
    page_range = input("ページ番号の範囲を指定してください（例：1-3）: ")

    try:
        start_page, end_page = map(int, page_range.split("-"))
        pages = range(start_page, end_page + 1)
    except ValueError:
        print("ページ番号の範囲は整数の範囲で指定してください。例：1-3")
        return

    prefecture_jp = PREFECTURE_MAPPING.get(prefecture_en, prefecture_en)
    base_url = f"https://www.ielove.co.jp/company/search/{prefecture_en}/{location}"
    data = get_detail(base_url, pages, prefecture_jp)
    output_csv(data)


if __name__ == "__main__":
    main()
