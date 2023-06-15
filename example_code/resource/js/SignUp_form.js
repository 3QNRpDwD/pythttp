document.getElementById("SignUpForm").addEventListener("submit", function(event) {
    event.preventDefault();

    var form = event.target;
    var data = {
      Form: "SignUp",
      UserID: form.elements["UserID"].value,
      UserEmail: form.elements["UserEmail"].value,
      UserName: form.elements["UserName"].value,
      UserPw: form.elements["UserPw"].value
    };

    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/SignUp_form", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function() {
      if (xhr.readyState === 4 && xhr.status === 200 || xhr.status === 403 || xhr.status === 406 || xhr.status === 400) {
        var responseHTML = xhr.responseText;
        var newPage = document.open("text/html", "replace");
        newPage.write(responseHTML);
        newPage.close();
      }
    };
    xhr.send(JSON.stringify(data));
  });