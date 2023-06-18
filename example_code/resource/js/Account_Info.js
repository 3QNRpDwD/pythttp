function clearInputValue(input) {
    input.value = '';
  };

// function clearInputValue(element) {
//     element.value = '';
//   }

document.getElementById("accountForm").addEventListener("submit", function(event) {
    event.preventDefault(); // 기본 제출 동작 방지

    // JSON 데이터 생성
    var formData = new FormData(this);
    var jsonObject = {Form: "Account"};
    for (const [key, value] of formData.entries()) {
        jsonObject[key] = value;
    }
    var jsonData = JSON.stringify(jsonObject);

    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/Account_Info", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4 && xhr.status === 200 || xhr.status === 422 || xhr.status === 403 || xhr.status === 400) {
        var responseHTML = xhr.responseText;
        var newPage = document.open("text/html", "replace");
        newPage.write(responseHTML);
        newPage.close();
        }
    };
    xhr.send(jsonData);
    });