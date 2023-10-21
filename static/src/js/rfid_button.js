odoo.define("parking_odoo.RFID_button", function (require, factory) {
  "use strict";
  console.log("rfid_button.js load");
  const wsUri = "ws://127.0.0.1:62536/";
  const websocket = new WebSocket(wsUri);
  console.log(websocket);
  websocket.onopen = (e) => {
    console.log("Da Mo");
  };
});
