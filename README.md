# PDF Floorplan Data Extractor (Python + PyMuPDF + Regex)

![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg?style=for-the-badge&logo=python&logoColor=ffdd54)
![PyMuPDF](https://img.shields.io/badge/PyMuPDF-fitz-blue.svg?style=for-the-badge&logo=adobe&logoColor=white)
![Regex](https://img.shields.io/badge/Regex-Parsing-red.svg?style=for-the-badge&logo=grep&logoColor=white)
![JSON](https://img.shields.io/badge/Output-JSON-yellow.svg?style=for-the-badge&logo=json&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)

A powerful Python script that extracts structured data from **unstructured floorplan PDFs**. It parses room names and dimensions using **Regex**, converts them to a standard format, and saves the output as a clean **JSON** file.

The script also generates a visual **annotated PDF** to verify the extraction results, drawing bounding boxes around all identified data.

---

## ✨ Highlights

-   **Intelligent 2-Pass Parsing**: A smart extraction logic that first looks for complete "Room" blocks (Name + Dimensions) and then does a second pass to find "Other" dimensions (like overall plan size) and codes (like "OTS").
-   **Robust Regex Parser**: A custom helper function that can parse a wide variety of dimension formats (e.g., `10' 8"`, `10'`, `8' 2 1/2"`, `6'6"`) into standardized inches.
-   **PDF ➜ JSON Pipeline**: An end-to-end "ETL" process that reads a raw PDF, transforms the text, and loads the structured data into a machine-readable JSON file.
-   **Visual Verification**: Automatically generates a new, annotated PDF (`floorplan_annotated.pdf`) that visually confirms what data was extracted and how it was classified.

---

## ⚙️ Tech Stack & Libraries
-   **Python 3.9+**
-   **PyMuPDF (fitz)**: For reading PDF text blocks and drawing annotations.
-   **Regex (re)**: For all pattern-matching and data extraction.
-   **JSON**: For standard structured data output.

---

## 🚀 How to Use

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/Nikhil-Maurya01/floorplan-data-extractor.git](https://github.com/Nikhil-Maurya01/floorplan-data-extractor.git)
    cd floorplan-data-extractor
    ```

2.  **Install dependencies:**
    ```bash
    # Create and activate a virtual environment (Recommended)
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

    # Install requirements
    pip install PyMuPDF
    ```

3.  **Place your PDF:**
    Add your floorplan PDF (e.g., `my_plan.pdf`) to the root folder.

4.  **Update the script:**
    Change the `INPUT_PDF` variable in `main.py` to match your file's name.

    ```python
    # main.py
    INPUT_PDF = "my_plan.pdf"
    ```

5.  **Run the extractor:**
    ```bash
    python main.py
    ```

6.  **Check the results!**
    You will find two new files in your folder:
    -   `floorplan_data.json`: The clean, structured data.
    -   `floorplan_annotated.pdf`: The visual verification PDF.

---

## 🤖 Visual Extraction Results

To verify the accuracy of the parser, the script automatically generates an annotated PDF. This visual output draws bounding boxes around all the text blocks it successfully processed.

The color-coded boxes make it easy to debug and understand the output:

-   **<span style="color:green">GREEN BOX</span>**: A complete **'Room'** block (e.g., "Bed Room\n10' x 8'") was successfully found and parsed.
-   **<span style="color:red">RED BOX</span>**: A standalone **'Dimension'** string was found (e.g., overall plan dimensions like `45'`).
-   **<span style="color:blue">BLUE BOX</span>**: A **'Code'** (like `OTS`) was identified.

*(Your annotated PDF output will look something like this:)*
![Annotated PDF Output](httpsor://storage.googleapis.com/aai-web-assist-public-data/floorplan_annotated_v2.png)

### Corresponding JSON Output

This visual map corresponds directly to the `floorplan_data.json` file, which structures this data. A single "room" object from the JSON (like the green-boxed "Kitchen") will look like this:

<details>
  <summary>Click to expand JSON output snippet</summary>
  
  ```json
  [
    {
      "page": 1,
      "rooms": [
        {
          "name": "Bed Room",
          "raw_text": "10' x 8' 2\"",
          "length_in": 120.0,
          "width_in": 98.0,
          "bbox": [
            194.5999298095703,
            128.33340454101562,
            303.8824768066406,
            173.2695770263672
          ]
        },
        {
          "name": "Kitchen",
          "raw_text": "7' 6\" x 8' 2\"",
          "length_in": 90.0,
          "width_in": 98.0,
          "bbox": [
            185.83998107910156,
            583.2529907226562,
            277.1622314453125,
            625.5492553710938
          ]
        }
      ],
      "other_dimensions": [
        {
          "raw": "20'",
          "inches": 240.0,
          "bbox": [
            266.36883544921875,
            48.145103454589844,
            333.91131591796875,
            70.60836029052734
          ]
        }
      ],
      "codes": [
        "OTS"
      ]
    }
  ]
