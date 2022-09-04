from skimage.metrics import structural_similarity
import cv2
# import numpy as np

import fitz
import os


def convert_pdf2img(input_file: str, output_name: str):
    """Converts pdf to image and generates a file by page"""

    # Open the document
    pdfIn = fitz.open(input_file)

    if pdfIn.pageCount <= 0:
        return ""

    page = pdfIn[0] # first page

    if not os.path.exists('converted'):
        os.makedirs('converted')

    # zoom_x = 2
    # zoom_y = 2

    # mat = fitz.Matrix(zoom_x, zoom_y)
    # pix = page.getPixmap(matrix=mat, alpha=False)
    pix = page.getPixmap(alpha=False)
    pix.writePNG(os.path.join('converted/', output_name))
    
    pdfIn.close()

    return output_name


def pdf_similarity(first_pdf:str, second_pdf:str):
    first_content = convert_pdf2img(first_pdf, 'first.png')
    secont_content = convert_pdf2img(second_pdf, 'second.png')

    first = cv2.imread('converted/first.png')
    second = cv2.imread('converted/second.png')

    # shape to the same size
    second = cv2.resize(second, (first.shape[1], first.shape[0]), interpolation = cv2.INTER_AREA)

    # Convert images to grayscale
    first_gray = cv2.cvtColor(first, cv2.COLOR_BGR2GRAY)
    second_gray = cv2.cvtColor(second, cv2.COLOR_BGR2GRAY)

    # Compute SSIM between two images
    score, _ = structural_similarity(first_gray, second_gray, full=True)

    return score

if __name__ == "__main__":
    first = "f1.pdf"
    second = "f2.pdf"
    score = pdf_similarity(first, second)
    print("Similarity Score: {:.3f}%".format(score * 100))