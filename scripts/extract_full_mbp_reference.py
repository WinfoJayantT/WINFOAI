import os
import re
import json
import pymupdf

PDF_DIR = "Data for project"
OUTPUT_FILE = "config/oracle_mbp_reference.json"

pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
print(f"Found {len(pdf_files)} PDF files in {PDF_DIR}")

all_reference_flows = []

for pdf_name in sorted(pdf_files):
    pdf_path = os.path.join(PDF_DIR, pdf_name)
    domain_name = pdf_name.replace("mbp-", "").replace(".pdf", "").replace("-", " ").title()
    try:
        doc = pymupdf.open(pdf_path)
        print(f"Processing {pdf_name} ({len(doc)} pages)...")
        
        for page_idx, page in enumerate(doc):
            text = page.get_text()
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            
            # Identify process diagram pages
            # Usually contain "Oracle Modern Best Practice" and a process title
            if "Oracle Modern Best Practice" in text:
                # Find L1 Process name
                l1_process = None
                product_mix = None
                key_metrics = None
                
                # Check for Product Mix / Key Metrics
                m_prod = re.search(r"Product Mix:\s*(.*?)(?:\n|Key Metrics|Cloud|Mobile|$)", text, re.DOTALL)
                if m_prod:
                    product_mix = m_prod.group(1).strip().replace("\n", " ")
                
                m_metrics = re.search(r"Key Metrics:\s*(.*?)(?:\n|Cloud|Mobile|Analytics|$)", text, re.DOTALL)
                if m_metrics:
                    key_metrics = m_metrics.group(1).strip().replace("\n", " ")

                # Find line after 25A/25B/25C/25D or "Oracle Modern Best Practice"
                for idx, line in enumerate(lines):
                    if re.match(r"^2[0-9][A-D]$", line) and idx + 1 < len(lines):
                        candidate = lines[idx + 1]
                        if candidate not in ["Cloud", "Mobile", "Analytics", "AI/ML", "Product Mix:"]:
                            l1_process = candidate
                            break
                    elif line == "Oracle Modern Best Practice" and idx + 1 < len(lines):
                        if not re.match(r"^2[0-9][A-D]$", lines[idx + 1]):
                            candidate = lines[idx + 1]
                            if candidate not in ["Cloud", "Mobile", "Analytics", "AI/ML", "Product Mix:", "Digital Business Processes"]:
                                l1_process = candidate
                                break

                if not l1_process or len(l1_process) < 3 or l1_process.startswith("Digital Business") or "Copyright" in l1_process or "Oracle Modern" in l1_process:
                    continue

                # Now extract the L2 / L3 activity boxes on this page
                # In MBP PDFs, L2/L3 boxes have a bold title (2-4 words) followed by 1-3 sentences description
                activities = []
                
                # Blocks extraction for better grouping
                blocks = page.get_text("blocks")
                for b in blocks:
                    block_text = b[4].strip()
                    b_lines = [bl.strip() for bl in block_text.splitlines() if bl.strip()]
                    if not b_lines:
                        continue
                    first_line = b_lines[0]
                    # Filter out metadata blocks
                    if any(ig in first_line for ig in [
                        "Oracle Modern Best Practice", "25C", "25D", "25A", "25B", "Product Mix", 
                        "Key Metrics", "Copyright", "Cloud", "Mobile", "Analytics", "Collaboration", "AI/ML"
                    ]):
                        continue
                    if first_line == l1_process:
                        continue
                    
                    if len(b_lines) >= 2:
                        # Likely an L2/L3 activity with title and description
                        title = b_lines[0]
                        # Sometimes title is multi-line if short
                        desc_start = 1
                        if len(b_lines) >= 3 and len(b_lines[0].split()) <= 2 and len(b_lines[1].split()) <= 3:
                            title = f"{b_lines[0]} {b_lines[1]}"
                            desc_start = 2
                        desc = " ".join(b_lines[desc_start:])
                        
                        if len(desc) > 10 and not desc.startswith("Copyright"):
                            activities.append({
                                "activity_title": title,
                                "activity_description": desc
                            })

                if activities:
                    all_reference_flows.append({
                        "domain": domain_name,
                        "source_pdf": pdf_name,
                        "page_number": page_idx + 1,
                        "l1_process": l1_process,
                        "product_mix": product_mix,
                        "key_metrics": key_metrics,
                        "activities_l3_l4": activities
                    })

    except Exception as e:
        print(f"Error parsing {pdf_name}: {e}")

print(f"Extracted {len(all_reference_flows)} reference business process flows across all PDFs.")

# Save to config/oracle_mbp_reference.json
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(all_reference_flows, f, indent=2)

print(f"Saved to {OUTPUT_FILE} successfully!")
