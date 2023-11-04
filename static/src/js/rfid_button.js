/** @odoo-module **/

import { registry } from "@web/core/registry";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { formView } from "@web/views/form/form_view";
import { FormController } from "@web/views/form/form_controller";
import { FormRenderer } from "@web/views/form/form_renderer";
import { onMounted, onWillUpdateProps, useState } from "@odoo/owl";
import rpc from "web.rpc";
import Dialog from "web.Dialog";
var websocket;
var result_split;
function connect() {
  const wsUri = "ws://127.0.0.1:62536/";
  websocket = new WebSocket(wsUri);
  websocket.onopen = function () {
    // subscribe to some channels
    websocket.send("hello");
  };

  websocket.onclose = function (e) {
    document.getElementById("rfid_btn").disabled = false;
    setTimeout(function () {
      connect();
    }, 1000);
  };

  websocket.onerror = function (err) {
    websocket.close();
    document.getElementById("rfid_btn").disabled = false;
  };
}

connect();
// confirm_callback: function () {
//
// },

export class ButtonFormController extends FormController {
  setup() {
    super.setup();
    this.state = useState({
      ...this.state,
      employee: false,
    });
  }

  onClickDKxe() {
    const self = this;
    const action = self.env.services.action;
    action.doAction({
      type: "ir.actions.act_window",
      name: "Action service",
      res_model: "product.template",
      domain: [],
      context: { default_contact_id: self.model.root.data.id },
      view_type: "form",
      views: [[false, "form"]],
      view_mode: "list,form",
      target: "current",
    });
  }

  onClickDKxe() {
    const self = this;
    if (self.model.root.data.id == undefined) {
      this.showAlerDialog("THÔNG BÁO", "CHƯA TẠO THÔNG TIN!!");
      return;
    }
    const action = self.env.services.action;
    action.doAction({
      type: "ir.actions.act_window",
      name: "ĐĂNG KÝ XE",
      res_model: "product.template",
      domain: [],
      context: { default_contact_id: self.model.root.data.id },
      view_type: "form",
      views: [[false, "form"]],
      view_mode: "list,form",
      target: "current",
    });
  }
  onDSxe() {
    const self = this;
    if (self.model.root.data.id == undefined) {
      this.showAlerDialog("THÔNG BÁO", "CHƯA TẠO THÔNG TIN!!");
      return;
    }
    const action = self.env.services.action;
    action.doAction({
      type: "ir.actions.act_window",
      name: "DANH SÁCH XE ĐANG SỞ HỮU",
      res_model: "product.template",
      domain: [["contact_id", "=", self.model.root.data.id]],
      context: { default_contact_id: self.model.root.data.id },
      view_type: "list",
      views: [
        [false, "list"],
        [false, "form"],
      ],
      view_mode: "list,form",
      target: "current",
    });
  }

  rfidHandler(model, field_search) {
    document.getElementById("rfid_btn").disabled = true;
    //Gửi lệnh quét thẻ
    try {
      websocket.send("quet the|false");
    } catch (error) {
      this.showConfirmDialogDownloadPlugin(
        "THÔNG BÁO",
        "Vui lòng kiểm tra service [ Window_nsp_service ] có đang chạy hay không, nếu chưa cài đặt service hãy nhấn vào nút [ OK ] bên dưới để cài đặt!"
      );
      return;
    }
    var self = this;
    websocket.onmessage = async (e) => {
      const message = e.data;
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
      if (message === "1") {
        // Lưu vào database và ghi mật khẩu sau khi kiểm tra xem mã thẻ đã thực sự ghi chưa
        var vals;
        if (field_search === "ref") {
          vals = {
            ref: result_split[1],
            barcode: result_split[2],
            employee: true,
          };
        } else
          vals = {
            default_code: result_split[1],
            barcode: result_split[2],
            check_doi_the: true,
          };
        self
          .rpcQuery(model, "search", [[[field_search, "=", result_split[1]]]])
          .then(function (results) {
            if (results.length !== 0) {
              self.showAlerDialog("THÔNG BÁO", "THẺ ĐÃ TỒN TẠI!!");
              websocket.send("ghi pass|" + result_split[2] + "|false");
              return;
            }
            self
              .rpcQuery(model, "write", [[self.model.root.data.id], vals])
              .then(function (results) {
                if (results)
                  websocket.send(
                    "ghi pass|" + result_split[2] + "|" + results.toString()
                  );
              });
          });
      }
      //Mã thẻ trả về
      if (message.charAt(0) === ".") {
        self
          .rpcQuery(model, "search", [
            [[field_search, "=", message.split(".")[1]]],
          ])
          .then(function (results) {
            //Nếu không có lỗi thì tìm kiếm xem đã có thẻ hay chưa
            if (results.length !== 0) {
              self.showAlerDialog("THÔNG BÁO", "THẺ ĐÃ TỒN TẠI!!");
              return;
            }
            //Nếu không có thẻ thì random mã EPC và password tại hàm createUUID của module Contact.py
            self.rpcQuery(model, "createUUID", [[]]).then(function (results) {
              //Nếu không random được mã thẻ
              if (results.charAt(0) === "L") {
                self.showAlerDialog("THÔNG BÁO", results);
                return;
              }
              const messageSend = results;
              result_split = results.split("|");
              //Nếu random được thì lưu vào cơ sở dữ liệu và ghi mã thẻ random vào thẻ
              // results = "ghi epc|"+"0" + hex_arr[1:24] +"|"+hex_arr[24:]
              websocket.send(messageSend);
            });
          });
      }
    };
  }

  onClickTestJavascript() {
    this.rfidHandler("res.partner", "ref");
  }
  onClickXeJavascript() {
    this.rfidHandler("product.template", "default_code");
  }

  showAlerDialog(title, content) {
    Dialog.alert(this, "", {
      title: title,
      $content: $("<div/>").html(content),
    });
    document.getElementById("rfid_btn").disabled = false;
  }

  showConfirmDialogDownloadPlugin(title, body) {
    const self = this;
    const dialog = self.env.services.dialog;
    dialog.add(
      ConfirmationDialog,
      {
        title: title,
        body: body,
        confirm: () => {
          console.log("confirm");
          window.open("/parking_odoo/static/file/Setup.zip");
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
    document.getElementById("rfid_btn").disabled = false;
  }

  showNotification(content, title, type) {
    const notification = this.env.services.notification;
    notification.add(content, {
      title: title,
      type: type,
      className: "p-4",
    });
    document.getElementById("rfid_btn").disabled = false;
  }
  //args: [this.model.root.data.id, { ref: "12122", employee: true }]
  rpcQuery(model, method, args) {
    return rpc
      .query({
        model: model,
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
