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
    convert_pdf2img(first_pdf, 'first.png')
    convert_pdf2img(second_pdf, 'second.png')

    first = cv2.imread('converted/first.png')
    second = cv2.imread('converted/second.png')

    # shape to the same size
    second = cv2.resize(second, (first.shape[1], first.shape[0]), interpolation = cv2.INTER_AREA)

    # Convert images to grayscale
    first_gray = cv2.cvtColor(first, cv2.COLOR_BGR2GRAY)
    second_gray = cv2.cvtColor(second, cv2.COLOR_BGR2GRAY)

    # Compute SSIM between two images
    score, diff = structural_similarity(first_gray, second_gray, full=True)

    return score

    # The diff image contains the actual image differences between the two images
    # and is represented as a floating point data type so we must convert the array 
    # to 8-bit unsigned integers in the range [0,255] before we can use it with OpenCV
    # diff = (diff * 255).astype("uint8")

    # # Threshold the difference image, followed by finding contours to
    # # obtain the regions that differ between the two images
    # thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    # contours = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # contours = contours[0] if len(contours) == 2 else contours[1]

    # # Highlight differences
    # mask = np.zeros(first.shape, dtype='uint8')
    # filled = second.copy()
    #
    # for c in contours:
    #     area = cv2.contourArea(c)
    #     if area > 100:
    #         x,y,w,h = cv2.boundingRect(c)
    #         cv2.rectangle(first, (x, y), (x + w, y + h), (36,255,12), 2)
    #         cv2.rectangle(second, (x, y), (x + w, y + h), (36,255,12), 2)
    #         cv2.drawContours(mask, [c], 0, (0,255,0), -1)
    #         cv2.drawContours(filled, [c], 0, (0,255,0), -1)

    # cv2.imshow('first', first)
    # cv2.imshow('second', second)
    # cv2.imshow('diff', diff)
    # cv2.imshow('mask', mask)
    # cv2.imshow('filled', filled)
    # cv2.waitKey()

if __name__ == "__main__":
    first = "f1.pdf"
    second = "f2.pdf"
    score = pdf_similarity(first, second)
    print("Similarity Score: {:.3f}%".format(score * 100))
