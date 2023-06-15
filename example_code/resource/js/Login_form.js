document.getElementById("loginForm").addEventListener("submit", function(event) {
    event.preventDefault(); // 폼 기본 제출 동작 방지

    var form = event.target;
    var data = {
      Form: "Login",
      UserID: form.elements["UserID"].value,
      UserPw: form.elements["UserPw"].value
    };

    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/login_form", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function() {
      if (xhr.readyState === 4 && xhr.status === 200 || xhr.status === 422 || xhr.status === 403 || xhr.status === 400) {
        var responseHTML = xhr.responseText;
        var newPage = document.open("text/html", "replace");
        newPage.write(responseHTML);
        newPage.close();
      }
    };
    xhr.send(JSON.stringify(data));
  });