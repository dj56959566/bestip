import requests
from bs4 import BeautifulSoup
import re
import json
import base64
from urllib.parse import quote

# ============ 节点生成配置（生成前改成你自己的真实值，别发聊天里）============
# 这些 IP 只是 CF 中转地址，节点能不能连上取决于 UUID / 密码 / SNI 是不是你自己的。
# 下面是示例值，照原样生成只能当格式示例，连不上。
NODE_UUID = "b831381d-6324-4d53-ad4f-8cda48b30811"  # VLESS / VMess / TUIC 的 UUID（默认）
NODE_SNI = "cloudflare.182682.xyz"  # Reality / TLS 的 SNI，ip.txt 优选域名里能用的 CF 测试域名
NODE_HOST = "cloudflare.182682.xyz"  # WS 的 host，和 SNI 同一个域名
NODE_PATH = "/ws"                 # WS 的 path
NODE_PASSWORD = "pass123"         # Trojan / Hysteria2 / TUIC / AnyTLS 的密码
NODE_SS_PASSWORD = "pass123"      # Shadowsocks 密码
NODE_REALITY_PBK = "SbVKOEMjK0sIlbwg4akyBg5mL5KZwwB-ed4eEE7YnRc"  # Reality 公钥
NODE_REALITY_SID = "0123abcd"     # Reality shortId
# 只生成 CF 中转 IP 真正能用的 3 种（VLESS/Trojan/VMess，WS+TLS）写进 nodes.txt；
# 想把下面 19 种全都生成一份，改成 True，会另外写 nodes-all.txt
GENERATE_ALL_TYPES = False

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
    "https://cf.090227.xyz/cmcc",  # 移动
    "https://cf.090227.xyz/cu",  # 联通
    "https://bestcf.pages.dev/tiancheng/tw.txt", #台湾 TW
    "https://bestcf.pages.dev/xinyitang3/ipv4.txt",   # mia
    "https://raw.githubusercontent.com/djbadboy-56959566-qq-com/bestip/main/danfeng-lax.txt",  # DanFeng 中转 LAX
    "https://raw.githubusercontent.com/djbadboy-56959566-qq-com/bestip/main/danfeng-tg.txt",  # DanFeng 中转详细
    "https://zip.cm.edu.kg/all.txt"  # CMLiussss 中转 IP 每日更新，13130 条，2026-11-14 13:11 更新
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
            try:
                data = r.json()  # 直接解析 JSON
            except ValueError:
                # 不是 JSON（比如 JS 网页），退回按文本正则提取，不让整条源报错
                ip_set.update(re.findall(ip_pattern, r.text))
                domain_set.update(re.findall(domain_pattern, r.text))
                print(f"✅ API JSON {url} -> {len(ip_set)} IP, {len(domain_set)} 域名 (累计)")
                continue
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

def _vmess(ps, add, port, net, tls="", path="", host="", aid="0", sni=""):
    cfg = {"v": "2", "ps": ps, "add": add, "port": str(port),
           "id": NODE_UUID, "aid": aid, "scy": "auto", "net": net,
           "type": "none", "host": host, "path": path, "tls": tls, "sni": sni}
    return "vmess://" + base64.b64encode(json.dumps(cfg).encode()).decode()

def build_nodes(ip):
    """按你贴的 19 种常用格式，用一个 IP 生成节点链接。注意：
    Reality / SS / Hy2 / TUIC / AnyTLS 需要你的服务器真的跑了那种协议，
    单纯把 CF 中转 IP 换进去是连不上的；CF 中转 IP 能用的就是 WS+TLS 那三种。"""
    n = f"CF-{ip}"
    return {
        # VLESS + Reality + Vision
        "vless_reality_vision": f"vless://{NODE_UUID}@{ip}:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni={NODE_SNI}&fp=chrome&pbk={NODE_REALITY_PBK}&sid={NODE_REALITY_SID}&type=tcp#{n}-Reality",
        # VLESS + WS + TLS（CDN 中转常见）
        "vless_ws_tls": f"vless://{NODE_UUID}@{ip}:443?encryption=none&security=tls&sni={NODE_HOST}&type=ws&host={NODE_HOST}&path={quote(NODE_PATH, safe='') }#{n}-WS",
        # VLESS + grpc
        "vless_grpc": f"vless://{NODE_UUID}@{ip}:443?encryption=none&security=tls&sni={NODE_SNI}&type=grpc&serviceName=grpc-svc#{n}-Grpc",
        # VLESS + httpupgrade
        "vless_httpupgrade": f"vless://{NODE_UUID}@{ip}:80?encryption=none&security=none&type=httpupgrade&path=%2Fupgrade&host={NODE_SNI}#{n}-HU",
        # VLESS + h2
        "vless_h2": f"vless://{NODE_UUID}@{ip}:443?encryption=none&security=tls&sni={NODE_SNI}&type=h2&path=%2Fh2path&host={NODE_HOST}#{n}-H2",
        # VMess (ws + tls)
        "vmess_ws": _vmess(f"{n}-Vmess", ip, 443, "ws", tls="tls", path=NODE_PATH, host=NODE_HOST, sni=NODE_HOST),
        # VMess legacy (tcp, no tls, aid>0)
        "vmess_legacy": _vmess(f"{n}-VmessLegacy", ip, 8080, "tcp", aid="64"),
        # VMess grpc
        "vmess_grpc": _vmess(f"{n}-VmessGrpc", ip, 443, "grpc", tls="tls", path="grpc-svc"),
        # Trojan (sni + allowInsecure)
        "trojan": f"trojan://{quote(NODE_PASSWORD, safe='')}@{ip}:443?sni={NODE_SNI}&allowInsecure=1&type=tcp#{n}-Trojan",
        # Trojan ws
        "trojan_ws": f"trojan://{quote(NODE_PASSWORD, safe='')}@{ip}:443?sni={NODE_SNI}&type=ws&path={quote(NODE_PATH, safe='')}&host={NODE_HOST}#{n}-TrojanWs",
        # SS SIP002
        "ss_sip002": f"ss://aes-256-gcm:{quote(base64.b64encode(NODE_SS_PASSWORD.encode()).decode(), safe='')}@{ip}:8388#{n}-SS",
        # SS legacy base64
        "ss_legacy": "ss://" + base64.urlsafe_b64encode(f"aes-256-gcm:{NODE_SS_PASSWORD}".encode()).decode().rstrip("=") + f"@{ip}:8388#{n}-SSLegacy",
        # SS 2022
        "ss_2022": f"ss://2022-blake3-aes-128-gcm:{quote(base64.b64encode(b'8J3gp0S5y2X0YVpDZH2YvA==').decode(), safe='')}@{ip}:8388#{n}-SS2022",
        # Hysteria2
        "hy2": f"hy2://{quote(NODE_PASSWORD, safe='')}@{ip}:443?sni={NODE_SNI}&insecure=1&obfs=salamander&obfs-password=obfspw#{n}-Hy2",
        # Hysteria2 端口跳跃
        "hy2_hop": f"hysteria2://{quote(NODE_PASSWORD, safe='')}@{ip}:443?sni={NODE_SNI}&insecure=1&mport=2087-2097,443#{n}-Hy2Hop",
        # TUIC v5
        "tuic": f"tuic://{NODE_UUID}:{quote(NODE_PASSWORD, safe='')}@{ip}:443?congestion_control=bbr&udp_relay_mode=native&alpn=h3&sni={NODE_SNI}&allow_insecure=1#{n}-Tuic",
        # AnyTLS
        "anytls": f"anytls://{quote(NODE_PASSWORD, safe='')}@{ip}:443?sni={NODE_SNI}&insecure=1#{n}-Anytls",
        # IPv6 字面量（CF 收集的是 IPv4，这里沿用你贴的格式，仅作格式示例）
        "vless_ipv6": f"vless://{NODE_UUID}@[2001:db8::1]:443?encryption=none&security=tls&sni={NODE_SNI}&type=tcp#{n}-IPv6",
        # VLESS + ws 非标端口
        "vless_path_edge": f"vless://{NODE_UUID}@{ip}:8443?encryption=none&security=none&type=ws&path=%2Fed#{n}-Edge",
    }

# CF 中转 IP 真正能用的 3 种，写进 nodes.txt / sub.txt
CORE_TYPES = ["vless_ws_tls", "trojan_ws", "vmess_ws"]

def generate_nodes(ip_total):
    core, all_nodes = [], []
    for ip in sorted(ip_total):
        nodes = build_nodes(ip)
        core.extend(nodes[t] for t in CORE_TYPES)
        all_nodes.extend(nodes.values())
    with open("nodes.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(core) + "\n")
    with open("sub.txt", "w", encoding="utf-8") as f:  # base64 订阅，v2rayN 直接导入
        f.write(base64.b64encode("\n".join(core).encode()).decode())
    if GENERATE_ALL_TYPES:
        with open("nodes-all.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(all_nodes) + "\n")
    print(f"🎉 共生成 {len(core)} 个常用节点到 nodes.txt / sub.txt"
          + (f"，{len(all_nodes)} 个全格式节点到 nodes-all.txt" if GENERATE_ALL_TYPES else ""))

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

    # 按收集到的 IP 生成常用节点
    generate_nodes(ip_total)
