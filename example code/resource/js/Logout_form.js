document.getElementById("LogoutForm").addEventListener("submit", function(event) {
  event.preventDefault(); // 폼 기본 제출 동작 방지

  var form = event.target;
  var data = {
    Form: "Logout"
  };

  fetch("/login_form", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
  })
  .then(response => {
    if (response.ok || response.status === 403 || response.status === 400) {
      return response.text();
    } else {
      throw new Error("Post request failed with status: " + response.status);
    }
  })
  .then(responseHTML => {
    var newPage = document.open("text/html", "replace");
    newPage.write(responseHTML);
    newPage.close();
  })
  .catch(error => {
    console.error("An error occurred while sending the post data:", error);
  });
});
