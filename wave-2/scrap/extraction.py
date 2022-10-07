#!/usr/bin/env python3

import time
from typing import NamedTuple, Optional, Dict, Tuple, List, Any, Union
import os
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from bs4.element import Tag


class FullScrap(NamedTuple):
    # TUTO TRIDU ROZHODNE NEMEN
    linux_only_availability: List[str]
    most_visited_webpage: Tuple[int, str]
    changes: List[Tuple[int, str]]
    params: List[Tuple[int, str]]
    tea_party: Optional[str]

    def as_dict(self) -> Dict[str, Any]:
        return {
            'linux_only_availability': self.linux_only_availability,
            'most_visited_webpage': self.most_visited_webpage,
            'changes': self.changes,
            'params': self.params,
            'tea_party': self.tea_party
        }

BAD_OS_NAMES = ["Windows", "BSD", "macOS", "AIX"]
GOOD_OS_NAMES = ["Linux", "Unix"]

class Scanner:
    '''Class to load/store and process website info'''
    def __init__(self, base_url: str) -> None:
        self.visited_links: Dict[str, int] = {}
        self.link_count: List[List[int, str]] = []
        self.base_domain = urlparse(base_url).netloc

        self.tea_party = ""
        self.linux_only: List[str] = []
        self.func_10_params: List[Tuple[int, str]] = []
        self.version_modified: Dict[str, int] = {}

        # check if we have downloaded this before
        if os.path.isfile(f"scrap_{self.base_domain}.txt"):
            self.cached_responses = self.load_url_list()
        else:
            self.cached_responses: Dict[str, int] = {}
    
    def load_url_list(self) -> Dict[str, int]:
        cached_responses: Dict[str, int] = {}
        with open(f"scrap_{self.base_domain}.txt", "r") as f:
            for line in f.read().split("\n"):
                response_code = line[:3]
                # print(response_code)
                url = line[4:]
                cached_responses[url] = response_code
                if response_code == "418":
                    self.tea_party = url
            f.close()
        return cached_responses

    def save_url_list(self) -> None:
        link_list = list(self.visited_links.items())
        with open(f"scrap_{self.base_domain}.txt", "w") as f:
            for i in range(len(link_list) - 1):
                f.write(f"{link_list[i][1]};{link_list[i][0]}\n")
            f.write(f"{link_list[-1][1]};{link_list[-1][0]}")
            f.close()
    
    def save_file(self, url: str, content: str) -> None:
        url_file_path = self.base_domain + urlparse(url).path
        if url_file_path.endswith("/"):
            url_file_path += "index.html"
        # print(url_file_path)
        if not os.path.exists(url_file_path):
            os.makedirs(os.path.dirname(url_file_path), exist_ok=True)
            with open(url_file_path, "w") as f:
                f.write(content)
                f.close()
    
    def load_file(self, url: str) -> Optional[str]:
        url_file_path = self.base_domain + urlparse(url).path
        if url_file_path.endswith("/"):
            url_file_path += "index.html"
        if os.path.isfile(url_file_path):
            print("LOADING", url_file_path)
            with open(url_file_path, "r") as f:
                content = f.read()
                f.close()
            return content
        else:
            return None
        

    def check_if_downloaded(self) -> bool:
        if os.path.isfile(f"scrap_{self.base_domain}.txt"):
            return True
        return False

    def get_links(self, base_url: str, content: str) -> List[str]:
        links: List[str] = []
        soup = BeautifulSoup(content, "html.parser")
        for a in soup.find_all("a"):
            href = a.get("href").split("#")[0]
            link = urljoin(base_url, href, allow_fragments=False)
            if urlparse(link).netloc == self.base_domain:
                links.append(link)
                if link != base_url:
                    self.count_link(link)

        return links
    
    def parse_functions(self, content: str) -> None:
        soup = BeautifulSoup(content, "html.parser")
        func_list = soup.find_all("dl", class_="function")
        for func in func_list:
            func_name = func.find("dt").get("id")

            # check if linux only
            # tbh does not make much sense to search for "LINUX or UNIX" only
            # but at the same time excluding all the other POSIX OSes
            # such as AIX, BSD, ...
            available = func.find("p", class_="availability")
            if available is None:
                continue
            is_linux_only = None
            for os in GOOD_OS_NAMES:
                if os in available.text:
                    is_linux_only = True
            for os in BAD_OS_NAMES:
                if os in available.text:
                    is_linux_only = False
            if is_linux_only:
                self.linux_only.append(func_name)

        for func in func_list:
            func_name = func.find("dt").get("id")
            # check arg count
            params = func.find("dt").find_all("em", class_="sig-param")
            if len(params) > 10:
                self.func_10_params.append((len(params), func_name))

    
    def count_changes(self, content: str) -> None:
        soup = BeautifulSoup(content, "html.parser")
        added = soup.find_all("div", class_="versionadded")
        changed = soup.find_all("div", class_="versionchanged")

        for added_thing in added:
            version_str = added_thing.find("span", class_="versionmodified added")
            if version_str is not None:
                parsed = version_str.text[15:19].replace(":", "")
                spl = parsed.split(".")
                ver = spl[0] + "." + spl[1]
                if spl[0] != "3":
                    continue
                elif self.version_modified.get(ver) is None:
                    self.version_modified[ver] = 1
                else:
                    self.version_modified[ver] += 1

        for changed_thing in changed:
            version_str = changed_thing.find("span", class_="versionmodified changed")
            if version_str is not None:
                parsed = version_str.text[19:23].replace(":", "")
                spl = parsed.split(".")
                ver = spl[0] + "." + spl[1]
                if spl[0] != "3":
                    continue
                elif self.version_modified.get(ver) is None:
                    self.version_modified[ver] = 1
                else:
                    self.version_modified[ver] += 1

    def count_link(self, link: str) -> None:
        for i in range(len(self.link_count)):
            if self.link_count[i][1] == link:
                self.link_count[i][0] += 1
                return
        self.link_count.append([1, link])

    def valid_url(self, url: str) -> bool:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    
    def attempt_load(self, url: str) -> Tuple[Optional[str], bool]:
        content = self.load_file(url)
        if content is not None:
            success = True
        else:
            if url in self.cached_responses.keys():
                code = self.cached_responses[url]
                if code != 200:
                    success = True
                else:
                    success = False
            else:
                success = False
        return content, success

    def download_recursively(self, url: str) -> None:
        if url.endswith("/"):
            url += "index.html"
        content, success = self.attempt_load(url)
        if success:
            self.visited_links[url] = self.cached_responses[url]
            if content is None:
                # this was either 404 or other error last time we tried
                return
        else:
            time.sleep(0.5)
            response = download_webpage(url)

            self.visited_links[url] = response.status_code
            if response.status_code != 200:
                if response.status_code == 418:
                    self.tea_party = url
                print("can't get url")
                print(f"{response.status_code}: {url}")
                return
            content = response.content.decode("utf-8")
            self.save_file(url, content)
        

        new_links = self.get_links(url, content)
        self.parse_functions(content)
        self.count_changes(content)

        for url in new_links:
            if not self.valid_url(url):
                continue

            if url not in self.visited_links.keys():
                self.download_recursively(url)


def mk_scanner(base_url: str) -> Scanner:
    scanner = Scanner(base_url)
    scanner.download_recursively(base_url)
    return scanner


def download_webpage(url: str, *args, **kwargs) -> requests.Response:
    """
    Download the page and returns its response by using requests.get
    :param url: url to download
    :return: requests Response
    """
    # TUTO FUNKCI ROZHODNE NEMEN
    print('GET ', url)
    return requests.get(url, *args, **kwargs)


def get_linux_only_availability(scanner: Union[str, Scanner]) -> List[str]:
    """
    Finds all functions that area available only on Linux systems
    :param base_url: base url of the website
    :return: all function names that area available only on Linux systems
    """
    # last second workaround if someone tries to use this function in
    # a way that was not intended at first
    if type(scanner) == str:
        scanner = mk_scanner(scanner)
    
    return sorted(scanner.linux_only)


def get_most_visited_webpage(scanner: Union[str, Scanner]) -> Tuple[int, str]:
    """
    Finds the page with most links to it
    :param base_url: base url of the website
    :return: number of anchors to this page and its URL
    """
    if type(scanner) == str:
        scanner = mk_scanner(scanner)

    max_number = 0
    max_link = ""
    for number, link in scanner.link_count:
        if number > max_number:
            if link.endswith(".html") or link.endswith("/"):
                max_number = number
                max_link = link
    return (max_number, max_link)


def get_changes(scanner: Scanner) -> List[Tuple[int, str]]:
    """
    Locates all counts of changes of functions and groups them by version
    :param base_url: base url of the website
    :return: all counts of changes of functions and groups them by version, sorted from the most changes DESC
    """
    if type(scanner) == str:
        scanner = mk_scanner(scanner)

    items = scanner.version_modified.items()
    ordered = sorted(items, key=lambda x: x[1], reverse=True)
    out = []
    for i in ordered:
        out.append((i[1], i[0]))
    return out


def get_most_params(scanner: Scanner) -> List[Tuple[int, str]]:
    """
    Finds the function that accepts more than 10 parameters
    :param base_url: base url of the website
    :return: number of parameters of this function and its name, sorted by the count DESC
    """
    if type(scanner) == str:
        scanner = mk_scanner(scanner)

    return list(sorted(scanner.func_10_params, key=lambda x: (-x[0], x[1])))


def find_secret_tea_party(scanner: Scanner) -> Optional[str]:
    """
    Locates a secret Tea party
    :param base_url: base url of the website
    :return: url at which the secret tea party can be found
    """
    if type(scanner) == str:
        scanner = mk_scanner(scanner)

    if scanner.tea_party != "":
        return scanner.tea_party
    return None


def scrap_all(base_url: str) -> FullScrap:
    """
    Scrap all the information as efficiently as we can
    :param base_url: base url of the website
    :return: full web scrap of the Python docs
    """
    # Tuto funkci muzes menit, ale musi vracet vzdy tyto data
    web_scanner = Scanner(base_url)
    web_scanner.download_recursively(base_url)
    web_scanner.save_url_list()

    scrap = FullScrap(
        linux_only_availability=get_linux_only_availability(web_scanner),
        most_visited_webpage=get_most_visited_webpage(web_scanner),
        changes=get_changes(web_scanner),
        params=get_most_params(web_scanner),
        tea_party=find_secret_tea_party(web_scanner)
    )
    return scrap


def main() -> None:
    """
    Do a full scrap and print the results
    :return:
    """
    # Tuto funkci klidne muzes zmenit podle svych preferenci :)
    import json
    time_start = time.time()
    print(json.dumps(scrap_all('https://python.iamroot.eu/').as_dict()))
    print('took', int(time.time() - time_start), 's')


if __name__ == '__main__':
    main()