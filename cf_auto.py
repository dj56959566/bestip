import requests
from bs4 import BeautifulSoup
import re
import json

# 普通网站列表
normal_urls = [
    "https://cf.vvhan.com/",
    "https://ip.164746.xyz",
    "http://ip.flares.cloud/",
    "https://vps789.com/cfip/?remarks=ip",
    "https://ipdb.030101.xyz/bestcfv4/",
    "https://www.wetest.vip/"
]

# JS 站点 API（直接返回文本或 JSON）
api_urls_text = [
    "https://addressesapi.090227.xyz/ct",  # 电信
    "https://addressesapi.090227.xyz/cm",  # 移动
    "https://addressesapi.090227.xyz/cu"   # 联通
    "https://bestcf.pages.dev/tiancheng/tw.txt", #台湾 TW
    "https://bestcf.pages.dev/xinyitang3/ipv4.txt"   # mia
]

api_urls_json = [
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

def fetch_api_text():
    ip_set, domain_set = set(), set()
    for url in api_urls_text:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            text = r.text
            ip_set.update(re.findall(ip_pattern, text))
            domain_set.update(re.findall(domain_pattern, text))
            print(f"✅ API文本 {url} -> {len(ip_set)} IP, {len(domain_set)} 域名 (累计)")
        except Exception as e:
            print(f"❌ API文本 {url}: {e}")
    return ip_set, domain_set

def fetch_api_json():
    ip_set, domain_set = set(), set()
    for url in api_urls_json:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            data = r.json()  # 直接解析 JSON
            # 假设 JSON 格式是列表 [{"ip":"1.2.3.4"}, {"ip":"5.6.7.8"}] 或类似结构
            for item in data:
                if isinstance(item, dict):
                    ip = item.get("ip")
                    if ip:
                        ip_set.add(ip)
                    domain = item.get("domain")
                    if domain:
                        domain_set.add(domain)
                elif isinstance(item, str):
                    # 兼容有些接口直接返回字符串 IP
                    ip_set.add(item)
            print(f"✅ API JSON {url} -> {len(ip_set)} IP, {len(domain_set)} 域名 (累计)")
        except Exception as e:
            print(f"❌ API JSON {url}: {e}")
    return ip_set, domain_set

if __name__ == "__main__":
    ip_total, domain_total = set(), set()

    # 普通网站
    ip1, d1 = fetch_normal()
    ip_total.update(ip1); domain_total.update(d1)

    # API 文本接口
    ip2, d2 = fetch_api_text()
    ip_total.update(ip2); domain_total.update(d2)

    # API JSON接口
    ip3, d3 = fetch_api_json()
    ip_total.update(ip3); domain_total.update(d3)

    # 保存结果
    with open("ip.txt", "w", encoding="utf-8") as f:
        f.write("# 优选IP\n")
        for ip in sorted(ip_total):
            f.write(ip + "\n")
        f.write("\n# 优选域名\n")
        for d in sorted(domain_total):
            f.write(d + "\n")

    print(f"🎉 共保存 {len(ip_total)} 个 IP, {len(domain_total)} 个 域名 到 ip.txt")
