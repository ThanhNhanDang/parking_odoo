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
function connect() {
  const wsUri = "ws://127.0.0.1:62536/";
  websocket = new WebSocket(wsUri);
  websocket.onopen = function () {
    // subscribe to some channels
    websocket.send("hello");
  };

  websocket.onclose = function (e) {
    console.log(
      "Socket is closed. Reconnect will be attempted in 1 second.",
      e.reason
    );
    setTimeout(function () {
      connect();
    }, 1000);
  };

  websocket.onerror = function (err) {
    console.error("Socket encountered error: ", err.message, "Closing socket");
    websocket.close();
  };
}

connect();
console.log("load");

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
  onClickXeJavascript() {
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
          .rpcQuery("product.template", "search", [
            [["default_code", "=", message.split(".")[1]]],
          ])
          .then(function (results) {
            //Nếu không có lỗi thì tìm kiếm xem đã có thẻ hay chưa
            if (results.length !== 0) {
              self.showAlerDialog("THÔNG BÁO", "THẺ ĐÃ TỒN TẠI!!");
              return;
            }
            //Nếu không có thẻ thì random mã EPC và password tại hàm createUUID của module Contact.py
            self
              .rpcQuery("product.template", "createUUID", [[]])
              .then(function (results) {
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
                  .rpcQuery("product.template", "write", [
                    [self.model.root.data.id],
                    {
                      default_code: result[1],
                      barcode: result[2],
                      check_doi_the: true,
                    },
                  ])
                  .then(function (results) {
                    if (results) websocket.send(messageSend);
                  });
              });
          });
      }
    };
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

  onClickTestJavascript() {
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
          .rpcQuery("res.partner", "search", [
            [["ref", "=", message.split(".")[1]]],
          ])
          .then(function (results) {
            //Nếu không có lỗi thì tìm kiếm xem đã có thẻ hay chưa
            if (results.length !== 0) {
              self.showAlerDialog("THÔNG BÁO", "THẺ ĐÃ TỒN TẠI!!");
              return;
            }
            //Nếu không có thẻ thì random mã EPC và password tại hàm createUUID của module Contact.py
            self
              .rpcQuery("res.partner", "createUUID", [[]])
              .then(function (results) {
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
                  .rpcQuery("res.partner", "write", [
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
