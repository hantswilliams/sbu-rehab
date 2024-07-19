const video = document.getElementById('video');
const canvas = document.createElement('canvas');
canvas.width = video.width;
canvas.height = video.height;
const context = canvas.getContext('2d');
const processedImage = document.getElementById('processedImage');

if (navigator.mediaDevices.getUserMedia) {
  navigator.mediaDevices.getUserMedia({ video: true })
    .then(function (stream) {
      video.srcObject = stream;
    })
    .catch(function (error) {
      console.log("Something went wrong!");
    });
}

video.addEventListener('play', () => {
  setInterval(() => {
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => {
      const formData = new FormData();
      formData.append('video', blob, 'frame.jpg');

      fetch('/video_feed', {
        method: 'POST',
        body: formData
      })
      .then(response => response.blob())
      .then(blob => {
        const url = URL.createObjectURL(blob);
        processedImage.src = url;
        processedImage.onload = () => URL.revokeObjectURL(url);
      })
      .catch(error => console.error('Error:', error));
    }, 'image/jpeg');
  }, 100);
});
