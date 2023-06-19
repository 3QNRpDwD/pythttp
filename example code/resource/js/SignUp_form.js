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

  fetch("/SignUp_form", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
  })
  .then(response => {
    if (response.ok || response.status === 403 || response.status === 406 || response.status === 400) {
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
