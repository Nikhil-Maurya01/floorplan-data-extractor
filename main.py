import fitz  # PyMuPDF
import re
import json
from fractions import Fraction
import os

# ===============================
# CONFIGURATION
# ===============================
INPUT_PDF = "30x50-Model-landscape.pdf" # PDF to process
OUTPUT_JSON = "floorplan_data.json"   # Resulting structured data
OUTPUT_PDF = "floorplan_annotated.pdf" # Visual output with annotations

# ===============================
# HELPER FUNCTION: DIMENSION PARSER
# ===============================

def parse_dimension_to_inches(dim_str: str) -> float | None:
    """
    Converts a single dimension string (e.g., "10'", "8' 2\"", "6'6\"") 
    into a float value in inches.
    
    Tries a series of regex patterns in order to parse the most common formats.
    """
    if not dim_str:
        return None
    
    # Clean the string: remove ONLY leading/trailing hyphens and spaces.
    # We MUST KEEP the quotes (') and apostrophes (") as they are critical 
    # for telling the regex patterns what unit we're dealing with (feet vs. inches).
    cleaned_str = dim_str.strip().strip('- ')
    
    feet = 0.0
    inches = 0.0
    
    try:
        # P1: 8' 2 1/2"
        match = re.match(r"^(\d+)'\s*(\d+)\s+(\d+)/(\d+)\"?$", cleaned_str)
        if match:
            feet = float(match.group(1))
            inches = float(match.group(2))
            inches += float(Fraction(int(match.group(3)), int(match.group(4))))
            return feet * 12 + inches

        # P2: 8' 2"
        match = re.match(r"^(\d+)'\s*(\d+(\.\d+)?)\"?$", cleaned_str)
        if match:
            feet = float(match.group(1))
            inches = float(match.group(2))
            return feet * 12 + inches

        # P3: 6'6" (no space)
        match = re.match(r"^(\d+)'(\d+(\.\d+)?)\"?$", cleaned_str)
        if match:
            feet = float(match.group(1))
            inches = float(match.group(2))
            return feet * 12 + inches

        # P4: 20' or 10' or 8'
        match = re.match(r"^(\d+(\.\d+)?)\s*'$", cleaned_str)
        if match:
            feet = float(match.group(1))
            return feet * 12
            
        # P5: 6 1/2"
        match = re.match(r"^(\d+)\s+(\d+)/(\d+)\"?$", cleaned_str)
        if match:
            inches = float(match.group(1))
            inches += float(Fraction(int(match.group(2)), int(match.group(3))))
            return inches
            
        # P6: 6"
        match = re.match(r"^(\d+(\.\d+)?)\"?$", cleaned_str)
        if match:
            inches = float(match.group(1))
            return inches
            
    except Exception as e:
        print(f"Warning: Could not parse dimension '{dim_str}'. Error: {e}")
        return None
    
    # Fallback/Failure
    print(f"Warning: Failed to parse dimension '{dim_str}' with any pattern.")
    return None

# ===============================
# REGEX PATTERNS
# ===============================

# This is a pattern to find a *single* dimension string.
# It is a NON-CAPTURING group (?:...) so it can be nested
# inside other regexes without messing up the group capture order.
DIM_SINGLE_STR_PATTERN = r"(?:\d+'(?:(?:\s*\d*(?:\s+\d+/\d+)?)?\s*\"?)?|\d+(?:\s+\d+/\d+)?\s*\")"

# Regex for PASS 1: Find a complete room block
# This looks for "Room Name\nLength x Width"
ROOM_DIM_REGEX = re.compile(
    # Group 1: The Room Name (anything until a newline)
    r"^(.*?)\n" +
    # Group 2: The first dimension (captures the single pattern)
    rf"\s*({DIM_SINGLE_STR_PATTERN})\s*" +
    # The 'x' separator
    r"[xX]" +
    # Group 3: The second dimension (captures the single pattern)
    rf"\s*({DIM_SINGLE_STR_PATTERN})",
    re.MULTILINE # re.MULTILINE allows `^` to match the start of each line
)

# Regex for PASS 2: Find any standalone dimension string
PASS_2_DIM_REGEX = re.compile(f"({DIM_SINGLE_STR_PATTERN})")

# Regex for finding codes (e.g., OTS, DB24)
CODE_REGEX = re.compile(r"\b[A-Z]{1,2}\d{2,3}[A-Z]*\b|\b(OTS)\b")

# ===============================
# MAIN PROCESSING
# ===============================

def process_floorplan(pdf_path):
    """
    Main function to process the floorplan PDF.
    It reads the PDF, extracts data in two passes, saves a JSON,
    and saves an annotated PDF.
    """
    
    if not os.path.exists(pdf_path):
        print(f"Error: Input PDF not found at {pdf_path}")
        return

    doc = fitz.open(pdf_path)
    all_data = []

    print(f"Processing {pdf_path}...")

    for page_num in range(len(doc)):
        page = doc[page_num]
        
        page_data = {
            "page": page_num + 1,
            "rooms": [],
            "other_dimensions": [],
            "codes": set() # Use a set to automatically avoid duplicates
        }
        
        # Get all text blocks from the page
        text_blocks = page.get_text("blocks")
        
        # This set is the key to our 2-pass system.
        # It stores indices of blocks handled in Pass 1 to avoid reprocessing in Pass 2.
        processed_block_indices = set() 

        # --- PASS 1: Find Rooms ---
        # In this pass, we ONLY look for the full "Room Name \n 10' x 8'" pattern
        for i, block in enumerate(text_blocks):
            bbox = block[:4] # (x0, y0, x1, y1) coordinates
            text = block[4] # The text content
            
            # Search for the room pattern in this block's text
            match = ROOM_DIM_REGEX.search(text)
            
            if match:
                try:
                    name = match.group(1).strip()
                    dim1_str = match.group(2).strip()
                    dim2_str = match.group(3).strip()
                    
                    # Convert dimension strings (e.g., "10'") into inches (e.g., 120.0)
                    dim1_in = parse_dimension_to_inches(dim1_str)
                    dim2_in = parse_dimension_to_inches(dim2_str)
                    
                    # Both dimensions must parse correctly to be a "room"
                    if dim1_in is not None and dim2_in is not None:
                        page_data["rooms"].append({
                            "name": name,
                            "raw_text": f"{dim1_str} x {dim2_str}",
                            "length_in": dim1_in,
                            "width_in": dim2_in,
                            "bbox": bbox
                        })
                        
                        # Draw a GREEN box for successfully parsed rooms
                        rect = fitz.Rect(bbox)
                        page.draw_rect(rect, color=(0, 1, 0), width=1.5)
                        
                        # Mark this block as 'done' so Pass 2 skips it
                        processed_block_indices.add(i)
                    else:
                        # Print a debug message if parsing failed for a matched room
                        print(f"Debug: Failed to parse dimensions for room '{name}'. Dim1 ('{dim1_str}') -> {dim1_in}, Dim2 ('{dim2_str}') -> {dim2_in}")

                except Exception as e:
                    print(f"Warning: Regex exception processing room block: {e}\nText: {text}")

        # --- PASS 2: Find Other Dimensions & Codes ---
        # Loop through all blocks again, skipping any we already processed
        for i, block in enumerate(text_blocks):
            # *** This is the key: Skip any block already identified as a Room in Pass 1 ***
            if i in processed_block_indices:
                continue 

            bbox = block[:4]
            text = block[4]
            
            # Flags to decide what color to draw the annotation box
            found_something = False
            is_dim = False
            is_code = False

            # Find any single dimension
            for dim_match in PASS_2_DIM_REGEX.finditer(text):
                dim_str = dim_match.group(1).strip()
                dim_in = parse_dimension_to_inches(dim_str)
                
                if dim_in is not None:
                    page_data["other_dimensions"].append({
                        "raw": dim_str,
                        "inches": dim_in,
                        "bbox": bbox
                    })
                    found_something = True
                    is_dim = True

            # Find codes
            for code_match in CODE_REGEX.finditer(text):
                page_data["codes"].add(code_match.group(0))
                found_something = True
                is_code = True

            # If we found *anything* in this leftover block, draw a box
            if found_something:
                rect = fitz.Rect(bbox)
                # Red for dimensions, Blue for codes
                color = (1, 0, 0) if is_dim else (0, 0, 1) 
                page.draw_rect(rect, color=color, width=1)
                processed_block_indices.add(i)

        # Convert the set of codes to a list for JSON serialization
        page_data["codes"] = list(page_data["codes"])
        all_data.append(page_data)

    # --- SAVE RESULTS ---
    
    # Save the complete data to a JSON file
    # 'indent=4' makes the JSON file human-readable
    with open(OUTPUT_JSON, "w") as f:
        json.dump(all_data, f, indent=4)
    print(f"Successfully extracted data to {OUTPUT_JSON}")

    # Save the modified PDF with all the new annotations
    doc.save(OUTPUT_PDF)
    print(f"Successfully saved annotated PDF to {OUTPUT_PDF}")
    doc.close()


# This block ensures this code only runs when you execute the script directly
if __name__ == "__main__":
    
    # Clean up old output files to prevent PDF viewer caching issues
    if os.path.exists(OUTPUT_JSON):
        os.remove(OUTPUT_JSON)
    if os.path.exists(OUTPUT_PDF):
        os.remove(OUTPUT_PDF)
        
    # Run the main function
    process_floorplan(INPUT_PDF)
