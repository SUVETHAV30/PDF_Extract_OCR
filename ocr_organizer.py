import json
import base64
import os
import re
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

def save_base64_image(base64_str: str, filename: str, output_dir: str = "extracted_images") -> str:
    """
    Save base64 encoded image to local file
    
    Args:
        base64_str: Base64 encoded image string
        filename: Name for the saved file
        output_dir: Directory to save images
    
    Returns:
        Path to saved image file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Remove data:image/jpeg;base64, prefix if present
    if base64_str.startswith('data:image'):
        base64_str = base64_str.split(',')[1]
    
    # Decode base64 string
    image_data = base64.b64decode(base64_str)
    
    # Save image file
    file_path = os.path.join(output_dir, filename)
    with open(file_path, 'wb') as f:
        f.write(image_data)
    
    return file_path

def extract_product_info_from_text(text: str) -> Dict[str, Any]:
    """
    Extract product information from OCR text using pattern matching
    
    Args:
        text: OCR extracted text
    
    Returns:
        Dictionary containing extracted product information
    """
    product_info = {
        "product_name": "",
        "product_description": "",
        "specifications": {},
        "features": [],
        "model_number": "",
        "brand": ""
    }
    
    lines = text.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for product name patterns (usually in caps or title case)
        if re.match(r'^[A-Z][A-Z\s\-0-9]{5,50}$', line) and not product_info["product_name"]:
            product_info["product_name"] = line
            
        # Look for model number patterns
        model_match = re.search(r'Model[:\s]+([A-Z0-9\-]+)', line, re.IGNORECASE)
        if model_match:
            product_info["model_number"] = model_match.group(1)
            
        # Look for brand patterns
        if re.search(r'Brand[:\s]+(\w+)', line, re.IGNORECASE):
            brand_match = re.search(r'Brand[:\s]+(\w+)', line, re.IGNORECASE)
            product_info["brand"] = brand_match.group(1)
            
        # Look for specifications (key: value patterns)
        spec_match = re.match(r'^([A-Za-z\s]+)[:]\s*(.+)$', line)
        if spec_match:
            key = spec_match.group(1).strip()
            value = spec_match.group(2).strip()
            product_info["specifications"][key] = value
            
        # Look for features (bullet points or numbered lists)
        if re.match(r'^[\•\-\*]\s*(.+)', line) or re.match(r'^\d+\.\s*(.+)', line):
            feature = re.sub(r'^[\•\-\*\d\.]\s*', '', line)
            product_info["features"].append(feature)
    
    # If no product name found, use first meaningful line
    if not product_info["product_name"] and lines:
        for line in lines:
            if len(line.strip()) > 10 and not line.strip().isdigit():
                product_info["product_name"] = line.strip()
                break
    
    # Create description from first few lines
    description_lines = []
    for line in lines[:10]:  # Take first 10 lines
        if line.strip() and len(line.strip()) > 20:
            description_lines.append(line.strip())
        if len(description_lines) >= 3:
            break
    
    product_info["product_description"] = " ".join(description_lines)
    
    return product_info

def extract_tables_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Extract table-like data from OCR text
    
    Args:
        text: OCR extracted text
    
    Returns:
        List of tables with headers and rows
    """
    tables = []
    lines = text.split('\n')
    
    current_table = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Detect table-like patterns (multiple columns separated by spaces/tabs)
        if '\t' in line or '  ' in line:  # Multiple spaces or tabs indicate columns
            columns = re.split(r'\s{2,}|\t', line)
            columns = [col.strip() for col in columns if col.strip()]
            
            if len(columns) >= 2:  # At least 2 columns
                if current_table is None:
                    current_table = {
                        "headers": columns,
                        "rows": []
                    }
                else:
                    current_table["rows"].append(columns)
        else:
            if current_table is not None:
                tables.append(current_table)
                current_table = None
    
    if current_table is not None:
        tables.append(current_table)
    
    return tables

def organize_ocr_response(ocr_response_dict: Dict[str, Any], pdf_filename: str) -> Dict[str, Any]:
    """
    Organize OCR response into structured product data
    
    Args:
        ocr_response_dict: Dictionary containing OCR response
        pdf_filename: Name of the original PDF file
    
    Returns:
        Organized product data dictionary
    """
    organized_data = {
        "source_pdf": pdf_filename,
        "extraction_timestamp": datetime.now().isoformat(),
        "products": [],
        "all_extracted_images": [],
        "metadata": {
            "total_pages": len(ocr_response_dict.get("pages", [])),
            "total_images": 0,
            "total_text_length": 0
        }
    }
    
    image_counter = 1
    all_text = ""
    
    for page_idx, page in enumerate(ocr_response_dict.get("pages", [])):
        page_text = page.get("markdown", "")
        all_text += page_text + "\n"
        
        # Extract and save images from this page
        page_images = []
        for image in page.get("images", []):
            image_filename = f"page_{page_idx + 1}_image_{image_counter}.jpg"
            
            # Save image locally
            try:
                saved_path = save_base64_image(
                    image.get("image_base64", ""), 
                    image_filename
                )
                
                image_info = {
                    "id": image.get("id", f"img_{image_counter}"),
                    "filename": image_filename,
                    "local_path": saved_path,
                    "base64_data": image.get("image_base64", ""),
                    "page_number": page_idx + 1,
                    "size_estimate": len(image.get("image_base64", "")) * 3 // 4  # Rough byte size
                }
                
                page_images.append(image_info)
                organized_data["all_extracted_images"].append(image_info)
                image_counter += 1
                
            except Exception as e:
                print(f"Error saving image {image_filename}: {e}")
    
    # Extract product information from combined text
    product_info = extract_product_info_from_text(all_text)
    
    # Extract tables
    tables = extract_tables_from_text(all_text)
    
    # Organize into product structure
    product_data = {
        "product_name": product_info["product_name"],
        "product_description": product_info["product_description"],
        "model_number": product_info["model_number"],
        "brand": product_info["brand"],
        "specifications": product_info["specifications"],
        "features": product_info["features"],
        "tables": tables,
        "product_images": [],
        "thumbnail_image": "",
        "all_page_images": organized_data["all_extracted_images"],
        "raw_text": all_text
    }
    
    # Assign first image as thumbnail and product image
    if organized_data["all_extracted_images"]:
        product_data["thumbnail_image"] = organized_data["all_extracted_images"][0]["local_path"]
        product_data["product_images"] = [img["local_path"] for img in organized_data["all_extracted_images"]]
    
    organized_data["products"].append(product_data)
    
    # Update metadata
    organized_data["metadata"]["total_images"] = len(organized_data["all_extracted_images"])
    organized_data["metadata"]["total_text_length"] = len(all_text)
    
    return organized_data

def save_organized_data(organized_data: Dict[str, Any], output_filename: str = "organized_product_data.json"):
    """
    Save organized data to JSON file
    
    Args:
        organized_data: Organized product data dictionary
        output_filename: Name of output JSON file
    """
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(organized_data, f, indent=4, ensure_ascii=False)
        print(f"Organized data saved to {output_filename}")
    except Exception as e:
        print(f"Error saving JSON file: {e}")

# Main processing function
def process_ocr_response(ocr_response_dict: Dict[str, Any], pdf_filename: str):
    """
    Main function to process OCR response and create organized output
    
    Args:
        ocr_response_dict: Dictionary containing OCR response
        pdf_filename: Name of the original PDF file
    """
    print("Processing OCR response...")
    
    # Organize the data
    organized_data = organize_ocr_response(ocr_response_dict, pdf_filename)
    
    # Save to JSON file
    output_filename = f"{Path(pdf_filename).stem}_organized_data.json"
    save_organized_data(organized_data, output_filename)
    
    # Print summary
    print(f"\n=== Processing Summary ===")
    print(f"Source PDF: {pdf_filename}")
    print(f"Total pages processed: {organized_data['metadata']['total_pages']}")
    print(f"Total images extracted: {organized_data['metadata']['total_images']}")
    print(f"Images saved to: ./extracted_images/")
    print(f"Organized data saved to: {output_filename}")
    
    if organized_data["products"]:
        product = organized_data["products"][0]
        print(f"\nProduct Information:")
        print(f"- Name: {product['product_name']}")
        print(f"- Model: {product['model_number']}")
        print(f"- Brand: {product['brand']}")
        print(f"- Specifications: {len(product['specifications'])} items")
        print(f"- Features: {len(product['features'])} items")
        print(f"- Tables: {len(product['tables'])} found")
    
    return organized_data

# Usage with your existing OCR response
if __name__ == "__main__":
    # Assuming you have 'response_dict' from your OCR processing
    # and 'pdf_file' path from your original code
    
    # Example usage:
    # organized_data = process_ocr_response(response_dict, str(pdf_file))
    
    print("Code ready! Use process_ocr_response(response_dict, pdf_filename) to organize your OCR data.")