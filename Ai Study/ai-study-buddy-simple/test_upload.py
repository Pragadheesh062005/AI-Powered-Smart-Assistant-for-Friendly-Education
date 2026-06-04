import requests
import time

def test():
    # 1. Upload PDF
    print("Uploading PDF...")
    with open("dummy.pdf", "rb") as f:
        res = requests.post("http://127.0.0.1:5000/upload", files={"pdf_file": f})
        print(res.status_code, res.json())
        if res.status_code != 200:
            return
            
    # 2. Ask Question
    print("Asking question...")
    res = requests.post("http://127.0.0.1:5000/ask", json={"question": "What is in this document?"})
    print(res.status_code, res.json())

if __name__ == "__main__":
    test()
