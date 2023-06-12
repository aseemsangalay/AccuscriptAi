import os
from flask import Flask, render_template, request, send_file
import fitz
from docx import Document
import re

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        # Check if a file was uploaded
        if "file" not in request.files:
            return render_template("index.html", error="No file uploaded.")
        
        file = request.files["file"]
        
        # Check if a file was selected
        if file.filename == "":
            return render_template("index.html", error="No file selected.")
        
        # Check if the file is a PDF
        if file.filename.endswith(".pdf"):
            # Save the uploaded file
            file_path = os.path.join("uploads", file.filename)
            file.save(file_path)
            
            # Extract the selected section
            section_to_extract = request.form["section"]
            extract_section(file_path, section_to_extract)
            
            # Generate the download link
            download_link = f"/download/{section_to_extract}.docx"
            
            return render_template("index.html", download_link=download_link)
        else:
            return render_template("index.html", error="Invalid file format. Please upload a PDF.")
    
    return render_template("index.html")

def extract_section(input_file, section_to_extract):
    # Read the content of the research paper PDF
    doc = fitz.open(input_file)
    num_pages = len(doc)
    text = ""
    for page in range(num_pages):
        page_text = doc[page].get_text()
        text += page_text

    # Define the end section markers with newline characters
    end_section_markers = {
        "introduction": r"(?<=\n)(Methods|MATERIALS AND METHODS)(?=\n|\nStudy Design)",
        "background": r"(?<=\n)Methods(?=\n|\nStudy Design)",
        "methods": r"(?<=\n)Results(?=\n|\nOutcomes)",
        "study design": r"(?<=\n)Results(?=\n|\nOutcomes)",
        "results": r"(?<=\n)Discussion(?=\n|\nConclusions)",
        "outcomes": r"(?<=\n)Discussion(?=\n|\nConclusions)",
        "discussion": r"(?<=\n)Conclusions(?=\n|\nReferences)",
        "conclusions": r"(?<=\n)Conclusions(?=\n|\nReferences)"
    }
    
    # Check if the start section is valid
    if section_to_extract.lower() not in end_section_markers:
        print("Invalid start section provided.")
        return

    # Get the end section marker for the start section
    end_section_marker = end_section_markers[section_to_extract.lower()]

    # Add newline characters to section and end section markers
    section_to_extract = f"\n{section_to_extract}\n"
    end_section_marker = f"\n{end_section_marker}\n"

    # Find the start and end sections using regular expressions
    section_start = re.search(section_to_extract, text, re.IGNORECASE)
    end_section = re.search(end_section_marker, text, re.IGNORECASE)

    if section_start is None:
        print(f"Section '{section_to_extract.strip()}' not found in the research paper.")
        return

    # Exclude the abstract section
    abstract_start = re.search(r"\n(abstract)\n", text, re.IGNORECASE)
    if abstract_start and abstract_start.start() < section_start.start():
        section_start = abstract_start

    # Determine the end index of the section
    section_end = end_section.start() if end_section else len(text)

    # Extract the content of the section
    section_text = text[section_start.start():section_end]

    # Clean up the section text
    section_text = re.sub(r'\s+', ' ', section_text)
    section_text = section_text.strip()

    # Create a new Word document
    output_document = Document()

    # Add the section content to the new document
    output_document.add_paragraph(section_text)

    # Save the new document
    output_path = os.path.join("downloads", f"{section_to_extract.strip()}.docx")
    output_document.save(output_path)

@app.route("/download/<filename>")
def download(filename):
    return send_file(f"downloads/{filename}", as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
