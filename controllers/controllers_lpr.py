from odoo import http,modules
import cv2
import numpy as np
import math
import logging
import base64
import os
cwd = os.getcwd()

classifications_txt_path = modules.module.get_resource_path(
    'parking_odoo',
    'static/file',
    'classifications.txt'
)
flattened_images_txt_path = modules.module.get_resource_path(
    'parking_odoo',
    'static/file',
    'flattened_images.txt'
)


_logger = logging.getLogger(__name__)
ADAPTIVE_THRESH_BLOCK_SIZE = 19
ADAPTIVE_THRESH_WEIGHT = 9

n = 1

Min_char = 0.01
Max_char = 0.09

RESIZED_IMAGE_WIDTH = 20
RESIZED_IMAGE_HEIGHT = 30


# module level variables ##########################################################################
GAUSSIAN_SMOOTH_FILTER_SIZE = (5, 5)  # kích cỡ càng to thì càng mờ
ADAPTIVE_THRESH_BLOCK_SIZE = 19
ADAPTIVE_THRESH_WEIGHT = 9

###################################################################################################

######## Upload KNN model ######################
npaClassifications = np.loadtxt(
    classifications_txt_path, np.float32)
npaFlattenedImages = np.loadtxt(
    flattened_images_txt_path, np.float32)
npaClassifications = npaClassifications.reshape(
    # reshape numpy array to 1d, necessary to pass to call to train
    (npaClassifications.size, 1))
kNearest = cv2.ml.KNearest_create()  # instantiate KNN object
kNearest.train(npaFlattenedImages, cv2.ml.ROW_SAMPLE, npaClassifications)
#########################


def preprocess(imgOriginal):

    imgGrayscale = extractValue(imgOriginal)
    # imgGrayscale = cv2.cvtColor(imgOriginal,cv2.COLOR_BGR2GRAY) nên dùng hệ màu HSV
    # Trả về giá trị cường độ sáng ==> ảnh gray
    # để làm nổi bật biển số hơn, dễ tách khỏi nền
    imgMaxContrastGrayscale = maximizeContrast(imgGrayscale)
    # cv2.imwrite("imgGrayscalePlusTopHatMinusBlackHat.jpg",imgMaxContrastGrayscale)
    height, width = imgGrayscale.shape

    imgBlurred = np.zeros((height, width, 1), np.uint8)
    imgBlurred = cv2.GaussianBlur(
        imgMaxContrastGrayscale, GAUSSIAN_SMOOTH_FILTER_SIZE, 0)
    # cv2.imwrite("gauss.jpg",imgBlurred)
    # Làm mịn ảnh bằng bộ lọc Gauss 5x5, sigma = 0

    imgThresh = cv2.adaptiveThreshold(imgBlurred, 255.0, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                      cv2.THRESH_BINARY_INV, ADAPTIVE_THRESH_BLOCK_SIZE, ADAPTIVE_THRESH_WEIGHT)

    # Tạo ảnh nhị phân
    return imgGrayscale, imgThresh
# Trả về ảnh xám và ảnh nhị phân
# end function

###################################################################################################


def extractValue(imgOriginal):
    height, width, numChannels = imgOriginal.shape
    imgHSV = np.zeros((height, width, 3), np.uint8)
    imgHSV = cv2.cvtColor(imgOriginal, cv2.COLOR_BGR2HSV)

    imgHue, imgSaturation, imgValue = cv2.split(imgHSV)

    # màu sắc, độ bão hòa, giá trị cường độ sáng
    # Không chọn màu RBG vì vd ảnh màu đỏ sẽ còn lẫn các màu khác nữa nên khó xđ ra "một màu"
    return imgValue
# end function

###################################################################################################


def maximizeContrast(imgGrayscale):
    # Làm cho độ tương phản lớn nhất
    height, width = imgGrayscale.shape

    imgTopHat = np.zeros((height, width, 1), np.uint8)
    imgBlackHat = np.zeros((height, width, 1), np.uint8)
    structuringElement = cv2.getStructuringElement(
        cv2.MORPH_RECT, (3, 3))  # tạo bộ lọc kernel

    # nổi bật chi tiết sáng trong nền tối
    imgTopHat = cv2.morphologyEx(
        imgGrayscale, cv2.MORPH_TOPHAT, structuringElement, iterations=10)
    # cv2.imwrite("tophat.jpg",imgTopHat)
    # Nổi bật chi tiết tối trong nền sáng
    imgBlackHat = cv2.morphologyEx(
        imgGrayscale, cv2.MORPH_BLACKHAT, structuringElement, iterations=10)
    # cv2.imwrite("blackhat.jpg",imgBlackHat)
    imgGrayscalePlusTopHat = cv2.add(imgGrayscale, imgTopHat)
    imgGrayscalePlusTopHatMinusBlackHat = cv2.subtract(
        imgGrayscalePlusTopHat, imgBlackHat)

    # cv2.imshow("imgGrayscalePlusTopHatMinusBlackHat",imgGrayscalePlusTopHatMinusBlackHat)
    # Kết quả cuối là ảnh đã tăng độ tương phản
    return imgGrayscalePlusTopHatMinusBlackHat
# end function


def testImage(img):
    ################ Image Preprocessing #################
    imgGrayscaleplate, imgThreshplate = preprocess(img)
    canny_image = cv2.Canny(imgThreshplate, 250, 255)  # Canny Edge
    kernel = np.ones((3, 3), np.uint8)
    dilated_image = cv2.dilate(canny_image, kernel, iterations=1)  # Dilation
    # cv2.imshow("dilated_image",dilated_image)

    ###########################################

    ###### Draw contour and filter out the license plate  #############
    contours, hierarchy = cv2.findContours(
        dilated_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[
        :10]  # Lấy 10 contours có diện tích lớn nhất
    # cv2.drawContours(img, contours, -1, (255, 0, 255), 3) # Vẽ tất cả các ctour trong hình lớn

    screenCnt = []
    for c in contours:
        peri = cv2.arcLength(c, True)  # Tính chu vi
        # làm xấp xỉ đa giác, chỉ giữ contour có 4 cạnh
        approx = cv2.approxPolyDP(c, 0.06 * peri, True)
        [x, y, w, h] = cv2.boundingRect(approx.copy())
        ratio = w / h
        # cv2.putText(img, str(len(approx.copy())), (x,y),cv2.FONT_HERSHEY_DUPLEX, 2, (0, 255, 0), 3)
        # cv2.putText(img, str(ratio), (x,y),cv2.FONT_HERSHEY_DUPLEX, 2, (0, 255, 0), 3)
        if (len(approx) == 4):
            screenCnt.append(approx)

            cv2.putText(img, str(len(approx.copy())), (x, y),
                        cv2.FONT_HERSHEY_DUPLEX, 2, (0, 255, 0), 3)

    if screenCnt is None:
        detected = 0
        return "No plate detected"
    else:
        detected = 1

    if detected == 1:
        for screenCnt in screenCnt:
            # Khoanh vùng biển số xe
            cv2.drawContours(img, [screenCnt], -1, (0, 255, 0), 3)

            ############## Find the angle of the license plate #####################
            (x1, y1) = screenCnt[0, 0]
            (x2, y2) = screenCnt[1, 0]
            (x3, y3) = screenCnt[2, 0]
            (x4, y4) = screenCnt[3, 0]
            array = [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
            sorted_array = array.sort(reverse=True, key=lambda x: x[1])
            (x1, y1) = array[0]
            (x2, y2) = array[1]
            doi = abs(y1 - y2)
            ke = abs(x1 - x2)
            angle = math.atan(doi / ke) * (180.0 / math.pi)

            ####################################

            ########## Crop out the license plate and align it to the right angle ################

            mask = np.zeros(imgGrayscaleplate.shape, np.uint8)
            new_image = cv2.drawContours(mask, [screenCnt], 0, 255, -1, )
            # cv2.imshow("new_image",new_image)

            # Cropping
            (x, y) = np.where(mask == 255)
            (topx, topy) = (np.min(x), np.min(y))
            (bottomx, bottomy) = (np.max(x), np.max(y))

            roi = img[topx:bottomx, topy:bottomy]
            imgThresh = imgThreshplate[topx:bottomx, topy:bottomy]
            ptPlateCenter = (bottomx - topx) / 2, (bottomy - topy) / 2

            if x1 < x2:
                rotationMatrix = cv2.getRotationMatrix2D(
                    ptPlateCenter, -angle, 1.0)
            else:
                rotationMatrix = cv2.getRotationMatrix2D(
                    ptPlateCenter, angle, 1.0)

            roi = cv2.warpAffine(roi, rotationMatrix,
                                 (bottomy - topy, bottomx - topx))
            imgThresh = cv2.warpAffine(
                imgThresh, rotationMatrix, (bottomy - topy, bottomx - topx))
            roi = cv2.resize(roi, (0, 0), fx=3, fy=3)
            imgThresh = cv2.resize(imgThresh, (0, 0), fx=3, fy=3)

            ####################################

            #################### Prepocessing and Character segmentation ####################
            kerel3 = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            thre_mor = cv2.morphologyEx(imgThresh, cv2.MORPH_DILATE, kerel3)
            cont, hier = cv2.findContours(
                thre_mor, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # cv2.imshow(str(n + 20), thre_mor)
            # Vẽ contour các kí tự trong biển số
            cv2.drawContours(roi, cont, -1, (100, 255, 255), 2)

            ##################### Filter out characters #################
            char_x_ind = {}
            char_x = []
            height, width, _ = roi.shape
            roiarea = height * width

            for ind, cnt in enumerate(cont):
                (x, y, w, h) = cv2.boundingRect(cont[ind])
                ratiochar = w / h
                char_area = w * h
                # cv2.putText(roi, str(char_area), (x, y+20),cv2.FONT_HERSHEY_DUPLEX, 2, (255, 255, 0), 2)
                # cv2.putText(roi, str(ratiochar), (x, y+20),cv2.FONT_HERSHEY_DUPLEX, 2, (255, 255, 0), 2)

                if (Min_char * roiarea < char_area < Max_char * roiarea) and (0.25 < ratiochar < 0.7):
                    if x in char_x:  # Sử dụng để dù cho trùng x vẫn vẽ được
                        x = x + 1
                    char_x.append(x)
                    char_x_ind[x] = ind

                    # cv2.putText(roi, str(char_area), (x, y+20),cv2.FONT_HERSHEY_DUPLEX, 2, (255, 255, 0), 2)

            ############ Character recognition ##########################

            char_x = sorted(char_x)
            strFinalString = ""
            first_line = ""
            second_line = ""

            for i in char_x:
                (x, y, w, h) = cv2.boundingRect(cont[char_x_ind[i]])
                cv2.rectangle(roi, (x, y), (x + w, y + h), (0, 255, 0), 2)

                imgROI = thre_mor[y:y + h, x:x + w]  # Crop the characters

                imgROIResized = cv2.resize(
                    # resize image
                    imgROI, (RESIZED_IMAGE_WIDTH, RESIZED_IMAGE_HEIGHT))
                npaROIResized = imgROIResized.reshape(
                    (1, RESIZED_IMAGE_WIDTH * RESIZED_IMAGE_HEIGHT))

                npaROIResized = np.float32(npaROIResized)
                _, npaResults, neigh_resp, dists = kNearest.findNearest(
                    npaROIResized, k=3)  # call KNN function find_nearest;
                # ASCII of characters
                strCurrentChar = str(chr(int(npaResults[0][0])))
                cv2.putText(roi, strCurrentChar, (x, y + 50),
                            cv2.FONT_HERSHEY_DUPLEX, 2, (255, 255, 0), 3)

                if (y < height / 3):  # decide 1 or 2-line license plate
                    first_line = first_line + strCurrentChar
                else:
                    second_line = second_line + strCurrentChar
           
            # roi = cv2.resize(roi, None, fx=0.75, fy=0.75)
            # cv2.imshow(str(n), cv2.cvtColor(roi, cv2.COLOR_BGR2RGB))

            # cv2.putText(img, first_line + "-" + second_line ,(topy ,topx),cv2.FONT_HERSHEY_DUPLEX, 2, (0, 255, 255), 2)
            return first_line + "-" + second_line
    # img = cv2.resize(img, None, fx=0.5, fy=0.5)


class ControllerLPR(http.Controller):
    @http.route('/parking/lpr/detection', website=False, csrf=False, type='http',  auth='public', methods=['POST'])
    def product_save(self, **kw):
        file = kw['image']
        arr = np.asarray(bytearray(file.read()), dtype=np.uint8)
        img = cv2.imdecode(arr, -1)  # 'Load it as it is'
        img = cv2.resize(img, dsize=(1920, 1080))
        result = testImage(img)
        return result
