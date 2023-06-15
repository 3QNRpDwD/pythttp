// 모달 관련 요소 선택
const openModalButton = document.getElementById('openModal');
const closeModalButton = document.getElementById('closeModal');
const modalOverlay = document.getElementById('modal');
const modalClose = document.querySelector('.modal-close');

// 모달 열기 버튼 클릭 이벤트 처리
openModalButton.addEventListener('click', () => {
  modalOverlay.style.display = 'flex';
});

// 모달 닫기 버튼 클릭 이벤트 처리
function closeModal() {
  modalOverlay.style.display = 'none';
}

closeModalButton.addEventListener('click', closeModal);
modalClose.addEventListener('click', closeModal);

// 게시물 작성 폼 제출 처리
const form = document.getElementById('postForm');

form.addEventListener('submit', async (e) => {
  e.preventDefault(); // 폼 제출 기본 동작 중단

  const title = document.getElementById('title').value;
  const content = document.getElementById('content').value;
  const imageFile = document.getElementById('image').files[0];

  let image = null;
  if (imageFile) {
    // Image 파일을 base64로 인코딩
    const reader = new FileReader();
    reader.onload = function(event) {
      image = event.target.result;
      sendPostData(title, content, image);
    };
    reader.readAsDataURL(imageFile);
  } else {
    sendPostData(title, content, image);
  }
});

// 게시물 데이터 전송
async function sendPostData(title, content, image) {
  const postData = {
    Form: 'Upload_Post',
    title: title,
    content: content,
    image: image
  };

  try {
    const response = await fetch('/Feed_Page', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(postData)
    });

    const responseHTML = await response.text();
    const newPage = document.open('text/html', 'replace');
    newPage.write(responseHTML);
    newPage.close();
  } catch (error) {
    console.error('Error:', error);
    // 오류 처리 로직 추가
  }

  // 모달 닫기
  closeModal();
}

// 추가된 코드: 모달 오버레이 클릭 시 모달 닫기
modalOverlay.addEventListener('click', (e) => {
  if (e.target === modalOverlay) {
    closeModal();
  }
});