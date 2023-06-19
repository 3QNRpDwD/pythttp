function goToPostPage(postId) {
  // 게시물의 원본 페이지 URL로 이동
  window.location.href = postId;
}

document.getElementById("searchForm").addEventListener("submit", function(event) {
  event.preventDefault(); // 폼의 기본 제출 동작 방지
  
  var searchInput = document.getElementById("searchInput").value;
  var encodedSearchInput = encodeURIComponent(searchInput);
  var url = "/search?query=" + encodedSearchInput;

  // GET 요청을 보내는 로직을 구현해야 합니다.
  // 여기서는 간략하게 콘솔에 URL을 출력하는 예시로 작성하였습니다.
  console.log(url);
  
  // 서버로 GET 요청을 보내고 응답을 처리하는 로직을 추가해야 합니다.
  // ...
});

var imageFile = null;
var fileUpload = document.getElementById("file-upload");
var imagePreview = document.getElementById("image-preview");
var deleteImage = document.getElementById("delete-image");
var postForm = document.getElementById("postForm");

// 이미지 파일 선택 시 미리보기
fileUpload.addEventListener("change", function(event) {
  var file = event.target.files[0];
  var reader = new FileReader();

  reader.onload = function(e) {
    imagePreview.innerHTML = "";
    var img = document.createElement("img");
    img.src = e.target.result;
    img.classList.add("max-w-xs", "max-h-48", "object-contain");
    imagePreview.appendChild(img);
  };

  reader.readAsDataURL(file);
  imageFile = file;
});

// 이미지 삭제 버튼 클릭 시
deleteImage.addEventListener("click", function(event) {
  imagePreview.innerHTML = "";
  fileUpload.value = "";
  imageFile = null;
});

// 폼 제출 이벤트 처리
postForm.addEventListener("submit", async function(event) {
  event.preventDefault(); // 폼의 기본 제출 동작 방지

  // 제목, 내용, 이미지 값 가져오기
  var title = document.getElementById("title").value;
  var content = document.getElementById("content").value;

  // 이미지 파일을 Base64로 인코딩
  if (imageFile) {
    var reader = new FileReader();
    reader.onloadend = function() {
      // Base64로 인코딩된 이미지 데이터를 JSON에 포함시키기
      var imageData = reader.result.split(",")[1];
      var postData = {
        Form: 'PostUpload',
        title: title,
        content: content,
        image: imageData
      };

      // JSON 데이터 서버로 전송
      sendPostDataToServer(postData);
    };
    reader.readAsDataURL(imageFile);
  } else {
    var postData = {
      Form: 'PostUpload',
      title: title,
      content: content,
      image: null
    };

    // JSON 데이터 서버로 전송
    sendPostDataToServer(postData)
      .then(() => {
      })
      .catch((error) => {
        console.error(error);
      });
  }
});

// JSON 데이터를 서버로 전송하는 함수
function sendPostDataToServer(postData) {
  return new Promise((resolve, reject) => {
    fetch("/Feed_Page", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(postData)
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
      resolve(responseHTML);
    })
    .catch(error => {
      reject(new Error("An error occurred while sending the post data: " + error));
    });
  });
}
