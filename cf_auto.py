import requests
from bs4 import BeautifulSoup
import re
import json
import time

# 你已有的URL列表
normal_urls = [
    "https://cf.vvhan.com/",
    "https://ip.164746.xyz",
    "http://ip.flares.cloud/",
    "https://vps789.com/cfip/?remarks=ip",
    "https://ipdb.030101.xyz/bestcfv4/",
    "https://www.wetest.vip/"
]

api_urls_text = [
    "https://addressesapi.090227.xyz/ct",
    "https://addressesapi.090227.xyz/cm",
    "https://addressesapi.090227.xyz/cu"
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

# 获取IP地理位置
def get_ip_location(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}?fields=country,regionName,city", timeout=5)
        data = response.json()
        return data
    except:
        return None

# 过滤地区
def is_target_region(ip):
    location = get_ip_location(ip)
    if location:
        country = location.get('country', '')
        region = location.get('regionName', '')
        city = location.get('city', '')
        # 判断是否在目标地区
        if country in ['Hong Kong', 'Japan', 'Singapore']:
            return True
        if city == 'Los Angeles':
            return True
    return False

# 测速（可选，若只用地区过滤可不调用）
def test_speed(ip):
    # 这里可以用speedtest-cli或其他测速API
    # 暂时不调用测速，直接用地区过滤
    return True

def fetch_normal():
    ip_set, domain_set = set(), set()
    for url in normal_urls:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            text_all = soup.get_text(separator="\n")
            ips = re.findall(ip_pattern, text_all)
            for ip in ips:
                if is_target_region(ip):
                    ip_set.add(ip)
            print(f"✅ 普通 {url} -> {len(ips)} IP，筛选后 {len(ip_set)} IP")
        except Exception as e:
            print(f"❌ 普通 {url}: {e}")
    return ip_set

def fetch_api_text():
    ip_set = set()
    for url in api_urls_text:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            text = r.text
            ips = re.findall(ip_pattern, text)
            for ip in ips:
                if is_target_region(ip):
                    ip_set.add(ip)
            print(f"✅ API文本 {url} -> {len(ips)} IP，筛选后 {len(ip_set)} IP")
        except Exception as e:
            print(f"❌ API文本 {url}: {e}")
    return ip_set

def fetch_api_json():
    ip_set = set()
    for url in api_urls_json:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            data = r.json()
            for item in data:
                ip = None
                if isinstance(item, dict):
                    ip = item.get("ip")
                elif isinstance(item, str):
                    ip = item
                if ip and is_target_region(ip):
                    ip_set.add(ip)
            print(f"✅ API JSON {url} -> {len(ip_set)} IP")
        except Exception as e:
            print(f"❌ API JSON {url}: {e}")
    return ip_set

if __name__ == "__main__":
    ip_total = set()

    # 获取所有IP并筛选
    ip_total.update(fetch_normal())
    ip_total.update(fetch_api_text())
    ip_total.update(fetch_api_json())

    # 保存筛选后的IP到文件
    with open("ip.txt", "w", encoding="utf-8") as f:
        f.write("# 目标地区IP\n")
        for ip in sorted(ip_total):
            f.write(ip + "\n")

    print(f"筛选后符合地区的IP数量：{len(ip_total)}")
