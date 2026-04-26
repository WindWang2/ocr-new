import os
import glob
try:
    import docx
except ImportError:
    os.system("pip install python-docx")
    import docx

def extract_text_from_docx(file_path):
    try:
        doc = docx.Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    except Exception as e:
        return f"Error reading {file_path}: {e}"

def extract_text_from_doc(file_path):
    try:
        import win32com.client
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        abs_path = os.path.abspath(file_path)
        doc = word.Documents.Open(abs_path)
        text = doc.Content.Text
        doc.Close()
        word.Quit()
        return text
    except Exception as e:
        return f"Error reading {file_path}: {e}"

def main():
    docs_dir = os.path.join("docs", "exp-templates")
    files = glob.glob(os.path.join(docs_dir, "*.docx")) + glob.glob(os.path.join(docs_dir, "*.doc"))
    root_files = glob.glob("*.doc*")
    all_files = files + root_files
    
    for f in all_files:
        print(f"=== {f} ===")
        if f.endswith(".docx"):
            print(extract_text_from_docx(f)[:1500] + "...\n")
        elif f.endswith(".doc"):
            print(extract_text_from_doc(f)[:1500] + "...\n")

if __name__ == "__main__":
    main()
