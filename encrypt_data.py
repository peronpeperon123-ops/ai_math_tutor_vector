import os
import glob
from cryptography.fernet import Fernet

key = Fernet.generate_key()
f = Fernet(key)

kb_text = ""
search_pattern = os.path.join("transcriptions", "*平面ベクトル*.txt")
files = glob.glob(search_pattern)
files.sort()

for fpath in files:
    try:
        with open(fpath, "r", encoding="utf-8") as file:
            kb_text += f"\n\n--- ファイル: {os.path.basename(fpath)} ---\n\n"
            kb_text += file.read()
    except Exception:
        with open(fpath, "r", encoding="shift_jis", errors="ignore") as file:
            kb_text += f"\n\n--- ファイル: {os.path.basename(fpath)} ---\n\n"
            kb_text += file.read()

encrypted_data = f.encrypt(kb_text.encode('utf-8'))

with open("knowledge_base.enc", "wb") as output_file:
    output_file.write(encrypted_data)

print("---SUCCESS---")
print(f"DATA_KEY = \"{key.decode('utf-8')}\"")
print(f"Processed {len(files)} files.")
