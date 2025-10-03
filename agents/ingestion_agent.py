import fitz  # PyMuPDF
from pyzbar.pyzbar import decode
from PIL import Image
import io
import logging
import base64
import json
import os
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class PDFIngestionAgent:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    def extract_pdf_content(self) -> List[Dict[str, Any]]:
        """
        Extract text + QR codes (decoded) from each page of a PDF.
        Returns a list of page-level dictionaries.
        """
        all_pages_content = []
        try:
            doc = fitz.open(self.pdf_path)
        except Exception as e:
            logging.error(f"Could not open PDF file at '{self.pdf_path}'. Reason: {e}")
            return all_pages_content

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)

            # Extract text
            page_text = page.get_text("text") or ""

            # Extract QR codes (raw + decoded)
            raw_qrs = self._extract_qr_from_images(doc, page, page_num)
            unique_qrs = list(set(raw_qrs))  # deduplicate
            decoded_qrs = [self._decode_qr_jwt(qr) for qr in unique_qrs]

            page_content = {
                "page_number": page_num + 1,
                "text": page_text.strip(),
                "qr_codes_raw": unique_qrs,
                "qr_codes_decoded": decoded_qrs
            }
            all_pages_content.append(page_content)

        doc.close()
        return all_pages_content

    def _extract_qr_from_images(self, doc, page, page_num: int) -> List[str]:
        """Extract raw QR code strings from images in a page."""
        decoded_qr_codes = []
        image_list = page.get_images(full=True)

        for img_index, img in enumerate(image_list):
            xref = img[0]
            try:
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image = Image.open(io.BytesIO(image_bytes))
                decoded_objects = decode(image)

                for obj in decoded_objects:
                    qr_data = obj.data.decode("utf-8")
                    decoded_qr_codes.append(qr_data)
            except Exception as e:
                logging.warning(
                    f"Could not process image {img_index + 1} on page {page_num + 1}. Error: {e}"
                )
        return decoded_qr_codes

    def _decode_qr_jwt(self, qr_string: str) -> Dict[str, Any]:
        """Decode a JWT-like QR string (Base64 payload → JSON)."""
        try:
            parts = qr_string.split(".")
            if len(parts) != 3:
                return {"error": "Not a valid JWT format"}

            payload = parts[1] + "=" * (-len(parts[1]) % 4)  # pad base64
            decoded_bytes = base64.urlsafe_b64decode(payload)
            decoded_json = json.loads(decoded_bytes.decode("utf-8"))

            # If "data" is a JSON string, parse it into dict
            if isinstance(decoded_json.get("data"), str):
                try:
                    decoded_json["data"] = json.loads(decoded_json["data"])
                except json.JSONDecodeError:
                    pass  # keep as string if parsing fails

            return decoded_json
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    invoices_dir = "data/invoices"
    output_file_path = "data/outputs/extracted_content.txt"

    # Ensure outputs folder exists
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    # Start fresh (overwrite old file)
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write("")

    # Walk through invoices folder & process all PDFs
    for root, _, files in os.walk(invoices_dir):
        for file_name in files:
            if file_name.lower().endswith(".pdf"):
                pdf_path = os.path.join(root, file_name)
                logging.info(f"📄 Processing invoice: {pdf_path}")

                agent = PDFIngestionAgent(pdf_path)
                pdf_content = agent.extract_pdf_content()

                if pdf_content:
                    with open(output_file_path, "a", encoding="utf-8") as f:
                        f.write(f"\n=== Extracted from {file_name} ===\n")
                        f.write("--- Successfully Extracted PDF Content ---\n")
                        for page_data in pdf_content:
                            f.write(
                                "\n" + "#"*40 + f"\n# Page {page_data['page_number']}\n" + "#"*40 + "\n"
                            )

                            if page_data['qr_codes_raw']:
                                f.write("\n[--- QR Code(s) Found ---]\n")
                                for i, qr_data in enumerate(page_data['qr_codes_raw']):
                                    f.write(f"  QR Code {i + 1}: {qr_data}\n")
                                f.write("[--------------------------]\n\n")

                                f.write("[--- Decoded QR Payload(s) ---]\n")
                                for decoded in page_data['qr_codes_decoded']:
                                    f.write(json.dumps(decoded, indent=4) + "\n")
                                f.write("[-----------------------------]\n\n")
                            else:
                                f.write("\n[--- No QR Codes Found ---]\n\n")

                            f.write("[--- Text Content ---]\n")
                            f.write(page_data['text'] + "\n")
                            f.write("[--------------------]\n")
                else:
                    logging.warning(f"No content extracted from {pdf_path}")

    logging.info(f"✅ Extraction complete. Results saved in '{output_file_path}'")
