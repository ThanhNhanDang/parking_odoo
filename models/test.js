let devices = await navigator.usb.getDevices();
devices.forEach((device) => {
  console.log(device);
});
