import PyPDF2
import tkinter as tk
from tkinter import filedialog, messagebox

def split_pdf(file_path, output_folder):
    try:
        with open(file_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            for page_num in range(len(reader.pages)):
                writer = PyPDF2.PdfWriter()
                writer.add_page(reader.pages[page_num])
                
                output_path = f"{output_folder}/page_{page_num + 1}.pdf"
                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)
                print(f"Page {page_num + 1} saved as {output_path}")
        messagebox.showinfo("Success", "PDF successfully split into individual pages.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if file_path:
        file_entry.delete(0, tk.END)
        file_entry.insert(0, file_path)

def select_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        folder_entry.delete(0, tk.END)
        folder_entry.insert(0, folder_path)

def split_pdf_gui():
    file_path = file_entry.get()
    output_folder = folder_entry.get()
    if not file_path or not output_folder:
        messagebox.showwarning("Input required", "Please select both a PDF file and an output folder.")
        return
    split_pdf(file_path, output_folder)

# Создание основного окна
root = tk.Tk()
root.title("PDF Splitter")

# Поле для ввода пути к файлу
file_label = tk.Label(root, text="PDF file:")
file_label.grid(row=0, column=0, padx=10, pady=10)

file_entry = tk.Entry(root, width=50)
file_entry.grid(row=0, column=1, padx=10, pady=10)

file_button = tk.Button(root, text="Browse...", command=select_file)
file_button.grid(row=0, column=2, padx=10, pady=10)

# Поле для ввода пути к папке
folder_label = tk.Label(root, text="Output folder:")
folder_label.grid(row=1, column=0, padx=10, pady=10)

folder_entry = tk.Entry(root, width=50)
folder_entry.grid(row=1, column=1, padx=10, pady=10)

folder_button = tk.Button(root, text="Browse...", command=select_folder)
folder_button.grid(row=1, column=2, padx=10, pady=10)

# Кнопка для запуска разделения PDF
split_button = tk.Button(root, text="Split PDF", command=split_pdf_gui)
split_button.grid(row=2, column=0, columnspan=3, pady=20)

# Запуск основного цикла
root.mainloop()
