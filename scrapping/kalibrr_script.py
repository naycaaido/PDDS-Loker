import time
import json
import re
import pandas as pd
import requests
import random
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 1. KONFIGURASI ---
# --- 1. KONFIGURASI ---
BASE_URL = "https://www.kalibrr.id/job-board/te/it/1"
# TARGET_DATA and OUTPUT_FILE are now parameters/handled externally
MAX_WORKERS = 2        # Thread worker

# --- 2. KAMUS DATA & HELPER ---
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
    """
    Menentukan kategori posisi berdasarkan judul pekerjaan
    """
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
    
# --- FUNGSI TEXT MINING SKILL ---
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

# --- 3. TAHAP 1: HARVEST URL (Sama seperti sebelumnya) ---
def harvest_data(target_count, search_query=None):
    print(f"🚜 HARVESTER: Mencari minimal {target_count} link valid...")
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    
    # Construct URL based on search
    if search_query:
        # Format: https://www.kalibrr.id/id-ID/home/i/it-and-software/te/{query}
        # Tambahan: kita bisa encode query jika perlu
        formatted_query = search_query.replace(" ", "-")
        target_url = f"https://www.kalibrr.id/id-ID/home/i/it-and-software/te/{formatted_query}"
        print(f"   🔎 Mode Pencarian: '{search_query}' -> {target_url}")
    else:
        # Default URL (IT Job Board)
        target_url = "https://www.kalibrr.id/job-board/te/it/1"
        print("   📂 Mode Default: List Lowongan IT")

    driver.get(target_url)
    time.sleep(3)
    
    harvested_items = []
    seen_urls = set()
    
    while len(harvested_items) < target_count:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Cari Card Container
        cards = soup.find_all("div", class_=lambda x: x and "k-bg-white" in x and "k-border-solid" in x and "k-rounded-lg" in x)
        
        added_this_round = 0
        for card in cards:
            try:
                title_tag = card.find("a", itemprop="name")
                if not title_tag: continue
                
                href = title_tag['href']
                posisi = title_tag.get_text(strip=True)
                
                if "/jobs/" in href and any(char.isdigit() for char in href):
                    full_url = f"https://www.kalibrr.id{href}" if href.startswith("/") else href
                    
                    if full_url not in seen_urls:
                        comp_tag = card.find("a", class_="k-text-subdued k-font-bold")
                        perusahaan = comp_tag.get_text(strip=True) if comp_tag else "N/A"
                        
                        loc_tag = card.find("span", class_="k-text-gray-500 k-block k-pointer-events-none")
                        lokasi = loc_tag.get_text(strip=True) if loc_tag else "Lokasi Lain"
                        
                        item = {
                            "link": full_url,
                            "posisi": posisi,
                            "perusahaan": perusahaan,
                            "lokasi": lokasi
                        }
                        
                        harvested_items.append(item)
                        seen_urls.add(full_url)
                        added_this_round += 1
            except Exception:
                continue
        
        print(f"   --> Total Data: {len(harvested_items)} (Baru: {added_this_round})")
        
        if len(harvested_items) >= target_count:
            break

        try:
            # Coba cari tombol Load More
            load_more_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Load more')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView();", load_more_btn)
            time.sleep(1)
            load_more_btn.click()
            time.sleep(2)
        except:
            # Jika tidak ada tombol Load More, mungkin pakai pagination tipe page number atau infinite scroll
            # Untuk search results Kalibrr, kadang tidak ada Load More, tapi pagination angka
            # Atau simply sudah habis
            print("⚠️ Load More tidak ditemukan atau habis. Mencoba scroll ke bawah...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Cek apakah ada data baru setelah scroll
            new_soup = BeautifulSoup(driver.page_source, "html.parser")
            new_cards = new_soup.find_all("div", class_=lambda x: x and "k-bg-white" in x and "k-border-solid" in x and "k-rounded-lg" in x)
            if len(new_cards) <= len(cards):
                 print("   [!] Tidak ada data baru setelah scroll. Stop.")
                 break
            
    driver.quit()
    final_items = harvested_items[:target_count]
    print(f"✅ HARVESTER SELESAI: {len(final_items)} data siap diproses detailnya.\n")
    return final_items

# --- 4. TAHAP 2: PROCESSING (UPDATE HTML PARSING) ---
def process_single_item(item):
    url = item['link']
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.google.com/'
        }
        time.sleep(random.uniform(0.5, 1.5))
        
        response = requests.get(url, headers=headers, timeout=15)
        
        # Default Data
        perusahaan = item['perusahaan']
        posisi = item['posisi']
        kota_raw = item['lokasi']
        gaji_angka = None
        deskripsi_full = ""
        pendidikan = "Tidak Disebutkan"
        jenis = "Full Time"

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 1. AMBIL DESKRIPSI & KUALIFIKASI (Untuk Skill Mining)
            # Cari div itemprop="description" DAN itemprop="qualifications"
            desc_div = soup.find("div", itemprop="description")
            qual_div = soup.find("div", itemprop="qualifications")
            
            desc_text = desc_div.get_text(separator=" ", strip=True) if desc_div else ""
            qual_text = qual_div.get_text(separator=" ", strip=True) if qual_div else ""
            
            # Gabungkan keduanya untuk text mining skill
            deskripsi_full = f"{desc_text} {qual_text}"

            # 2. AMBIL PENDIDIKAN (Dari tabel HTML <dl>)
            # Cari <dt> dengan text "Persyaratan tingkat pendidikan"
            # Note: Pakai lambda function di text=... agar case insensitive & partial match
            dt_pendidikan = soup.find("dt", string=lambda t: t and ("pendidikan" in t.lower() or "education" in t.lower()))
            
            if dt_pendidikan:
                # Ambil saudara selanjutnya (<dd>)
                dd_pendidikan = dt_pendidikan.find_next_sibling("dd")
                if dd_pendidikan:
                    pendidikan = dd_pendidikan.get_text(strip=True)

            # 3. AMBIL GAJI (Coba parsing dari JSON-LD jika ada, atau Next Data)
            # HTML Kalibrr menyembunyikan gaji di UI ("Gaji Tidak Diumumkan"), tapi kadang ada di JSON
            next_data = soup.find("script", id="__NEXT_DATA__")
            if next_data:
                try:
                    data = json.loads(next_data.string)
                    job_info = data.get('props', {}).get('pageProps', {}).get('job', {})
                    min_sal = job_info.get('minimum_salary')
                    max_sal = job_info.get('maximum_salary')
                    if min_sal:
                        gaji_angka = float(min_sal)
                        if max_sal: gaji_angka = (gaji_angka + float(max_sal)) / 2
                except: pass
        
        # --- FINAL CLEANING ---
        skills_found = extract_skills(deskripsi_full)
        provinsi = get_provinsi(kota_raw)
        
        kategori = determine_category(posisi)

        return {
            "Perusahaan": perusahaan,
            "Posisi": posisi,
            "kategori_posisi": kategori,
            "kota": kota_raw,
            "gaji_angka": gaji_angka,
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
    Menjalankan scraper dengan target jumlah data tertentu.
    Mengembalikan pandas DataFrame.
    """
    start_time = time.time()
    items = harvest_data(target_count, search_query)
    if not items:
        return pd.DataFrame() # Return empty DataFrame if nothing found

    print(f"🚀 Memproses detail untuk {len(items)} data...")
    results = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = executor.map(process_single_item, items)
        for i, res in enumerate(futures):
            if res:
                results.append(res)
                if (i+1) % 5 == 0: print(f"   ...Selesai {i+1}")

    if results:
        df = pd.DataFrame(results)
        print(f"\n🎉 SUKSES! {len(df)} data berhasil discraping.")
        return df
    else:
        return pd.DataFrame()

if __name__ == "__main__":
    # Test run direct execution
    df_result = run_scraper(5, search_query="python")
    print(df_result.head())
