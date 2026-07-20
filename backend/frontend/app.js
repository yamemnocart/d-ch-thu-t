const API_BASE = "http://localhost:8000/api";

const videoFile = document.getElementById("videoFile");
const uploadBtn = document.getElementById("uploadBtn");
const videoUrl = document.getElementById("videoUrl");
const processUrlBtn = document.getElementById("processUrlBtn");
const statusArea = document.getElementById("statusArea");
const progressBar = document.getElementById("progressBar");
const statusText = document.getElementById("statusText");
const resultArea = document.getElementById("resultArea");
const previewVideo = document.getElementById("previewVideo");
const downloadVideo = document.getElementById("downloadVideo");
const downloadSrt = document.getElementById("downloadSrt");

let pollingTimer = null;

function startPolling(taskId) {
    progressBar.style.width = "10%";
    statusArea.classList.remove("hidden");
    resultArea.classList.add("hidden");

    pollingTimer = setInterval(async () => {
        const res = await fetch(`${API_BASE}/status/${taskId}`);
        const data = await res.json();

        if (data.status === "processing") {
            statusText.textContent = data.step;
            progressBar.style.width = `${Math.min(90, progressBar.offsetWidth / 4 + 10)}%`;
        } else if (data.status === "completed") {
            clearInterval(pollingTimer);
            progressBar.style.width = "100%";
            statusText.textContent = "Xử lý xong!";
            
            setTimeout(() => {
                statusArea.classList.add("hidden");
                resultArea.classList.remove("hidden");
                previewVideo.src = data.video_url;
                downloadVideo.href = data.video_url;
                downloadSrt.href = data.srt_url;
            }, 800);
        } else if (data.status === "error") {
            clearInterval(pollingTimer);
            statusText.textContent = `Lỗi: ${data.message}`;
            progressBar.classList.replace("bg-blue-500", "bg-red-500");
        }
    }, 1500);
}

// Xử lý tải file lên
uploadBtn.addEventListener("click", async () => {
    if (!videoFile.files[0]) return alert("Vui lòng chọn file video");
    
    const formData = new FormData();
    formData.append("file", videoFile.files[0]);
    
    try {
        uploadBtn.disabled = true;
        uploadBtn.textContent = "Đang tải lên...";
        const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: formData });
        const { task_id } = await res.json();
        startPolling(task_id);
    } catch (e) {
        alert("Lỗi kết nối server: " + e.message);
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.textContent = "Tải lên & Xử lý";
    }
});

// Xử lý link
processUrlBtn.addEventListener("click", async () => {
    const url = videoUrl.value.trim();
    if (!url) return alert("Vui lòng nhập link video");
    
    try {
        processUrlBtn.disabled = true;
        processUrlBtn.textContent = "Đang tải...";
        const formData = new FormData();
        formData.append("url", url);
        const res = await fetch(`${API_BASE}/process-url`, { method: "POST", body: formData });
        const { task_id } = await res.json();
        startPolling(task_id);
    } catch (e) {
        alert("Lỗi kết nối server: " + e.message);
    } finally {
        processUrlBtn.disabled = false;
        processUrlBtn.textContent = "Xử lý link";
    }
});
