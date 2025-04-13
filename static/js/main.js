document.addEventListener("DOMContentLoaded", function () {
  // 聊天功能
  const chatInput = document.getElementById("chat-input");
  const sendBtn = document.getElementById("send-btn");
  const chatMessages = document.getElementById("chat-messages");

  // 加载历史消息
  loadChatMessages();

  // 发送消息
  function sendMessage() {
    const message = chatInput.value.trim();
    if (message === "") return;

    fetch("/chat/send", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: `message=${encodeURIComponent(message)}`,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.status === "success") {
          chatInput.value = "";
          loadChatMessages();
        }
      });
  }

  // 加载消息
  function loadChatMessages() {
    fetch("/chat/messages")
      .then((response) => response.json())
      .then((data) => {
        if (data.status === "success") {
          chatMessages.innerHTML = "";
          data.messages.forEach((msg) => {
            const messageDiv = document.createElement("div");
            messageDiv.className = "message";
            messageDiv.innerHTML = `
                        <div class="username">${msg.username}</div>
                        <div class="text">${msg.message}</div>
                        <div class="time">${msg.time}</div>
                    `;
            chatMessages.appendChild(messageDiv);
          });
          chatMessages.scrollTop = chatMessages.scrollHeight;
        }
      });
  }

  // 事件监听
  sendBtn.addEventListener("click", sendMessage);
  chatInput.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
      sendMessage();
    }
  });

  // 每5秒刷新一次聊天消息
  setInterval(loadChatMessages, 3000);
});


// 修改播放器初始化逻辑，增加移动端检测
function initMobilePlayer() {
    if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
        // 移动端强制使用HLS
        if (video.canPlayType('application/vnd.apple.mpegurl')) {
            video.src = streamSources.hls;
            video.play().catch(e => console.error('移动端播放错误:', e));
        } else if (Hls.isSupported()) {
            initHlsPlayer(streamSources.hls);
        }
    }
}

// 在DOMContentLoaded事件中添加
document.addEventListener("DOMContentLoaded", function() {
    initMobilePlayer();
});
