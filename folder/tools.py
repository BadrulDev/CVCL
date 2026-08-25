import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def make_pdf_document(filename: str, title: str, content: str) -> str:
    """
    Generates a PDF document inside a folder named after the title.
    
    Args:
        filename: Name of the output PDF file (e.g., 'report.pdf').
        title: The main heading for the document (used to create the folder name).
        content: The detailed body text/paragraphs for the PDF.
    """
    # 1. Clean title to create a safe folder name (removes invalid path characters)
    folder_name = re.sub(r'[\\/*?:"<>|]', "", title).strip().replace(" ", "_")
    
    # 2. Create the folder if it does not already exist
    os.makedirs(folder_name, exist_ok=True)
    
    # 3. Combine folder path and filename
    file_path = os.path.join(folder_name, filename)

    # 4. Generate the PDF inside the folder
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=15
    )
    body_style = styles['BodyText']
    body_style.fontSize = 11
    body_style.leading = 14

    story = [
        Paragraph(title, title_style),
        Spacer(1, 10)
    ]

    for para in content.split("\n\n"):
        if para.strip():
            story.append(Paragraph(para.replace("\n", " "), body_style))
            story.append(Spacer(1, 10))

    doc.build(story)
    return f"Successfully generated PDF at: {os.path.abspath(file_path)}"