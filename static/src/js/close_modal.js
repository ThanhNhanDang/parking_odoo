document.addEventListener("DOMContentLoaded", function() {
    // Lấy tham chiếu đến nút và section
    const modalContentPartner  = document.getElementById("modalPartner");
    const btnSave = document.getElementById("btn_save");

    // Thêm sự kiện click cho nút
    btnSave.addEventListener("save", function() {
        // Kiểm tra trạng thái hiện tại của section và thay đổi
        if (modalContentPartner.classList.contains("modal-content")) {
            modalContentPartner.classList.remove("modal-content"); // Hiện section
        } else {
            modalContentPartner.classList.add("modal-content"); // Ẩn section
        }
    });
});
