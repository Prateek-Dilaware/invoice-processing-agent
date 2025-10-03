import os
import json
import re
from dotenv import load_dotenv
from groq import Groq

# ---------------------------
# Config
# ---------------------------
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")

INPUT_FILE = "data/outputs/extracted_content.txt"

if not API_KEY:
    raise ValueError("❌ GROQ_API_KEY not found in environment variables")

client = Groq(api_key=API_KEY)


# ---------------------------
# LLM Agent
# ---------------------------
class LLMValidatorAgent:
    def __init__(self, model_name: str = LLM_MODEL):
        self.model_name = model_name

    def validate_page(self, page_text: str) -> dict:
        system_prompt = (
            "You are an invoice validator.\n"
            "You will be given the text of one invoice page.\n\n"
            "Rules:\n"
            "1. If the page has both a Decoded QR Payload JSON block and the tax summary block, validate.\n"
            "2. Compare fields: SellerGstin, BuyerGstin, DocNo, DocDt, Irn, TotInvVal vs GrandTotal.\n\n"
            "3. If all match return JSON only:\n"
            '{"status":"validated","DocNo":"...","TotInvVal":..., "notes":"All fields match"}\n\n'
            "4. If mismatch return JSON only:\n"
            '{"status":"mismatch","DocNo":"...","errors":[{"field":"...","qr_value":...,"text_value":...}]}\n\n'
            '5. If the page does not have QR or tax summary, return:\n'
            '{"status":"error","message":"Incomplete invoice data"}\n\n'
            "Output strictly in JSON only."
        )
        try:
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": page_text}
                ],
                temperature=0.0,
            )
            raw_output = response.choices[0].message.content.strip()
            return json.loads(raw_output)
        except Exception as e:
            return {"status": "error", "message": str(e)}


# ---------------------------
# Utilities
# ---------------------------
def split_into_pages(content: str):
    return re.split(r"(?=########################################\n# Page \d+\n########################################)", content)


def insert_flag_to_page(page_text: str, flag: str) -> str:
    return page_text.strip() + "\n\n" + flag + "\n"


# ---------------------------
# Main
# ---------------------------
def append_validation():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    pages = split_into_pages(content)
    agent = LLMValidatorAgent()
    validated_pages = []

    invoice_counter = 0

    for page in pages:
        m = re.search(r"# Page (\d+)", page)
        if not m:
            validated_pages.append(page)
            continue

        page_num = int(m.group(1))
        if page_num % 5 == 0:  # only multiples of 5
            invoice_counter += 1
            result = agent.validate_page(page)

            if result.get("status") == "validated":
                flag = f"VALIDATION: VALID ✅ (DocNo: {result.get('DocNo')}, TotInvVal: {result.get('TotInvVal')})"
                print(f"Invoice {invoice_counter} validated (DocNo: {result.get('DocNo')})")
            elif result.get("status") == "mismatch":
                errors = result.get("errors", [])
                mismatch_info = ", ".join(
                    [f"{e['field']} mismatch" for e in errors]
                )
                flag = f"VALIDATION: NOT VALID ❌ (DocNo: {result.get('DocNo')} - {mismatch_info})"
                print(f"Invoice {invoice_counter} mismatch")
            else:
                flag = f"VALIDATION: ERROR ⚠️ ({result.get('message', 'Incomplete invoice data')})"
                print(f"Invoice {invoice_counter} error")

            page = insert_flag_to_page(page, flag)

        validated_pages.append(page)

    with open(INPUT_FILE, "w", encoding="utf-8") as f:
        f.write("".join(validated_pages))

    print(f"\n✅ Validation complete. Results appended directly into {INPUT_FILE}")


if __name__ == "__main__":
    append_validation()
