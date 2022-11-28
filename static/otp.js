function input(e) {
    var keyInput = document.getElementById("id_otp");
    keyInput.value = keyInput.value + e;
}

function deleting_val() {
    var tbInput = document.getElementById("id_otp");
    tbInput.value = tbInput.value.substr(0, tbInput.value.length - 1);
}
