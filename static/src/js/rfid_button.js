import { registry } from '@web/core/registry';
import { formView } from '@web/views/form/form_view';
import { FormController } from '@web/views/form/form_controller';
import { FormRenderer } from '@web/views/form/form_renderer';
const { Component, onMounted, onWillUnmount, onWillUpdateProps, useState } = owl;

export class ButtonFormController extends FormController {
  setup() {
      super.setup();
      console.log("rfid_button.js load");
  }

  onClickTestJavascript(){
      alert("Hello World");
      // const wsUri = "ws://127.0.0.1:62536/";
      // const websocket = new WebSocket(wsUri);
      // console.log(websocket);
      // websocket.onopen = (e) => {
      //   console.log("Da Mo");
      //   websocket.send("Da Mo 1");
      // };
  }
}
ButtonFormController.template="parking_odoo.RFID_button";

export class ButtonFormRenderer extends FormRenderer {
  setup() {

      super.setup();

      onMounted(()=>{

      });

      onWillUpdateProps(async(nextProps)=>{

      });

  }
}

registry.category('views').add('rfid_button', {
  ...formView,
  Controller: ButtonFormController,
  Renderer: ButtonFormRenderer,
});
