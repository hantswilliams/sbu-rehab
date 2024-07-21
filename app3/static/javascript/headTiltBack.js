function calculateAngle(a, b, c) {
  const ab = { x: b.x - a.x, y: b.y - a.y };
  const bc = { x: b.x - c.x, y: b.y - c.y };
  const abLength = Math.sqrt(ab.x * ab.x + ab.y * ab.y);
  const bcLength = Math.sqrt(bc.x * bc.x + bc.y * bc.y);
  const dotProduct = ab.x * bc.x + ab.y * bc.y;
  const angle = Math.acos(dotProduct / (abLength * bcLength));
  return angle * (180 / Math.PI); // convert to degrees
}

function smoothAngle(currentAngle) {
  angleHistory.push(currentAngle);
  if (angleHistory.length > historyLength) {
    angleHistory.shift();
  }
  const sum = angleHistory.reduce((a, b) => a + b, 0);
  return sum / angleHistory.length;
}

function updateProgressBar(currentAngle) {
  const progressBar = document.getElementById('progress-bar');
  const progressBarText = document.getElementById('progress-bar-text');
  const countView = document.getElementById('count-view');
  const messageBox = document.getElementById('message-box');
  const angleChange = currentAngle - startingAngle;
  const progress = Math.min(Math.max((angleChange / targetAngleChange) * 100, 0), 100); // normalize to 0-100%

  progressBar.style.width = progress + '%';
  progressBarText.innerText = `${Math.round(currentAngle)}°`;

  if (progress < 33) {
    progressBar.className = 'h-6 bg-gray-500 rounded';
  } else if (progress < 66) {
    progressBar.className = 'h-6 bg-blue-500 rounded';
  } else {
    progressBar.className = 'h-6 bg-green-500 rounded';
  }

  if (progress === 100 && isCounting && !isReturning) {
    isReturning = true;
    messageBox.innerText = "Move your head back down!";
    messageBox.style.display = 'block'; // Show the message box
  } else if (progress === 0 && isCounting && isReturning) {
    repsCount++;
    countView.innerText = repsCount;
    isReturning = false;
    messageBox.innerText = "Move your head up!";
    messageBox.style.display = 'block'; // Show the message box
    if (repsCount >= numReps) {
      stopAnalysis();
    }
  }
}

async function estimatePose(video, net) {
  const canvas = document.getElementById('output');
  const ctx = canvas.getContext('2d');
  canvas.width = video.width;
  canvas.height = video.height;

  async function detect() {
    const pose = await net.estimateSinglePose(video, {
      flipHorizontal: false
    });

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const keypoints = pose.keypoints.reduce((acc, point) => {
      if (['nose', 'rightEar', 'rightShoulder'].includes(point.part)) {
        acc[point.part] = point.position;
      }
      return acc;
    }, {});

    const { nose, rightEar, rightShoulder } = keypoints;

    const exercise = document.getElementById('exercise-selector').value;
    let angle = 0;

    if (exercise === 'headTiltBack') {
      angle = calculateAngle(nose, rightEar, rightShoulder);
    }

    // Set starting angle if not set
    if (startingAngle === null) {
      startingAngle = angle;
    }

    // Smooth the angle
    const smoothedAngle = smoothAngle(angle);

    // Display angle as a progress bar
    updateProgressBar(smoothedAngle);

    // Capture data only when actively counting and frame count matches the skip value
    if (isCounting && frameCount % frameSkip === 0) {
      const userMrn = document.getElementById('user-selector').value;
      // Send pose data to backend
      fetch('/save_pose', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ keypoints: JSON.stringify(pose.keypoints), angle: smoothedAngle, exercise: exercise, count: repsCount, test_uuid: testUuid, user_mrn: userMrn })
      });
    }

    // Draw keypoints and lines between them
    ctx.beginPath();
    ctx.arc(nose.x, nose.y, 5, 0, 2 * Math.PI);
    ctx.fill();
    ctx.moveTo(nose.x, nose.y);
    ctx.arc(rightEar.x, rightEar.y, 5, 0, 2 * Math.PI);
    ctx.fill();
    ctx.moveTo(rightEar.x, rightEar.y);
    ctx.arc(rightShoulder.x, rightShoulder.y, 5, 0, 2 * Math.PI);
    ctx.fill();

    // Draw lines between keypoints to form a triangle
    ctx.beginPath();
    ctx.moveTo(nose.x, nose.y);
    ctx.lineTo(rightEar.x, rightEar.y);
    ctx.lineTo(rightShoulder.x, rightShoulder.y);
    ctx.lineTo(nose.x, nose.y);
    ctx.strokeStyle = 'red';
    ctx.lineWidth = 2;
    ctx.stroke();

    frameCount++;
    animationFrameId = requestAnimationFrame(detect);
  }

  detect();
}

function stopAnalysis() {
  isCounting = false;
  repsCount = 0;
  startingAngle = null;
  if (animationFrameId) {
    cancelAnimationFrame(animationFrameId);
  }
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
  }
  document.getElementById('message-box').style.display = 'none';
  alert("Exercise stopped. Please re-enter the values to start again.");
}
