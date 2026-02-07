import time
import json
import re
import pandas as pd
import requests
import random
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

# --- 1. KONFIGURASI ---
BASE_URL = "https://www.loker.id/lowongan-kerja/information-technology"
MAX_PAGES = 100         # Scrape halaman 1 sampai 10
MAX_WORKERS = 2        # Thread worker untuk detail processing
OUTPUT_FILE = "data_lokerid_fixed.csv"    

# --- 2. KAMUS DATA & HELPER (FROM KALIBRR & LOKERID) ---
def get_provinsi(kota):
    if pd.isna(kota): return "Lainnya"
    kota = str(kota).title().strip()
    kota_lower = kota.lower()   
    
    mapping = {
        "Jakarta Raya": "DKI Jakarta", "Jakarta Selatan": "DKI Jakarta", "Jakarta Barat": "DKI Jakarta",
        "Jakarta Pusat": "DKI Jakarta", "Jakarta Timur": "DKI Jakarta", "Jakarta Utara": "DKI Jakarta",
        "Tangerang": "Banten", "Tangerang Selatan": "Banten", "Banten": "Banten",
        "Bandung": "Jawa Barat", "Bogor": "Jawa Barat", "Depok": "Jawa Barat", "Bekasi": "Jawa Barat",
        "Cikarang": "Jawa Barat", "Sukabumi": "Jawa Barat", "Karawang": "Jawa Barat", "Cirebon": "Jawa Barat",
        "Semarang": "Jawa Tengah", "Solo": "Jawa Tengah", "Surakarta": "Jawa Tengah", "Magelang": "Jawa Tengah",
        "Yogyakarta": "DI Yogyakarta", "Sleman": "DI Yogyakarta", "Bantul": "DI Yogyakarta",
        "Surabaya": "Jawa Timur", "Malang": "Jawa Timur", "Sidoarjo": "Jawa Timur", "Gresik": "Jawa Timur",
        "Kediri": "Jawa Timur", "Bali": "Bali", "Denpasar": "Bali"
    }
    
    if kota in mapping: return mapping[kota]
    
    # Heuristic Search
    if "jakarta" in kota_lower: return "DKI Jakarta"
    if any(x in kota_lower for x in ["bandung", "bekasi", "bogor", "depok", "cimahi", "karawang"]): return "Jawa Barat"
    if any(x in kota_lower for x in ["tangerang", "banten", "serang"]): return "Banten"
    if any(x in kota_lower for x in ["semarang", "solo", "kudus"]): return "Jawa Tengah"
    if any(x in kota_lower for x in ["surabaya", "malang", "sidoarjo", "gresik"]): return "Jawa Timur"
    if any(x in kota_lower for x in ["yogyakarta", "jogja", "sleman"]): return "DI Yogyakarta"
    
    return "Lainnya"

IT_SKILLS_DATABASE = {
    # --- PROGRAMMING LANGUAGES ---
    "python", "java", "c++", "c#", "golang", "php", "ruby", "swift", "kotlin", "typescript", 
    "javascript", "html", "css", "r", "dart", "matlab", "scala", "rust", "shell", "bash", "perl", "lua", "assembly",
    # --- FRAMEWORKS & LIBRARIES ---
    "react", "angular", "vue", "node.js", "django", "flask", "spring boot", "laravel", "codeigniter",
    "flutter", "react native", "next.js", "nuxt.js", "express.js", "pandas", "numpy", "tensorflow", 
    "pytorch", "keras", "scikit-learn", "dotnet", ".net", "jquery", "bootstrap", "tailwind", "fastapi", "hibernate",
    # --- DATABASE (SQL & NoSQL) ---
    "sql", "mysql", "postgresql", "mongodb", "oracle", "redis", "firebase", "elasticsearch", 
    "sql server", "mariadb", "sqlite", "cassandra", "dynamodb", "couchdb", "neo4j", "hbase", "realm",
    # --- CLOUD & DEVOPS ---
    "aws", "azure", "google cloud", "gcp", "docker", "kubernetes", "jenkins", "terraform", 
    "git", "github", "gitlab", "bitbucket", "linux", "ubuntu", "centos", "redhat", "nginx", "apache", 
    "ci/cd", "ansible", "circleci", "prometheus", "grafana", "elk stack", "openshift", "helm", "vagrant",
    # --- DATA & AI ---
    "snowflake", "bigquery", "redshift", "databricks", "azure synapse", "teradata", "vertica",
    "airflow", "dbt", "luigi", "prefect", "glue", "athena", "kinesis", "kafka", "rabbitmq", "pub/sub",
    "tableau", "power bi", "looker", "qlikview", "qlik sense", "sas", "spss", "excel", "google data studio",
    "big data", "hadoop", "spark", "pyspark", "hive", "pig", "impala", "flink",
    "machine learning", "deep learning", "nlp", "computer vision", "generative ai", "llm",
    "hugging face", "openai", "langchain", "mlflow", "kubeflow", "sagemaker", "vertex ai", 
    "jupyter", "colab", "opencv", "yolo", "ocr",
    # --- NETWORKING ---
    "CCNA", "CCNP", "CCIE", "CCDP", "CCDE", "CCAr",
    "JNCIA", "JNCIS", "JNCIP", "JNCIE",
    "MTCNA", "MTCRE", "MTCINE",
    "NSE1", "NSE2", "NSE3", "NSE4", "NSE7", "NSE8",
    "PCNSA", "PCNSE",
    "COMPTIA NETWORK+", "COMPTIA SECURITY+", "CISSP", "CISM", "CEH", "OSCP", "CISA",
    "tcp/ip", "dns", "dhcp", "bgp", "ospf", "eigrp", "rip", "mpls", "vlan", "vxlan", "sd-wan", 
    "vpn", "ipsec", "ssl/tls", "stp", "rstp", "nat", "pat", "qos", "ipv4", "ipv6", "subnetting",
    "routing", "switching", "osi model", "voip", "sip", "wan", "lan", "wlan", "man",
    "cisco", "juniper", "mikrotik", "fortinet", "palo alto", "aruba", "ubiquiti", "unifi", 
    "f5", "citrix", "arista", "ruckus", "tplink", "huawei", "dell networking", "barracuda",
    "wireshark", "packet tracer", "gns3", "eve-ng", "nmap", "solarwinds", "prtg", "nagios", 
    "zabbix", "cacti", "netcat", "tcpdump", "iperf", "putty", "crt", "winbox", "ping", "traceroute",
    # --- NETWORK SECURITY ---
    "cybersecurity", "penetration testing", "firewall", "next-gen firewall", "ngfw", "ids", "ips", 
    "siem", "splunk", "wazuh", "nessus", "metasploit", "burp suite", "kalilinux", "soc", 
    "incident response", "forensics", "zero trust", "waf", "ddos protection",
    # --- IOT & HARDWARE ---
    "iot", "arduino", "raspberry pi", "embedded systems", "microcontroller", "mqtt", "coap",
    "fpga", "plc", "scada", "hmi", "pcb", "stm32", "esp32", "esp8266", "verilog", "vhdl",
    # --- TOOLS & METHODOLOGIES ---
    "jira", "trello", "asana", "confluence", "notion",
    "agile", "scrum", "kanban", "waterfall", "sdlc", "devops",
    "qa", "selenium", "appium", "cypress", "junit", "postman", "soapui",
    "figma", "adobe xd", "sketch", "invision", "zeplin"
}

SPECIAL_SKILLS = {"c": r"\bc\b", "go": r"\bgo\b", ".net": r"\.net", "c#": r"c#", "c++": r"c\+\+"}

def determine_category(title):
    title_lower = str(title).lower()
    if any(x in title_lower for x in ['data', 'ai', 'learning', 'intelligence', 'analyst', 'scientist']):
        return 'Data / AI'
    elif any(x in title_lower for x in ['frontend', 'backend', 'fullstack', 'software', 'developer', 'programmer', 'web', 'mobile', 'android', 'ios']):
        return 'Software Engineering'
    elif any(x in title_lower for x in ['qa', 'tester', 'quality']):
        return 'QA / Tester'
    elif any(x in title_lower for x in ['devops', 'sre', 'cloud', 'system', 'network', 'infra', 'security', 'cyber']):
        return 'DevOps / Infra'
    elif any(x in title_lower for x in ['product', 'manager', 'scrum', 'project', 'owner']):
        return 'Product / Project'
    else:
        return 'Other'

def extract_skills(text):
    if pd.isna(text): return []
    text_lower = str(text).lower()
    found_skills = set()
    for skill in IT_SKILLS_DATABASE:
        if len(skill) > 2 and skill not in SPECIAL_SKILLS:
            if re.search(r"\b" + re.escape(skill) + r"\b", text_lower):
                found_skills.add(skill)
    for skill, pattern in SPECIAL_SKILLS.items():
        if re.search(pattern, text_lower):
            found_skills.add(skill)
    return sorted(list(found_skills))

# --- HELPER FROM LOKERID SCRAPPING ---
def clean_text(text):
    if not text: return ""
    return " ".join(text.split())

def clean_gaji_strict(text):
    if not text: return "No data"
    text = " ".join(text.split())
    if len(text) > 100: return "No data"
    if not any(char.isdigit() for char in text): return "No data"
    return text

def get_kualifikasi_list(soup):
    candidates = soup.find_all(string=re.compile("Kualifikasi|Qualification|Requirement", re.IGNORECASE))
    for header_text in candidates:
        header_tag = header_text.parent
        if header_tag.name in ['script', 'style', 'head', 'title']: continue
            
        next_element = header_tag.find_next_sibling()
        while next_element and (next_element.name is None or next_element.get_text(strip=True) == ""):
            next_element = next_element.next_sibling
            
        list_container = None
        if next_element:
            if next_element.name in ['ul', 'ol']:
                list_container = next_element
            elif next_element.name == 'div':
                list_container = next_element.find(['ul', 'ol'])
        
        if list_container:
            items = []
            for li in list_container.find_all('li'):
                text_poin = li.get_text(" ", strip=True)
                if "Beranda" in text_poin or "Loker" in text_poin: continue
                text_poin = re.sub(r'\s+', ' ', text_poin)
                items.append(text_poin)
            if items: return " | ".join(items)
    return "-"

def get_info_by_icon_or_label(soup, keywords):
    for keyword in keywords:
        target = soup.find(string=re.compile(keyword, re.IGNORECASE))
        if target:
            parent = target.parent.parent 
            if parent:
                full_text = parent.get_text(" ", strip=True)
                # Cleaning simple
                value = re.sub(f".*{keyword}", "", full_text, flags=re.IGNORECASE).strip(": ").strip()
                return value
    return "Hidden/Tidak Disebutkan"

def simplify_education(text):
    if not text or text == "Tidak Disebutkan": return text
    text_upper = text.upper()
    if any(x in text_upper for x in ['SMA', 'SMK', 'STM']):
        return "SMA/SMK"
    if any(x in text_upper for x in ['DIPLOMA', 'D1', 'D2', 'D3', 'D4']):
        return "Diploma"
    if any(x in text_upper for x in ['SARJANA', 'S1', 'BACHELOR']):
        return "S1"
    if any(x in text_upper for x in ['MASTER', 'S2', 'MAGISTER']):
        return "S2"
    if any(x in text_upper for x in ['DOKTOR', 'S3']):
        return "S3"
    return text

def parse_salary_average(text):
    """
    Parses 'Rp 5.5 - 6 Juta' or 'Rp 5 - 10 Juta' into an integer average.
    Returns None if parsing fails.
    """
    if not text or text in ["Hidden", "No data", "Hidden/Tidak Disebutkan"]:
        return None
    
    try:
        # Normalize text: Remove 'Rp', 'Juta', and whitespace
        clean = text.lower().replace("rp", "").replace("juta", "").replace("jt", "").strip()
        
        # Handle range "5.5 - 6"
        if "-" in clean:
            parts = clean.split("-")
            min_val = float(parts[0].strip())
            max_val = float(parts[1].strip())
            average = (min_val + max_val) / 2
            
            # Convert to full value (millions)
            return int(average * 1_000_000)
            
        # Handle single value "5.5" (rare but possible)
        else:
            val = float(clean)
            return int(val * 1_000_000)
            
    except Exception:
        return None

# --- 3. TAHAP 1: HARVEST URL ---
def harvest_data(max_pages, search_query=None):
    print(f"🚜 HARVESTING: Mengambil data dari {max_pages} halaman...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://www.loker.id/',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    harvested_items = []
    
    # Base URL Determination
    if search_query:
        # Format: https://www.loker.id/cari-lowongan-kerja/page/{page}?q={query}&category=information-technology
        base_search_url = "https://www.loker.id/cari-lowongan-kerja"
        print(f"   🔎 Mode Pencarian: '{search_query}' (Kategori IT)")
    else:
        # Format: https://www.loker.id/lowongan-kerja/information-technology/page/{page}
        base_default_url = "https://www.loker.id/lowongan-kerja/information-technology"
        print("   📂 Mode Default: List Lowongan IT Terbaru")

    for page in range(1, max_pages + 1):
        if search_query:
            # Construct Search URL
            # Note: Pagination for search results usually looks like /cari-lowongan-kerja/page/2?q=...
            if page == 1:
                url_target = f"{base_search_url}?q={search_query}&category=information-technology"
            else:
                url_target = f"{base_search_url}/page/{page}?q={search_query}&category=information-technology"
        else:
            # Construct Default URL
            if page == 1:
                url_target = base_default_url
            else:
                url_target = f"{base_default_url}/page/{page}"

        print(f"   >> Halaman {page}/{max_pages}: {url_target}")
        
        try:
            resp = requests.get(url_target, headers=headers, timeout=20)
            if resp.status_code != 200:
                print(f"   [!] Gagal Halaman {page}: Status {resp.status_code}")
                continue
            
            soup = BeautifulSoup(resp.content, "html.parser")
            cards = soup.find_all('article', class_='card')
            
            if not cards:
                print(f"   [!] Tidak ada data di halaman {page}. Mungkin halaman habis.")
                break

            for card in cards:
                try:
                    link_tag = card.find('a', href=True)
                    if not link_tag: continue
                    
                    job_url = link_tag['href']
                    if not job_url.startswith('http'): job_url = "https://www.loker.id" + job_url
                    
                    judul_tag = card.find('h3')
                    posisi = judul_tag.text.strip() if judul_tag else "Tanpa Judul"
                    
                    comp_tag = card.find('span', class_='text-secondary-500')
                    perusahaan = comp_tag.text.strip() if comp_tag else "Perusahaan N/A"
                    
                    loc_tag = card.find('span', attrs={'translate': 'no'})
                    lokasi = loc_tag.text.strip() if loc_tag else "Indonesia"
                    
                    harvested_items.append({
                        "link": job_url,
                        "posisi": posisi,
                        "perusahaan": perusahaan,
                        "lokasi": lokasi
                    })
                except Exception:
                    continue
            
            time.sleep(1) # Polite sleep
            
        except Exception as e:
            print(f"   [!] Error Halaman {page}: {e}")
            
    print(f"✅ HARVEST SELESAI: {len(harvested_items)} lowongan ditemukan.\n")
    return harvested_items

# --- 4. TAHAP 2: PROCESSING ---
def process_single_item(item):
    url = item['link']
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://www.loker.id/',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    try:
        # PENTING: Loker.id bisa memblokir jika terlalu agresif, gunakan sleep jika perlu di dalam thread
        time.sleep(random.uniform(0.5, 1.5)) 
        
        response = requests.get(url, headers=headers, timeout=15)
        
        # Default data
        perusahaan = item['perusahaan']
        posisi = item['posisi']
        kota_raw = item['lokasi']
        gaji_angka = None 
        pendidikan = "Tidak Disebutkan"
        jenis = "Full Time" 
        deskripsi_full = ""
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # --- EKSTRAKSI ALA lokerid_scrapping.py ---
            
            # 1. Gaji (Parse Average)
            raw_gaji = get_info_by_icon_or_label(soup, ["Gaji", "Salary", "IDR", "Rp"])
            if raw_gaji != "Hidden/Tidak Disebutkan":
                # Parse "Rp 5.5 - 6 Juta" -> 5750000
                gaji_angka = parse_salary_average(raw_gaji)
            
            # 2. Tipe Pekerjaan -> map ke 'jenis'
            raw_jenis = get_info_by_icon_or_label(soup, ["Tipe Pekerjaan", "Job Type", "Status"])
            if raw_jenis != "Hidden/Tidak Disebutkan":
                jenis = raw_jenis
            
            # 3. Pendidikan
            raw_pendidikan = get_info_by_icon_or_label(soup, ["Pendidikan", "Education", "Degree"])
            if raw_pendidikan != "Hidden/Tidak Disebutkan":
                pendidikan = simplify_education(raw_pendidikan)
                
            # 4. Kualifikasi & Deskripsi untuk Skill Mining
            kualifikasi = get_kualifikasi_list(soup)
            
            desc_container = soup.find('div', id='description')
            if not desc_container:
                # Fallback logic
                potential_divs = soup.find_all('div', class_=False)
                max_len = 0
                for div in potential_divs:
                    text_len = len(div.get_text())
                    if text_len > max_len and text_len > 200:
                        desc_container = div
                        max_len = text_len
            
            deskripsi_body = desc_container.get_text(" ", strip=True) if desc_container else ""
            deskripsi_full = f"{deskripsi_body} {kualifikasi}"

        # --- FINAL PROCESSING & MAPPING ---
        skills_found = extract_skills(deskripsi_full)
        provinsi = get_provinsi(kota_raw)
        kategori = determine_category(posisi)
        
        # Mapping ke format Kalibrr
        return {
            "Perusahaan": perusahaan,
            "Posisi": posisi,
            "kategori_posisi": kategori,
            "kota": kota_raw,
            "gaji_angka": gaji_angka,     # Updated to use calculated average (int/float)
            "list_skill": str(skills_found),
            "pendidikan": pendidikan,
            "jenis": jenis,
            "provinsi": provinsi,
            "link": url
        }

    except Exception as e:
        print(f"❌ Error {url}: {e}")
        return {
            "Perusahaan": item['perusahaan'],
            "Posisi": item['posisi'],
            "kategori_posisi": determine_category(item['posisi']),
            "kota": item['lokasi'],
            "gaji_angka": None,
            "list_skill": "[]",
            "pendidikan": "Tidak Disebutkan",
            "jenis": "Full Time",
            "provinsi": get_provinsi(item['lokasi']),
            "link": url
        }

# --- 5. MAIN / EXPORTED FUNCTION ---

def run_scraper(target_count=10, search_query=None):
    """
    Menjalankan scraper dengan target jumlah data tertentu (estimasi via halaman).
    1 Halaman Loker.id biasanya ~10-20 item. 
    Jadi kita hitung MAX_PAGES berdasarkan target_count.
    """
    start_time = time.time()
    
    # Estimasi 1 halaman = 15 data. 
    # Jika target 10, butuh 1 page. Jika target 30, butuh 2 page.
    max_pages = max(1, -(-target_count // 15)) # Ceiling division
    
    # Tahap 1: Harvest
    items = harvest_data(max_pages, search_query)
    
    # Potong sesuai target count jika berlebih
    items = items[:target_count]
    
    if not items: 
        return pd.DataFrame()

    print(f"🚀 Memproses detail untuk {len(items)} data...")
    results = []
    
    # Tahap 2: Detail Processing (Multi-thread)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = executor.map(process_single_item, items)
        for i, res in enumerate(futures):
            if res:
                results.append(res)
                if (i+1) % 5 == 0: print(f"   ...Selesai {i+1}/{len(items)}")

    # Tahap 3: Return DataFrame
    if results:
        df = pd.DataFrame(results)
        print(f"\n🎉 SUKSES! {len(df)} data berhasil diambil.")
        return df
    else:
        return pd.DataFrame()

if __name__ == "__main__":
    # Test Run
    df = run_scraper(target_count=5, search_query="python")
    print(df.head())

