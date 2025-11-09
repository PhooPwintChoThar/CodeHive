import os
import PyPDF2

def convert_pdf_to_txt(pdf_path: str, output_path: str = None) -> str:
    """
    Convert a single PDF file to text file
    
    Args:
        pdf_path: Path to the PDF file
        output_path: Path where to save the .txt file (optional)
    
    Returns:
        Path to the created .txt file
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    if not pdf_path.lower().endswith('.pdf'):
        raise ValueError(f"File must be a PDF: {pdf_path}")
    
    try:
        # Extract text from PDF
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            print(f"Extracting {num_pages} pages from {os.path.basename(pdf_path)}...")
            
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
        
        # Determine output path
        if output_path is None:
            output_path = pdf_path.replace('.pdf', '.txt')
        
        # Save to text file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        print(f"Successfully converted: {os.path.basename(pdf_path)} -> {os.path.basename(output_path)}")
        return output_path
        
    except Exception as e:
        raise RuntimeError(f"Error converting PDF: {e}")


def convert_all_pdfs_in_directory(directory_path: str, output_dir: str = None) -> list:
    """
    Convert all PDF files in a directory to text files
    
    Args:
        directory_path: Path to directory containing PDF files
        output_dir: Directory to save .txt files (optional, defaults to same directory)
    
    Returns:
        List of paths to created .txt files
    """
    if not os.path.isdir(directory_path):
        raise ValueError(f"Directory not found: {directory_path}")
    
    # Create output directory if specified and doesn't exist
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    pdf_files = [f for f in os.listdir(directory_path) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        raise ValueError(f"No PDF files found in directory: {directory_path}")
    
    converted_files = []
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(directory_path, pdf_file)
        
        if output_dir:
            txt_name = pdf_file.replace('.pdf', '.txt')
            output_path = os.path.join(output_dir, txt_name)
        else:
            output_path = None  # Save in same directory as PDF
        
        try:
            result = convert_pdf_to_txt(pdf_path, output_path)
            converted_files.append(result)
        except Exception as e:
            print(f"Error converting {pdf_file}: {e}")
    
    return converted_files


if __name__ == "__main__":
    # Example 1: Convert a single PDF
    # convert_pdf_to_txt("lectures/L07_Recursion.pdf")
    
    # Example 2: Convert all PDFs in a directory
    converted = convert_all_pdfs_in_directory("lectures/ComputerProgramming")
    print(f"\nTotal files converted: {len(converted)}")
    for file in converted:
        print(f"  - {file}")