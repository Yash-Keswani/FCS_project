function input(e) {
    var keyInput = document.getElementById("keyInput");
    keyInput.value = keyInput.value + e;
}

function deleting_val() {
    var tbInput = document.getElementById("keyInput");
    tbInput.value = tbInput.value.substr(0, tbInput.value.length - 1);
}
