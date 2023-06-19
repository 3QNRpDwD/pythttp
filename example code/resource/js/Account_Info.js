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
  
    fetch("/Account_Info", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: jsonData
    })
    .then(response => {
      if (response.ok || response.status === 422 || response.status === 403 || response.status === 400) {
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
  