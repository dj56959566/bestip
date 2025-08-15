import requests
from bs4 import BeautifulSoup
import re

# 普通网站列表
normal_urls = [
    "https://cf.vvhan.com/",
    "https://ip.164746.xyz",
    "http://ip.flares.cloud/",
    "https://vps789.com/cfip/?remarks=ip",
    "https://ipdb.030101.xyz/bestcfv4/",
    "https://www.wetest.vip/"
]

# 直接 API （JS 渲染页面的真实接口）
api_urls = [
    "https://addressesapi.090227.xyz/ct",   # 电信
    "https://addressesapi.090227.xyz/cm",   # 移动（部分地区可能无数据）
    "https://addressesapi.090227.xyz/cu",   # 联通（部分地区可能无数据）
    "https://stock.hostmonit.com/CloudFlareYes"
]

# 正则表达式
ip_pattern = r"\b\d{1,3}(?:\.\d{1,3}){3}\b"
domain_pattern = r"\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def fetch_normal():
    ip_set, domain_set = set(), set()
    for url in normal_urls:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            text_all = soup.get_text(separator="\n")
            ip_set.update(re.findall(ip_pattern, text_all))
            domain_set.update(re.findall(domain_pattern, text_all))
            print(f"✅ 普通 {url} -> {len(ip_set)} IP, {len(domain_set)} 域名 (累计)")
        except Exception as e:
            print(f"❌ 普通 {url}: {e}")
    return ip_set, domain_set

def fetch_api():
    ip_set, domain_set = set(), set()
    for url in api_urls:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            text = r.text
            ip_set.update(re.findall(ip_pattern, text))
            domain_set.update(re.findall(domain_pattern, text))
            print(f"✅ API {url} -> {len(ip_set)} IP, {len(domain_set)} 域名 (累计)")
        except Exception as e:
            print(f"❌ API {url}: {e}")
    return ip_set, domain_set

if __name__ == "__main__":
    ip_total, domain_total = set(), set()
    ip1, d1 = fetch_normal()
    ip2, d2 = fetch_api()
    ip_total.update(ip1); ip_total.update(ip2)
    domain_total.update(d1); domain_total.update(d2)

    with open("ip.txt", "w", encoding="utf-8") as f:
        f.write("# 优选IP\n")
        for ip in sorted(ip_total):
            f.write(ip + "\n")
        f.write("\n# 优选域名\n")
        for d in sorted(domain_total):
            f.write(d + "\n")

    print(f"🎉 保存 {len(ip_total)} 个 IP, {len(domain_total)} 个 域名 到 ip.txt")
