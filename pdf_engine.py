
# -*- coding: utf-8 -*-
"""
PDF Engine: Unified interface for PDF processing (Final Version)
"""
import io
from pypdf import PdfReader, PdfWriter
from PIL import Image

def process(task_type, file_bytes, **kwargs):
    """
    Unified entry point for all PDF operations.
    Args:
        task_type (str): e.g. 'merge', 'split', 'remove_links', ...
        file_bytes (BytesIO): input PDF as BytesIO
        kwargs: extra params for some tools
    Returns:
        BytesIO: processed PDF as BytesIO
    """
    if task_type == "remove_links":
        return remove_links(file_bytes)
    elif task_type == "merge":
        return merge_pdfs([file_bytes])
    elif task_type == "remove_pages":
        pages = kwargs.get('pages')
        return remove_pages(file_bytes, pages)
    elif task_type == "rotate":
        angle = kwargs.get('angle', 90)
        pages = kwargs.get('pages')
        return rotate_pages(file_bytes, angle, pages)
    elif task_type == "compress":
        return compress_pdf(file_bytes)
    else:
        raise NotImplementedError(f"Unknown task_type: {task_type}")

def remove_links(file_bytes):
    reader = PdfReader(file_bytes)
    writer = PdfWriter()
    for page in reader.pages:
        # إزالة الروابط من الصفحة
        if "/Annots" in page:
            annots = page["/Annots"]
            new_annots = []
            for annot in annots:
                obj = annot.get_object()
                subtype = obj.get("/Subtype")
                if subtype != "/Link":
                    new_annots.append(annot)
            if new_annots:
                page["/Annots"] = new_annots
            else:
                del page["/Annots"]
        writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out

def merge_pdfs(files):
    writer = PdfWriter()
    for f in files:
        f.seek(0)
        reader = PdfReader(f)
        for page in reader.pages:
            writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out

def remove_pages(file_bytes, pages):
    """pages: string like '2,4-6'"""
    reader = PdfReader(file_bytes)
    writer = PdfWriter()
    total = len(reader.pages)
    to_remove = set()
    if pages:
        for part in str(pages).split(','):
            if '-' in part:
                a, b = part.split('-')
                to_remove.update(range(int(a)-1, int(b)))
            else:
                to_remove.add(int(part)-1)
    for i, page in enumerate(reader.pages):
        if i not in to_remove:
            writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out

def rotate_pages(file_bytes, angle=90, pages=None):
    reader = PdfReader(file_bytes)
    writer = PdfWriter()
    total = len(reader.pages)
    rotate_set = set()
    if pages:
        for part in str(pages).split(','):
            if '-' in part:
                a, b = part.split('-')
                rotate_set.update(range(int(a)-1, int(b)))
            else:
                rotate_set.add(int(part)-1)
    for i, page in enumerate(reader.pages):
        if not pages or i in rotate_set:
            page.rotate(angle)
        writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out

def compress_pdf(file_bytes):
    # ضغط بسيط: إعادة حفظ الصفحات (لا ضغط صور متقدم)
    reader = PdfReader(file_bytes)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    out = io.BytesIO()
    writer.write(out, compress=True)
    out.seek(0)
    return out
