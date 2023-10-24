/** @odoo-module **/

import { registry } from "@web/core/registry";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { formView } from "@web/views/form/form_view";
import { FormController } from "@web/views/form/form_controller";
import { FormRenderer } from "@web/views/form/form_renderer";
import { onMounted, onWillUpdateProps, useState } from "@odoo/owl";
import rpc from "web.rpc";
import Dialog from "web.Dialog";

const wsUri = "ws://127.0.0.1:62536/";

const websocket = new WebSocket(wsUri);
websocket.onopen = async (e) => {
  websocket.send("hello");
};

// confirm_callback: function () {
//   titles = titles || [];
//   if (titles.length > 0) {
//     var url = "/parking_odoo/static/file/";
//     var len = titles.length;
//     for (var ii = 0; ii < len; ii++) {
//       url = url + "titles=" + titles[ii];
//       if (ii < len - 1) {
//         url = url + "&";
//       }
//     }
//     document.window.open(url);
//   }
// },

export class ButtonFormController extends FormController {
  setup() {
    super.setup();
    this.state = useState({ ...this.state, employee: false });
  }
  onClickTestJavascript() {
    //Gửi lệnh quét thẻ
    websocket.send("quet the|false");
    var self = this;
    websocket.onmessage = async (e) => {
      const message = e.data;
      console.log(message);
      //Kiểm tra lỗi nếu ký tự đầu là L
      if (message.charAt(0) === "L") {
        //In thông báo lỗi ra màn hình
        self.showAlerDialog("THÔNG BÁO", message);
        return;
      }
      //Cấp thẻ thành công
      if (message.charAt(0) === "C") {
        self.state.employee = true;
        self.showNotification(message, "THÔNG BÁO", "success");
        return;
      }
      //Mã thẻ trả về
      if (message.charAt(0) === ".") {
        self
          .rpcQuery("search", [[["ref", "=", message.split(".")[1]]]])
          .then(function (results) {
            //Nếu không có lỗi thì tìm kiếm xem đã có thẻ hay chưa
            if (results.length !== 0) {
              self.showAlerDialog("THÔNG BÁO", "THẺ ĐÃ TỒN TẠI!!");
              return;
            }
            //Nếu không có thẻ thì random mã EPC và password tại hàm createUUID của module Contact.py
            self.rpcQuery("createUUID", [[]]).then(function (results) {
              //Nếu không random được mã thẻ
              if (results.charAt(0) === "L") {
                self.showAlerDialog("THÔNG BÁO", results);
                return;
              }
              const messageSend = results;
              const result = results.split("|");
              //Nếu random được thì lưu vào cơ sở dữ liệu và ghi mã thẻ và mật khẩu random vào thẻ
              // results = "ghi the|"+"0" + hex_arr[1:24] +"|"+hex_arr[24:]
              self
                .rpcQuery("write", [
                  [self.model.root.data.id],
                  { ref: result[1], barcode: result[2], employee: true },
                ])
                .then(function (results) {
                  if (results) websocket.send(messageSend);
                });
            });
          });
      }
    };
  }

  showAlerDialog(title, content) {
    Dialog.alert(this, "", {
      title: title,
      $content: $("<div/>").html(content),
    });
  }

  showConfirmDialogDownloadPlugin(title, body) {
    const dialog = this.env.services.dialog;
    dialog.add(
      ConfirmationDialog,
      {
        title: title,
        body: body,
        confirm: () => {
          console.log("confirm");
        },
        cancel: () => {
          console.log("cancel");
        },
      },
      {
        onclose: () => {
          console.log("close");
        },
      }
    );
  }

  showNotification(content, title, type) {
    const notification = this.env.services.notification;
    notification.add(content, {
      title: title,
      type: type,
      className: "p-4",
    });
  }
  //args: [this.model.root.data.id, { ref: "12122", employee: true }]
  rpcQuery(method, args) {
    return rpc
      .query({
        model: "res.partner",
        method: method,
        args: args,
      })
      .then(function (results) {
        return results;
      });
  }
}
ButtonFormController.template = "parking_odoo.RFID_button";

export class ButtonFormRenderer extends FormRenderer {
  setup() {
    super.setup();
    onMounted(() => {});
    onWillUpdateProps(async (nextProps) => {});
  }
}

registry.category("views").add("rfid_button", {
  ...formView,
  Controller: ButtonFormController,
  Renderer: ButtonFormRenderer,
});
