from odoo import http, modules
import pytz
import cv2
import numpy as np
import math
import logging
import base64
import json
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
            return first_line+second_line
    # img = cv2.resize(img, None, fx=0.5, fy=0.5)


def find_location_empty():
    # Tìm danh sách vị trí trống trong bãi lấy danh sách tên của bãi
    locations_empty = http.request.env["stock.location"].sudo().search([
        ('state', '=', 'empty')])
    # Tìm danh vị trí trống đầu tiên trong danh sách
    for location_empty in locations_empty:
      
        # Có nhiều bãi xe nên tìm bãi xe của mình
        # Tìm bãi xe trống đầu tiên rồi cập nhật danh sách trống
        location = location_empty.complete_name.split('/')
        # Tìm BX của mình và tìm Bãi nào có định dạng là 3 phần tử
        # BX\A\A1 or BX\B\B2

        if 'BX' in location and len(location) > 2 and location_empty.state == 'empty':
            return location_empty
    return []

def changeDate(date_in):
    user_tz = pytz.timezone(http.request.env.context.get('tz') or http.request.env.user.tz or pytz.utc)
    # Convert the date to a Python `datetime` object
    python_date = date_in.strptime(
        str(date_in), "%Y-%m-%d %H:%M:%S")
    timezone = pytz.utc.localize(python_date).astimezone(user_tz)
    # if (timezone.date() == today):
    display_date_result = timezone.strftime("%H:%M:%S %d/%m/%Y")
    return display_date_result


class ControllerHistoryLPR(http.Controller):
    @http.route('/parking/lpr/detection', website=False, csrf=False, type='http',  auth='public', methods=['POST'])
    def product_save(self, **kw):
        file = kw['image']
        arr = np.asarray(bytearray(file.read()), dtype=np.uint8)
        img = cv2.imdecode(arr, -1)  # 'Load it as it is'
        img = cv2.resize(img, dsize=(1920, 1080))
        result = testImage(img)
        return result

    @http.route('/parking/post/in/move_history', website=False, csrf=False, type='http', methods=['POST'],  auth='public')
    def post_in_move_history(self, **kw):
        location_empty = find_location_empty()
        if not location_empty:
            return "-1"
        product_template = http.request.env["product.template"].sudo().search(
            [('default_code', '=', kw['sEPC'])], limit=1)
        if not product_template.location_id:
            # Cập nhật vị trí trống
            location_empty.write({'product_id': product_template.id})
            file = kw['image_sau']
            img_attachment = file.read()
            image_1920_camera_sau = base64.b64encode(img_attachment)
            arr = np.asarray(bytearray(img_attachment), dtype=np.uint8)
            img = cv2.imdecode(arr, -1)  # 'Load it as it is'
            img = cv2.resize(img, dsize=(1920, 1080))
            bien_so_realtime = testImage(img)
            file = kw['image_truoc']
            img_attachment = file.read()
            image_1920_camera_truoc = base64.b64encode(img_attachment)
            user = http.request.env['res.partner'].sudo().search(
                domain=[('id', '=', kw['user_id'])],
                limit=1)
            if not user:
                return "0"
            stock_move_history = http.request.env["stock.move.line"].sudo().create(
                {
                    'picking_code': 'incoming',
                    'product_id': product_template.id,
                    'contact_id': kw['user_id'],
                    'location_id': location_empty.id,
                    'location_dest_id': location_empty.id,
                    'company_id': 1,
                    'image_1920_camera_sau': image_1920_camera_sau,
                    'image_1920_camera_truoc': image_1920_camera_truoc,
                    'bien_so_realtime': bien_so_realtime
                })
            product_template.write({'date_in': stock_move_history.date})
            display_date_result = changeDate(stock_move_history.date)
            return json.dumps({
                "bien_so_realtime": bien_so_realtime,
                "bien_so_dk": product_template.name,
                "image_1920_ng": str(stock_move_history.image_1920_ng),
                "image_1920_xe": str(stock_move_history.image_1920_xe),
                "date_vao": display_date_result,
                "location_name": location_empty.name,
                "user_name": user.name,
                "ma_the": product_template.default_code,
                "user_id": user.id,
                "history_id": stock_move_history.id,
            }, ensure_ascii=False)
        return "0"

    @http.route('/parking/post/out/move_history', website=False, csrf=False, type='http', methods=['POST'],  auth='public')
    def post_out_move_history(self, **kw):
        product_template = http.request.env["product.template"].sudo().search(
            [('default_code', '=', kw['sEPC'])], limit=1)
        # Nếu xe có vị trí tức là nó đã vào, giờ xử lý quy trình ra bãi
        if product_template.location_id:
            file = kw['image_sau']
            img_attachment = file.read()
            image_1920_camera_sau = base64.b64encode(img_attachment)
            arr = np.asarray(bytearray(img_attachment), dtype=np.uint8)
            img = cv2.imdecode(arr, -1)  # 'Load it as it is'
            img = cv2.resize(img, dsize=(1920, 1080))
            bien_so_realtime = testImage(img)

            file = kw['image_truoc']
            img_attachment = file.read()
            image_1920_camera_truoc = base64.b64encode(img_attachment)
            user = http.request.env['res.partner'].sudo().search(
                domain=[('id', '=', kw['user_id'])],
                limit=1)
            if not user:
                return 0
            stock_move_history = http.request.env["stock.move.line"].sudo().create(
                {
                    'picking_code': 'outgoing',
                    'product_id': product_template.id,
                    'contact_id': kw['user_id'],
                    'location_id': location_empty.id,
                    'location_dest_id': location_empty.id,
                    'company_id': 1,
                    'image_1920_camera_sau': image_1920_camera_sau,
                    'image_1920_camera_truoc': image_1920_camera_truoc,
                    'bien_so_realtime': bien_so_realtime
                })
            ## Cập nhật thời gian ra bãi
            product_template.write({'date_out': stock_move_history.date})
            ## Cập nhật thời gian vào bãi cho lịch sử di chuyển
            stock_move_history.write({'date_in': product_template.date_in})
            display_date_result = changeDate(stock_move_history.date)
            display_date_result2 = changeDate(stock_move_history.date_in)
            return json.dumps({
                "bien_so_realtime": bien_so_realtime,
                "bien_so_dk": product_template.name,
                "image_1920_ng": str(stock_move_history.image_1920_ng),
                "image_1920_xe": str(stock_move_history.image_1920_xe),
                "date_vao": display_date_result2, 
                "date_ra": display_date_result,
                "location_name": location_empty.name,
                "user_name": user.name,
                "ma_the": product_template.default_code,
                "user_id": user.id,
                "history_id": stock_move_history.id,
            }, ensure_ascii=False)
        return "0"
