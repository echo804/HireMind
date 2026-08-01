import fitz
doc = fitz.open("/mnt/d/codexproject/codexproject/HireMind/.reasonix/attachments/clipboard-20260729-144000.356707-000002.pdf")
for page in doc:
    print(page.get_text())
