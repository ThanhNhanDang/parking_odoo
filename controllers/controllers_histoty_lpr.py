from odoo import http, modules
import pytz
import logging
import base64
import json

import math
import cv2
import numpy as np
import torch

############# requeirement for LPR #############
# for .pt: opencv-python matplotlib torchvision pyyaml pandas seaborn
# for .onnx: onnx onnxruntime
############# requeirement for LPR #############

# LP_detector_nano_61_path = modules.module.get_resource_path(
#     'parking_odoo',
#     'static/file/model',
#     'LP_detector_nano_61.pt'
# )

# LP_ocr_nano_62_path = modules.module.get_resource_path(
#     'parking_odoo',
#     'static/file/model',
#     'LP_ocr_nano_62.pt'
# )
# yolov5_path = modules.module.get_resource_path(
#     'parking_odoo',
#     'yolov5'
# )
# yolo_LP_detect = torch.hub.load(
#     yolov5_path, 'custom', path=LP_detector_nano_61_path, force_reload=True, source='local')
# yolo_license_plate = torch.hub.load(
#     yolov5_path, 'custom', path=LP_ocr_nano_62_path, force_reload=True, source='local')
# yolo_license_plate.conf = 0.60

######## helper ########
# license plate type classification helper function


def linear_equation(x1, y1, x2, y2):
    b = y1 - (y2 - y1) * x1 / (x2 - x1)
    a = (y1 - b) / x1
    return a, b


def check_point_linear(x, y, x1, y1, x2, y2):
    a, b = linear_equation(x1, y1, x2, y2)
    y_pred = a*x+b
    return (math.isclose(y_pred, y, abs_tol=3))

# detect character and number in license plate


def read_plate(yolo_license_plate, im):
    LP_type = "1"
    results = yolo_license_plate(im)
    bb_list = results.pandas().xyxy[0].values.tolist()
    if len(bb_list) == 0 or len(bb_list) < 7 or len(bb_list) > 10:
        return "unknown"
    center_list = []
    y_mean = 0
    y_sum = 0
    for bb in bb_list:
        x_c = (bb[0]+bb[2])/2
        y_c = (bb[1]+bb[3])/2
        y_sum += y_c
        center_list.append([x_c, y_c, bb[-1]])

    # find 2 point to draw line
    l_point = center_list[0]
    r_point = center_list[0]
    for cp in center_list:
        if cp[0] < l_point[0]:
            l_point = cp
        if cp[0] > r_point[0]:
            r_point = cp
    for ct in center_list:
        if l_point[0] != r_point[0]:
            if (check_point_linear(ct[0], ct[1], l_point[0], l_point[1], r_point[0], r_point[1]) == False):
                LP_type = "2"

    y_mean = int(int(y_sum) / len(bb_list))
    # size = results.pandas().s

    # 1 line plates and 2 line plates
    line_1 = []
    line_2 = []
    license_plate = ""
    if LP_type == "2":
        for c in center_list:
            if int(c[1]) > y_mean:
                line_2.append(c)
            else:
                line_1.append(c)
        for l1 in sorted(line_1, key=lambda x: x[0]):
            license_plate += str(l1[2])
        license_plate += "-"
        for l2 in sorted(line_2, key=lambda x: x[0]):
            license_plate += str(l2[2])
    else:
        for l in sorted(center_list, key=lambda x: x[0]):
            license_plate += str(l[2])
    return license_plate
######## helper ########

###### utils_rotate ######


def changeContrast(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l_channel, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l_channel)
    limg = cv2.merge((cl, a, b))
    enhanced_img = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
    return enhanced_img


def rotate_image(image, angle):
    image_center = tuple(np.array(image.shape[1::-1]) / 2)
    rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
    result = cv2.warpAffine(
        image, rot_mat, image.shape[1::-1], flags=cv2.INTER_LINEAR)
    return result


def compute_skew(src_img, center_thres):
    if len(src_img.shape) == 3:
        h, w, _ = src_img.shape
    elif len(src_img.shape) == 2:
        h, w = src_img.shape
    else:
        print('upsupported image type')
    img = cv2.medianBlur(src_img, 3)
    edges = cv2.Canny(img,  threshold1=30,  threshold2=100,
                      apertureSize=3, L2gradient=True)
    lines = cv2.HoughLinesP(edges, 1, math.pi/180, 30,
                            minLineLength=w / 1.5, maxLineGap=h/3.0)
    if lines is None:
        return 1

    min_line = 100
    min_line_pos = 0
    for i in range(len(lines)):
        for x1, y1, x2, y2 in lines[i]:
            center_point = [((x1+x2)/2), ((y1+y2)/2)]
            if center_thres == 1:
                if center_point[1] < 7:
                    continue
            if center_point[1] < min_line:
                min_line = center_point[1]
                min_line_pos = i

    angle = 0.0
    # nlines = lines.size
    cnt = 0
    for x1, y1, x2, y2 in lines[min_line_pos]:
        ang = np.arctan2(y2 - y1, x2 - x1)
        if math.fabs(ang) <= 30:  # excluding extreme rotations
            angle += ang
            cnt += 1
    if cnt == 0:
        return 0.0
    return (angle / cnt)*180/math.pi


def deskew(src_img, change_cons, center_thres):
    if change_cons == 1:
        return rotate_image(src_img, compute_skew(changeContrast(src_img), center_thres))
    else:
        return rotate_image(src_img, compute_skew(src_img, center_thres))

###### utils_rotate ######

###### test LPR image #######


def testImage(img_t):
    # _, height, _ = img_t.shape
    # top = 12
    # bottom = height
    # img = img_t[top:bottom, :]
    # plates = yolo_LP_detect(img, size=640)
    # # print(plates.pandas().xyxy[0].values.tolist())
    # list_plates = plates.pandas().xyxy[0].values.tolist()
    # list_read_plates = set()
    # if len(list_plates) == 0:
    #     lp = read_plate(yolo_license_plate, img)
    #     if lp != "unknown":
    #         # cv2.putText(img, lp, (7, 70), cv2.FONT_HERSHEY_SIMPLEX,
    #         #             0.9, (36, 255, 12), 2)
    #         list_read_plates.add(lp)
    #     return {'lp': "unknown", 'jpg': None}
    # for plate in list_plates:
    #     flag = 0
    #     x = int(plate[0])  # xmin
    #     y = int(plate[1])  # ymin
    #     w = int(plate[2] - plate[0])  # xmax - xmin
    #     h = int(plate[3] - plate[1])  # ymax - ymin
    #     crop_img = img[y:y+h, x:x+w]
    #     _, buffer = cv2.imencode('.jpg', crop_img)
    #     jpg_as_text = base64.b64encode(buffer).decode()
    #     # đánh nhãn
    #     cv2.rectangle(img, (int(plate[0]), int(plate[1])), (int(
    #         plate[2]), int(plate[3])), color=(0, 0, 225), thickness=2)
    #     lp = ""
    #     for cc in range(0, 2):
    #         for ct in range(0, 2):
    #             lp = read_plate(yolo_license_plate,
    #                             deskew(crop_img, cc, ct))
    #             if lp != "unknown":
    #                 # list_read_plates.add(lp)
    #                 # cv2.putText(img, lp, (int(plate[0]), int(plate[1]-10)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36,255,12), 2)
    #                 flag = 1
    #                 break
    #         if flag == 1:
    #             break

    #     return {'lp': lp, 'jpg': jpg_as_text}
    return {'lp': "unknown", 'jpg': None}


###### test LPR image #######
_logger = logging.getLogger(__name__)


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


def changeDate(date_in, is_het_han):
    user_tz = pytz.timezone(str(http.request.env.user.tz or pytz.utc))
    # Convert the date to a Python `datetime` object
    python_date = date_in.strptime(
        str(date_in), "%Y-%m-%d %H:%M:%S")
    timezone = pytz.utc.localize(python_date).astimezone(user_tz)
    # if (timezone.date() == today):
    if is_het_han:
        display_date_result = timezone.strftime("%d/%m/%Y")
    else:
        display_date_result = timezone.strftime("%H:%M:%S %d/%m/%Y")
    return display_date_result


class ControllerHistoryLPR(http.Controller):
    @http.route('/parking/lpr/detection', website=False, csrf=False, type='http',  auth='public', methods=['POST'])
    def product_save(self, **kw):
        file = kw['image']
        arr = np.asarray(bytearray(file.read()), dtype=np.uint8)
        img = cv2.imdecode(arr, -1)  # 'Load it as it is'
        result = testImage(img)
        return result
    
    @http.route('/parking/post/in/edit', website=False, csrf=False, type='http', methods=['POST'],  auth='public')
    def edit(self, **kw):
        product_template = http.request.env["product.template"].sudo().search([('default_code', '=', kw['sEPC'])], limit=1)
       
        file = kw['image_capture']
        img_attachment = file.read()
        image_1920 = base64.b64encode(img_attachment)
        
        product_template.write({'name':'helo', 'image_1920': image_1920})


    @http.route('/parking/post/in/move_history', website=False, csrf=False, type='http', methods=['POST'],  auth='public')
    def post_in_move_history(self, **kw):
        product_template = http.request.env["product.template"].sudo().search(
            [('default_code', '=', kw['sEPC'])], limit=1)
        user = http.request.env['res.partner'].sudo().search(
            domain=[('id', '=', kw['user_id'])],
            limit=1)
        if not user:
            return "0"
        if not product_template:
            return "0"
        if 'image_capture' in kw:
            file = kw['image_capture']
            img_attachment = file.read()
            arr = np.asarray(bytearray(img_attachment), dtype=np.uint8)
            image_1920_camera_sau = base64.b64encode(img_attachment)
        else: 
            image_1920_camera_sau = None
        display_date_result2 = changeDate(user.date_expiration, True)
        if not product_template.location_id:
            location_empty = find_location_empty()
            if not location_empty:
                return "-1"
            # Cập nhật vị trí trống
            location_empty.write({'product_id': product_template.id})
            # img = cv2.imdecode(arr, -1)  # 'Load it as it is'
            img = None
            bien_so_realtime = testImage(img)
            if bien_so_realtime['lp'] == "unknown":
                image_1920_bs_camera = None
            else:
                image_1920_bs_camera = bien_so_realtime['jpg']
            
            stock_move_history = http.request.env["stock.move.line"].sudo().create(
                {
                    'move_history_id_before': product_template.move_history_id.id,
                    'picking_code': 'incoming',
                    'product_id': product_template.id,
                    'contact_id': kw['user_id'],
                    'location_id': location_empty.id,
                    'location_dest_id': location_empty.id,
                    'company_id': 1,
                    'image_1920_camera_sau': image_1920_camera_sau,
                    'image_1920_bs_camera': image_1920_bs_camera,
                    'bien_so_realtime': bien_so_realtime['lp'],
                })
            product_template.write(
                {'date_in': stock_move_history.date, 'move_history_id': stock_move_history.id})
            display_date_result = changeDate(stock_move_history.date, False)
            if image_1920_camera_sau != None:
                image_1920_camera_sau = image_1920_camera_sau.decode()
            else: 
                image_1920_camera_sau = "-1"
            return json.dumps({
                "bien_so_realtime": bien_so_realtime['lp'],
                "bien_so_chup": bien_so_realtime['jpg'],
                "bien_so_dk": product_template.name,
                "image_1920_ng": user.image_1920.decode(),
                "image_1920_xe": product_template.image_1920.decode(),
                "image_1920_camera_sau": image_1920_camera_sau,
                "image_1920_bs_dk": product_template.image_1920_bien_so.decode(),
                "date_vao": display_date_result,
                "date_het_han": display_date_result2,
                "dia_chi": user.city,
                "user_name": user.name,
            }, ensure_ascii=False)
        if image_1920_camera_sau != None:
            image_1920_camera_sau = image_1920_camera_sau.decode()
        else: 
            image_1920_camera_sau = "-1"
        return json.dumps({
            "bien_so_dk": product_template.name,
            "bien_so_realtime": "unknown",
            "image_1920_ng": user.image_1920.decode(),
            "image_1920_xe": product_template.image_1920.decode(),
            "image_1920_bs_dk": product_template.image_1920_bien_so.decode(),
            "image_1920_camera_sau": image_1920_camera_sau,
            "date_het_han": display_date_result2,
            "dia_chi": user.city,
            "user_name": user.name,
        }, ensure_ascii=False)

    @http.route('/parking/post/out/move_history', website=False, csrf=False, type='http', methods=['POST'],  auth='public')
    def post_out_move_history(self, **kw):
        product_template = http.request.env["product.template"].sudo().search(
            [('default_code', '=', kw['sEPC'])], limit=1)
        # Nếu xe có vị trí tức là nó đã vào, giờ xử lý quy trình ra bãi
        user = http.request.env['res.partner'].sudo().search(
            domain=[('id', '=', kw['user_id'])],
            limit=1)
        if not user:
            return "0"
        if not product_template:
            return "0"
        if 'image_capture' in kw:
            file = kw['image_capture']
            img_attachment = file.read()
            arr = np.asarray(bytearray(img_attachment), dtype=np.uint8)
            image_1920_camera_sau = base64.b64encode(img_attachment)
        else: 
            image_1920_camera_sau = None
        if product_template.location_id:
            # img = cv2.imdecode(arr, -1)  # 'Load it as it is'
            img = None
            bien_so_realtime = testImage(img)
            if bien_so_realtime['lp'] == "unknown":
                image_1920_bs_camera = None
            else:
                image_1920_bs_camera = bien_so_realtime['jpg']

            stock_move_history = http.request.env["stock.move.line"].sudo().create(
                {
                    'move_history_id_before': product_template.move_history_id.id,
                    'picking_code': 'outgoing',
                    'product_id': product_template.id,
                    'contact_id': kw['user_id'],
                    'location_id': product_template.location_id.id,
                    'location_dest_id': product_template.location_id.id,
                    'company_id': 1,
                    'image_1920_camera_sau': image_1920_camera_sau,
                    'image_1920_bs_camera': image_1920_bs_camera,
                    'bien_so_realtime': bien_so_realtime['lp'],
                    'date_in': product_template.date_in,
                })
            stock_move_history.location_id.write({'product_id': None})
            delta = stock_move_history.date - product_template.date_in
            hours = delta.total_seconds() // 3600
            minutes = (delta.total_seconds() % 3600) // 60
            stock_move_history.write(
                {'date_sub_in_out': f"{hours} giờ {minutes} phút"})
            # Cập nhật thời gian ra bãi
            if (product_template.move_history_id.image_1920_bs_camera == False):
                image_1920_bs_cambefore = None
            else:
                image_1920_bs_cambefore = product_template.move_history_id.image_1920_bs_camera.decode()
            product_template.write(
                {'date_out': stock_move_history.date, 'move_history_id': stock_move_history.id})
            # Cập nhật thời gian vào bãi cho lịch sử di chuyển
            display_date_result = changeDate(stock_move_history.date, False)
            display_date_result2 = changeDate(
                stock_move_history.date_in, False)
            if product_template.move_history_id.bien_so_realtime == "unknown":
                bien_so_realtime_vao = "unknown"
            else:
                bien_so_realtime_vao = product_template.move_history_id.bien_so_realtime
            if(stock_move_history.i_1920_cam_sau_before == False):
                i_1920_cam_sau_before = None
            else: i_1920_cam_sau_before = stock_move_history.i_1920_cam_sau_before.decode()
        
            if(stock_move_history.i_1920_cam_trc_before == False):
                i_1920_cam_trc_before = None
            else: i_1920_cam_trc_before = stock_move_history.i_1920_cam_trc_before.decode()

            if image_1920_camera_sau != None:
                image_1920_camera_sau = image_1920_camera_sau.decode()
            else: 
                image_1920_camera_sau = "-1"
            return json.dumps({
                "bien_so_realtime": bien_so_realtime['lp'],
                "bien_so_realtime_vao": bien_so_realtime_vao,
                'bien_so_chup': bien_so_realtime['jpg'],
                "bien_so_dk": product_template.name,
                "image_1920_camera_sau": image_1920_camera_sau,
                "i_1920_cam_sau_before": i_1920_cam_sau_before,
                "i_1920_cam_trc_before": i_1920_cam_trc_before,
                "image_1920_bs_dk": product_template.image_1920_bien_so.decode(),
                "image_1920_ng": user.image_1920.decode(),
                "user_name": user.name,
                "image_1920_bs_cambefore": image_1920_bs_cambefore,
                "date_vao": display_date_result2,
                "date_ra": display_date_result,
                "date_sub_in_out": stock_move_history.date_sub_in_out
            }, ensure_ascii=False)

        if image_1920_camera_sau != None:
            image_1920_camera_sau = image_1920_camera_sau.decode()
        else: 
            image_1920_camera_sau = "-1"
        return json.dumps({
            "bien_so_dk": product_template.name,
            "user_name":user.name,
            "bien_so_realtime": "unknown",
            "image_1920_ng": user.image_1920.decode(),
            "image_1920_xe": product_template.image_1920.decode(),
            "image_1920_bs_dk": product_template.image_1920_bien_so.decode(),
            "image_1920_camera_sau": image_1920_camera_sau,
            
        }, ensure_ascii=False)
