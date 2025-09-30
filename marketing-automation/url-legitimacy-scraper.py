import re
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup

website_url = inputData['url']

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; LegitCheck/1.0)"
}

# List of social domains to watch out for
SOCIAL_DOMAINS = {
    "linkedin.com", "instagram.com", "facebook.com",
    "x.com", "twitter.com", "youtube.com", "tiktok.com"
}

def is_blank(value: str) -> bool:
    return not value or str(value).strip() == ""

# Standardize the url
def normalize_url(u: str) -> str:
    if is_blank(u):
        return u
    parsed = urlparse(u)
    if not parsed.scheme:
        return "https://" + u  # default to https
    return u

def fetch(url: str, timeout=12):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        return resp, resp.url
    except requests.RequestException:
        return None, None
      
# criteria: check if there are multiple links/not one pager
def extract_internal_links(soup: BeautifulSoup, base_url: str):
    base = urlparse(base_url)
    internal = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        full = urljoin(base_url, href)
        parsed = urlparse(full)
        if parsed.scheme in {"http", "https"} and parsed.netloc.lower() == base.netloc.lower():
            key = (parsed.path.rstrip("/") or "/") + (f"?{parsed.query}" if parsed.query else "")
            internal.add(key)
    return internal

# criteria: check if there are social links
def has_social_links(soup: BeautifulSoup):
    for a in soup.find_all("a", href=True):
        host = urlparse(a["href"]).netloc.lower()
        if any(dom in host for dom in SOCIAL_DOMAINS):
            return True
    return False

# criteria: check if there's contact info
def has_contact_info(soup: BeautifulSoup, text_sample_limit=30000):
    text = soup.get_text(" ", strip=True)[:text_sample_limit]
    email_pat = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
    phone_pat = re.compile(r"(\+?\d[\d\-\s().]{6,}\d)")
    contact_link = soup.find("a", string=re.compile(r"contact|support|help|customer service", re.I)) \
               or soup.find("a", href=re.compile(r"contact|support|help", re.I))
    return bool(email_pat.search(text) or phone_pat.search(text) or contact_link)

# criteria: is secure and available
def page_is_html(resp: requests.Response) -> bool:
    ctype = (resp.headers.get("Content-Type") or "").lower()
    return ("text/html" in ctype) or ("application/xhtml" in ctype) or (ctype == "")

def analyze_url(website_url: str):
    website_url = normalize_url(website_url)
    report = {
        "input": website_url,
        "blank": False,
        "criteria": {
            "secure_and_available": False,
            "not_one_pager": False,
            "many_internal_links": False,
            "has_social_link": False,
            "has_contact_info": False,
        },
        "score": 0,
        "meets_threshold": False,
        "looks_legit": False,
        "summary_60char": ""
    }

    if is_blank(website_url):
        report["blank"] = True
        report["summary_60char"] = "No URL provided."
        return report

    resp, final_url = fetch(website_url)
    if not resp or not page_is_html(resp):
        report["summary_60char"] = "Unreachable or not HTML; likely not legit."
        return report

    ok = (200 <= resp.status_code < 400)
    https = (urlparse(final_url).scheme == "https")
    report["criteria"]["secure_and_available"] = bool(ok and https)

    soup = BeautifulSoup(resp.text, "html.parser")
    internal_pages = extract_internal_links(soup, final_url)
    internal_count = len(internal_pages)

    report["criteria"]["not_one_pager"] = internal_count >= 2
    report["criteria"]["many_internal_links"] = internal_count >= 3
    report["criteria"]["has_social_link"] = has_social_links(soup)
    report["criteria"]["has_contact_info"] = has_contact_info(soup)

    score = sum(report["criteria"].values())
    report["score"] = score
    report["meets_threshold"] = score >= 3
    report["looks_legit"] = report["meets_threshold"]
  
# if 3/5 criteria are met it looks legit, result fed to an AI model to double check
    if report["looks_legit"]:
        report["summary_60char"] = "Likely legit: meets 3+ key checks"
    else:
        miss = [k for k, v in report["criteria"].items() if not v]
        report["summary_60char"] = "Not legit: fails " + ", ".join(miss[:2])

    # A few debug fields that can help in Zap runs
    report["debug"] = {
        "status_code": getattr(resp, "status_code", None),
        "final_url": final_url,
        "internal_pages_found": internal_count
    }
    return report


output = {"result": analyze_url(website_url)}
