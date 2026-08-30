import re
import requests
import urllib3
import pypdf

# Disable SSL warning since MWRD often has certificate issues
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MWRD_URL = "https://mwrdpravah.in/damsafety/control/pdfLatestReportEng"

# Mapping of keywords in dam names to clean display name and region
TARGET_DAMS = {
    "pune": {
        "khadakwasla": "Khadakwasla",
        "panshet": "Panshet",
        "warasgaon": "Warasgaon",
        "temghar": "Temghar",
        "pawana": "Pawana",
        "bhama askhed": "Bhama Askhed"
    },
    "mumbai": {
        "vaitarna h. e. p.": "Upper Vaitarna",
        "middle vaitarna": "Middle Vaitarna",
        "modaksagar": "Modak Sagar",
        "tansa": "Tansa",
        "bhatsa": "Bhatsa"
    }
}

# Matches: Sr.No Name Date Time Dead Live Gross LiveGrossToday PctToday PctLastYear
# E.g. '12 Khadakwasla 25/06/2026 08:06 AM 30.00 55.91 85.91 11.35 41.35 20.30 % 60.87 %'
DAM_LINE_REGEX = re.compile(
    r"(\d+)\s+([\w\s\.\(\)-]+?)\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2}\s+[AP]M)\s+"
    r"([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s+([\d\.]+)\s*%\s+([\d\.]+)\s*%"
)

def fetch_latest_pdf():
    """Downloads the latest PDF report from MWRD and returns the byte content."""
    res = requests.get(MWRD_URL, verify=False, timeout=30)
    res.raise_for_status()
    return res.content

def parse_report_pdf(pdf_bytes):
    """Parses MWRD PDF byte content and extracts target dam storage details."""
    import io
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    extracted_data = []

    for page_num in range(len(reader.pages)):
        text = reader.pages[page_num].extract_text()
        for line in text.split("\n"):
            m = DAM_LINE_REGEX.search(line)
            if not m:
                continue
            
            raw_name = m.group(2).strip()
            raw_name_lower = raw_name.lower()
            
            # Match dam with target list
            matched_region = None
            clean_name = None
            
            for region, dams in TARGET_DAMS.items():
                for kw, display_name in dams.items():
                    if kw in raw_name_lower:
                        matched_region = region
                        clean_name = display_name
                        break
                if matched_region:
                    break
            
            if matched_region:
                extracted_data.append({
                    "region": matched_region,
                    "name": clean_name,
                    "raw_name": raw_name,
                    "date": m.group(3),
                    "time": m.group(4),
                    "dead_storage": float(m.group(5)),
                    "live_storage_designed": float(m.group(6)),
                    "gross_storage_designed": float(m.group(7)),
                    "live_storage_today": float(m.group(8)),
                    "gross_storage_today": float(m.group(9)),
                    "percentage_today": float(m.group(10)),
                    "percentage_last_year": float(m.group(11))
                })
                
    return extracted_data

def get_current_lake_levels():
    """Utility function to fetch and parse in one step."""
    try:
        pdf_bytes = fetch_latest_pdf()
        return parse_report_pdf(pdf_bytes)
    except Exception as e:
        print(f"Error fetching/parsing MWRD report: {e}")
        return []
