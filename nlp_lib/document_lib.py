import traceback
import json
import requests

def get_summary(text):
    try:
        # log_block(text, "Input Text")
        payload = {"text": text, "format": "paragraph", "length_penalty": 0}
        url = r"https://www.semrush.com/goodcontent/api/generate-summary/"
        session = requests.Session()
        response = session.post(url, json=payload, verify=False)
        obj = json.loads(response.text)
        # log_block(format_json(obj))
        summary = obj.get("summary")
        # set_copied(summary)
    except:
        traceback.print_exc()


text = """

def get_summary(text): try: log_block(text, 'Input Text') payload = {"text": text, "format": "paragraph", "length_penalty": 0} url = r'https://www.semrush.com/goodcontent/api/generate-summary/' response = http_post(url, payload) obj = to_json(response.text) log_block(format_json(obj)) summary = obj.get('summary') set_copied(summary) except: traceback.print_exc()
"""
get_summary(text)
