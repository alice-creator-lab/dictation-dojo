#!/usr/bin/env python3
"""建立權威嘅「字 → 教育局字詞表 id」對照表。

用 POST 直接搜字（searchMethod=direct），再由回傳頁嘅筆順動畫 iframe
讀出 id：  /EmbziciwebRes/stkdemo_js/<range>/<id>.html

唔用 result.jsp?id=N 反推字，因為頁面第一個詞語往往唔係表頭字
（例如 id=3103 係「經」，但第一條詞語係「已經」），會對錯字。

輸出：edb-ids.json（放喺 app 根目錄，{ "字": id }）
"""
import http.cookiejar, json, os, re, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.join(ROOT, "tools")
CACHE = os.path.join(HERE, ".edb-post")
OUT = os.path.join(ROOT, "edb-ids.json")
URL = "https://www.edbchinese.hk/lexlist_ch/result.jsp"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124 Safari/537.36")
STK = re.compile(r"stkdemo_js/[^/'\"]+/(\d{4})\.html")

os.makedirs(CACHE, exist_ok=True)
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def prime():
    """開首頁換 JSESSIONID（POST 要）。"""
    req = urllib.request.Request("https://www.edbchinese.hk/lexlist_ch/index.jsp",
                                 headers={"User-Agent": UA})
    with opener.open(req, timeout=30) as r:
        r.read()


def lookup(ch):
    path = os.path.join(CACHE, "%04x.html" % ord(ch))
    if os.path.exists(path):
        m = STK.search(open(path, encoding="utf-8", errors="ignore").read())
        return (ch, m.group(1) if m else None)
    body = urllib.parse.urlencode({
        "searchMethod": "direct", "searchCriteria": ch, "submit": "",
    }).encode()
    last = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(URL, data=body, headers={
                "User-Agent": UA,
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": "https://www.edbchinese.hk/lexlist_ch/index.jsp",
            })
            with opener.open(req, timeout=30) as r:
                t = r.read().decode("utf-8", "ignore")
            open(path, "w", encoding="utf-8").write(t)
            m = STK.search(t)
            return (ch, m.group(1) if m else None)
        except Exception as e:      # noqa: BLE001
            last = e
            time.sleep(1.5 * (attempt + 1))
    print("FAIL %s %s" % (ch, last), file=sys.stderr)
    return (ch, None)


def universe():
    chars = []
    seen = set()

    def add(c):
        if c not in seen:
            seen.add(c)
            chars.append(c)

    for line in open(os.path.join(ROOT, "dict.txt"), encoding="utf-8"):
        w = line.strip()
        if w:
            for c in w:
                add(c)
    # 舊對照表抽到嘅字（雖然 id 唔可靠，但字本身係字表內嘅字，值得補查）
    old = os.path.join(HERE, "edb-ids.json")
    if os.path.exists(old):
        for c in json.load(open(old, encoding="utf-8")):
            add(c)
    return chars


def main():
    chars = universe()
    print("lookup %d chars" % len(chars), flush=True)
    prime()
    out, missing = {}, []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for i, (c, sid) in enumerate(ex.map(lookup, chars), 1):
            if sid:
                out[c] = int(sid)
            else:
                missing.append(c)
            if i % 300 == 0:
                print("...%d/%d (found %d)" % (i, len(chars), len(out)), flush=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False,
              separators=(",", ":"), sort_keys=False)
    print("wrote %s: %d chars, missing %d" % (OUT, len(out), len(missing)))
    print("missing sample:", "".join(missing[:40]))


if __name__ == "__main__":
    main()
