// ========================================
// Detection Page JavaScript
// FR2: Text Detection
// FR3: Image Detection
// FR4: URL Verification
// FR5: Results Display
// FR6: Safety Recommendations
// FR7: Report Job Modal
// FR10: Save to History
// FR11: User Feedback & Model Improvement ← NEW
// ========================================

let currentImageFile = null;
let currentResult = null;

// ========================================
// FR11: NEW VARIABLE ADDED
// ========================================
let inlineSelectedRating = null;

document.addEventListener("DOMContentLoaded", function () {
  checkAuthentication();
  setupEventListeners();
  loadUserName();
});

function checkAuthentication() {
  const token = localStorage.getItem("token");
  if (!token) {
    window.location.href = "Login.html";
  }
}

function loadUserName() {
  const userName = localStorage.getItem("userName") || "User";
  document.getElementById("userName").textContent = userName;
}

function setupEventListeners() {
  const jobText = document.getElementById("jobText");
  if (jobText) {
    jobText.addEventListener("input", function () {
      updateCharCount();
      validateTextInput();
    });
  }

  const jobUrl = document.getElementById("jobUrl");
  if (jobUrl) {
    jobUrl.addEventListener("input", validateUrl);
  }

  const uploadZone = document.getElementById("uploadZone");
  if (uploadZone) {
    uploadZone.addEventListener("dragover", handleDragOver);
    uploadZone.addEventListener("drop", handleDrop);
  }
}

// ========================================
// Tab Switching
// ========================================
function switchTab(tabName) {
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.classList.remove("active");
  });
  document.querySelectorAll(".content-card").forEach((card) => {
    card.classList.remove("active");
  });
  document.getElementById(tabName + "Tab").classList.add("active");
  document.getElementById(tabName + "Content").classList.add("active");
}

// ========================================
// FR2: Text Detection
// ========================================
function updateCharCount() {
  const jobText = document.getElementById("jobText").value;
  const charCount = document.getElementById("textCharCount");
  charCount.textContent = jobText.length;

  if (jobText.length < 50) {
    charCount.style.color = "#dc2626";
  } else if (jobText.length > 4500) {
    charCount.style.color = "#ea580c";
  } else {
    charCount.style.color = "#16a34a";
  }
}

function validateTextInput() {
  const jobText = document.getElementById("jobText").value;
  const validation = document.getElementById("textValidation");
  const analyzeBtn = document.getElementById("analyzeTextBtn");

  if (jobText.length < 50) {
    validation.textContent = "❌ Minimum 50 characters required";
    validation.className = "validation-msg error";
    analyzeBtn.disabled = true;
  } else if (jobText.length > 5000) {
    validation.textContent = "❌ Maximum 5000 characters allowed";
    validation.className = "validation-msg error";
    analyzeBtn.disabled = true;
  } else {
    validation.textContent = "✓ Ready for analysis";
    validation.className = "validation-msg success";
    analyzeBtn.disabled = false;
  }
}

function clearText() {
  document.getElementById("jobText").value = "";
  updateCharCount();
  validateTextInput();
}

async function analyzeText() {
  const jobText = document.getElementById("jobText").value;

  if (jobText.length < 50) {
    alert("Please enter at least 50 characters");
    return;
  }

  showLoading("Analyzing job description...");

  try {
    const response = await detectTextAPI({ job_text: jobText });

    if (response.error) {
      hideLoading();
      alert("Error: " + response.error);
      return;
    }

    currentResult = response;
    currentResult.job_text = jobText;

    hideLoading();
    displayResults(response);
  } catch (error) {
    hideLoading();
    alert("Error analyzing text: " + error.message);
  }
}

// ========================================
// FR3: Image Detection
// ========================================
function handleImageUpload(event) {
  const file = event.target.files[0];
  processImageFile(file);
}

function handleDragOver(e) {
  e.preventDefault();
  e.stopPropagation();
}

function handleDrop(e) {
  e.preventDefault();
  e.stopPropagation();
  const file = e.dataTransfer.files[0];
  processImageFile(file);
}

function processImageFile(file) {
  const validation = document.getElementById("imageValidation");
  const analyzeBtn = document.getElementById("analyzeImageBtn");

  const validTypes = ["image/jpeg", "image/jpg", "image/png"];
  if (!validTypes.includes(file.type)) {
    validation.textContent = "❌ Only JPG, JPEG, PNG formats allowed";
    validation.className = "validation-msg error";
    return;
  }

  if (file.size > 5 * 1024 * 1024) {
    validation.textContent = "❌ File size must be less than 5MB";
    validation.className = "validation-msg error";
    return;
  }

  currentImageFile = file;
  showImagePreview(file);
  validation.textContent = "✓ Image ready for analysis";
  validation.className = "validation-msg success";
  analyzeBtn.disabled = false;
}

function showImagePreview(file) {
  const reader = new FileReader();
  reader.onload = function (e) {
    document.getElementById("uploadZone").style.display = "none";
    document.getElementById("imagePreview").style.display = "block";
    document.getElementById("previewImg").src = e.target.result;
    document.getElementById("fileName").textContent = file.name;
    document.getElementById("fileSize").textContent =
      (file.size / 1024).toFixed(2) + " KB";
  };
  reader.readAsDataURL(file);
}

function removeImage() {
  currentImageFile = null;
  document.getElementById("uploadZone").style.display = "block";
  document.getElementById("imagePreview").style.display = "none";
  document.getElementById("imageInput").value = "";
  document.getElementById("analyzeImageBtn").disabled = true;
  document.getElementById("imageValidation").textContent = "";
}

async function analyzeImage() {
  if (!currentImageFile) {
    alert("Please upload an image first");
    return;
  }

  showLoading("Extracting text from image...");

  try {
    const response = await detectImageAPI(currentImageFile);

    if (response.error) {
      hideLoading();
      alert("Error: " + response.error);
      return;
    }

    currentResult = response;
    hideLoading();
    displayResults(response);
  } catch (error) {
    hideLoading();
    alert("Error analyzing image: " + error.message);
  }
}

// ========================================
// FR4: URL Verification
// ========================================
function validateUrl() {
  const urlInput = document.getElementById("jobUrl");
  const validation = document.getElementById("urlValidation");
  const verifyBtn = document.getElementById("verifyUrlBtn");
  const url = urlInput.value.trim();

  if (url === "") {
    validation.textContent = "";
    verifyBtn.disabled = true;
    return;
  }

  const urlPattern =
    /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/;

  if (!urlPattern.test(url)) {
    validation.textContent =
      "❌ Invalid URL format. Must start with http:// or https://";
    validation.className = "validation-msg error";
    verifyBtn.disabled = true;
  } else {
    validation.textContent = "✓ Valid URL format";
    validation.className = "validation-msg success";
    verifyBtn.disabled = false;
  }
}

async function verifyUrl() {
  const url = document.getElementById("jobUrl").value.trim();

  if (!url) {
    alert("Please enter a URL");
    return;
  }

  showLoading("Verifying domain...");

  try {
    const response = await verifyUrlAPI({ url: url });

    if (response.error) {
      hideLoading();
      alert("Error: " + response.error);
      return;
    }

    currentResult = response;
    currentResult.job_url = url;

    hideLoading();
    displayResults(response);
  } catch (error) {
    hideLoading();
    alert("Error verifying URL: " + error.message);
  }
}

// ========================================
// FR5: Display Results
// ========================================
function displayResults(result) {
  const resultsSection = document.getElementById("resultsSection");
  const riskPercentage = document.getElementById("riskPercentage");
  const riskLabel = document.getElementById("riskLabel");
  const riskBadge = document.getElementById("riskBadge");

  const riskScore = result.risk_score || result.riskScore || 0;
  const isFake = result.is_fake !== undefined ? result.is_fake : result.isFake;

  riskPercentage.textContent = riskScore + "%";

  let riskLevel, riskClass, riskColor;
  if (riskScore <= 30) {
    riskLevel = "Low Risk";
    riskClass = "low";
    riskColor = "#16a34a";
  } else if (riskScore <= 70) {
    riskLevel = "Medium Risk";
    riskClass = "medium";
    riskColor = "#ea580c";
  } else {
    riskLevel = "High Risk";
    riskClass = "high";
    riskColor = "#dc2626";
  }

  riskLabel.textContent = riskLevel;
  riskPercentage.style.color = riskColor;
  riskBadge.className = "risk-badge " + riskClass;
  riskBadge.querySelector(".badge-text").textContent = riskLevel;

  document.getElementById("detectionMethod").textContent =
    result.method || "Analysis";
  document.getElementById("resultTitle").textContent = isFake
    ? "⚠️ Potential Fake Job Detected"
    : "✅ Job Appears Legitimate";

  // ✅ FR6: Awareness message — based on risk level
  showAwarenessMessage(riskScore, isFake);

  // Trust meter
  const trustScore = 100 - riskScore;
  document.getElementById("trustMeterFill").style.width = trustScore + "%";
  document.getElementById("trustMeterValue").textContent = trustScore + "%";

  // Indicators
  const indicatorsList = document.getElementById("suspiciousIndicators");
  indicatorsList.innerHTML = "";
  (result.indicators || []).forEach((indicator) => {
    const li = document.createElement("li");
    li.textContent = indicator;
    indicatorsList.appendChild(li);
  });

  // Reasons
  const reasonsDiv = document.getElementById("detailedReasons");
  reasonsDiv.innerHTML = "";
  (result.reasons || []).forEach((reason) => {
    const p = document.createElement("p");
    p.textContent = "• " + reason;
    p.style.padding = "8px 0";
    reasonsDiv.appendChild(p);
  });

  // Recommendations
  const recommendationsList = document.getElementById("safetyRecommendations");
  recommendationsList.innerHTML = "";
  (result.recommendations || []).forEach((rec) => {
    const li = document.createElement("li");
    li.textContent = rec;
    recommendationsList.appendChild(li);
  });

  // OCR extracted text
  if (result.extracted_text) {
    const extractedTextDiv = document.createElement("div");
    extractedTextDiv.className = "info-box";
    extractedTextDiv.innerHTML = `
      <strong>📝 Extracted Text (OCR):</strong>
      <p style="margin-top: 10px; white-space: pre-wrap;">${result.extracted_text}</p>
      <p style="margin-top: 10px; font-size: 14px; color: #666;">
        OCR Confidence: ${result.ocr_confidence ? result.ocr_confidence.toFixed(1) : "N/A"}%
      </p>`;
    reasonsDiv.parentElement.insertBefore(
      extractedTextDiv,
      reasonsDiv.parentElement.firstChild,
    );
  }

  // ========================================
  // FR11: Reset feedback for every new result
  // ========================================
  resetInlineFeedback();

  resultsSection.style.display = "flex";
}

// ========================================
// FR6: Awareness Messages
// Different messages based on risk level
// ========================================
function showAwarenessMessage(riskScore, isFake) {
  // Remove any existing awareness message
  const oldMsg = document.getElementById("awarenessMessage");
  if (oldMsg) oldMsg.remove();

  let message = "";
  let bgColor = "";
  let borderColor = "";

  if (riskScore <= 30) {
    // Low Risk
    bgColor = "#dcfce7";
    borderColor = "#16a34a";
    message = `
      <h4 style="color:#166534; margin-bottom:8px;">✅ Low Risk Job</h4>
      <p style="color:#166534; margin-bottom:8px;">This job posting appears legitimate. However, still follow these steps:</p>
      <ul style="color:#166534; padding-left:20px;">
        <li>Search the company name on Google and read reviews</li>
        <li>Visit the official website to verify the job listing</li>
        <li>The interview process should be normal — no payment required</li>
        <li>The offer letter should come from the company's official email</li>
      </ul>`;
  } else if (riskScore <= 70) {
    // Medium Risk
    bgColor = "#fef3c7";
    borderColor = "#ea580c";
    message = `
      <h4 style="color:#92400e; margin-bottom:8px;">⚠️ Medium Risk — Please Check Carefully!</h4>
      <p style="color:#92400e; margin-bottom:8px;">This job has some suspicious indicators. Before proceeding, make sure to:</p>
      <ul style="color:#92400e; padding-left:20px;">
        <li>🔍 Verify the company's physical address and phone number</li>
        <li>💰 Never make any payment or pay any fee</li>
        <li>📧 Check the recruiter's email — personal emails (gmail/yahoo) are a red flag</li>
        <li>🌐 Check the company website's SSL certificate (must have https)</li>
        <li>👥 Verify the company and recruiter on LinkedIn</li>
      </ul>`;
  } else {
    // High Risk
    bgColor = "#fee2e2";
    borderColor = "#dc2626";
    message = `
      <h4 style="color:#991b1b; margin-bottom:8px;">🚨 High Risk — This Job Appears to be FAKE!</h4>
      <p style="color:#991b1b; margin-bottom:8px;">The AI has detected serious fraud indicators in this job. Take these steps immediately:</p>
      <ul style="color:#991b1b; padding-left:20px;">
        <li>❌ Do NOT apply for this job</li>
        <li>❌ Do not share any personal information (ID card, bank details)</li>
        <li>❌ Do not make any payment or registration fee</li>
        <li>📢 Please report it using the "Report This Job" button below</li>
        <li>👮 File a complaint with FIA Cybercrime: 0800-02345</li>
        <li>🔒 If you have already shared any information, contact your bank immediately</li>
      </ul>`;
  }

  // Create and insert the awareness div into results
  const awarenessDiv = document.createElement("div");
  awarenessDiv.id = "awarenessMessage";
  awarenessDiv.style.cssText = `
    background: ${bgColor};
    border-left: 5px solid ${borderColor};
    border-radius: 8px;
    padding: 16px 20px;
    margin: 16px 0;
  `;
  awarenessDiv.innerHTML = message;

  // Insert at the top of the result body
  const resultBody = document.querySelector(".result-body");
  if (resultBody) {
    resultBody.insertBefore(awarenessDiv, resultBody.firstChild);
  }
}

// ========================================
// FR11: ONE LINE ADDED to closeResults
// ========================================
function closeResults() {
  document.getElementById("resultsSection").style.display = "none";
  resetInlineFeedback(); // FR11: reset feedback when closing
}

// ========================================
// FR10: Save to History
// ========================================
function saveToHistory() {
  // History is automatically saved in the backend
  // This button redirects the user to the history page
  if (confirm("Would you like to go to the History page?")) {
    window.location.href = "history.html";
  }
}

// ========================================
// FR7: Report Job Modal
// ========================================
function openReportModal() {
  document.getElementById("reportReason").value = "";
  document.getElementById("reportDescription").value = "";
  document.getElementById("reportCharCount").textContent = "0";
  document.getElementById("reasonError").classList.remove("show");
  document.getElementById("descriptionError").classList.remove("show");
  document.getElementById("reportSuccess").classList.remove("show");
  document.getElementById("reportForm").style.display = "block";
  document.getElementById("submitReportBtn").disabled = false;
  document.getElementById("submitReportBtn").textContent = "🚨 Submit Report";
  document.getElementById("reportModal").style.display = "flex";
}

function closeReportModal() {
  document.getElementById("reportModal").style.display = "none";
}

function updateReportCharCount() {
  const desc = document.getElementById("reportDescription").value;
  document.getElementById("reportCharCount").textContent = desc.length;
}

async function submitReport() {
  document.getElementById("reasonError").classList.remove("show");
  document.getElementById("descriptionError").classList.remove("show");

  const reason = document.getElementById("reportReason").value;
  const description = document.getElementById("reportDescription").value.trim();

  let hasError = false;

  if (!reason) {
    document.getElementById("reasonError").classList.add("show");
    hasError = true;
  }

  if (description.length < 10) {
    document.getElementById("descriptionError").classList.add("show");
    hasError = true;
  }

  if (hasError) return;

  const submitBtn = document.getElementById("submitReportBtn");
  submitBtn.disabled = true;
  submitBtn.textContent = "Submitting...";

  try {
    const reportData = {
      reason: reason,
      description: description,
      job_text: currentResult ? currentResult.job_text || "" : "",
      url: currentResult ? currentResult.job_url || "" : "",
    };

    const response = await reportJobAPI(reportData);

    if (response.success) {
      document.getElementById("reportForm").style.display = "none";
      document.getElementById("reportSuccess").classList.add("show");
      setTimeout(() => {
        closeReportModal();
      }, 2500);
    } else {
      alert("Error: " + (response.error || "Report failed. Please try again."));
      submitBtn.disabled = false;
      submitBtn.textContent = "🚨 Submit Report";
    }
  } catch (error) {
    alert("Network error. Please check your connection.");
    submitBtn.disabled = false;
    submitBtn.textContent = "🚨 Submit Report";
  }
}

// ========================================
// Loading Overlay
// ========================================
function showLoading(message) {
  document.getElementById("loadingText").textContent = message;
  document.getElementById("loadingOverlay").style.display = "flex";
}

function hideLoading() {
  document.getElementById("loadingOverlay").style.display = "none";
}

// ========================================
// Logout
// ========================================
function logout() {
  if (confirm("Are you sure you want to logout?")) {
    localStorage.removeItem("token");
    localStorage.removeItem("userName");
    window.location.href = "Login.html";
  }
}

// ========================================
// FR11: User Feedback & Model Improvement
// ← ALL NEW CODE — nothing above changed
// ========================================

function selectInlineRating(rating) {
  inlineSelectedRating = rating;
  document.getElementById("inlineThumbsUp").classList.remove("selected");
  document.getElementById("inlineThumbsDown").classList.remove("selected");
  if (rating === "thumbs_up") {
    document.getElementById("inlineThumbsUp").classList.add("selected");
  } else {
    document.getElementById("inlineThumbsDown").classList.add("selected");
  }
  document.getElementById("inlineRatingError").style.display = "none";
}

function updateInlineCharCount() {
  const val = document.getElementById("inlineFeedbackComment").value.length;
  document.getElementById("inlineCharCount").textContent = val;
}

async function submitInlineFeedback() {
  // Validation: rating is mandatory
  if (!inlineSelectedRating) {
    document.getElementById("inlineRatingError").style.display = "block";
    return;
  }

  // Validation: comment max 200 characters
  const comment = document.getElementById("inlineFeedbackComment").value.trim();
  if (comment.length > 200) {
    alert("⚠️ Comment must be less than 200 characters");
    return;
  }

  const submitBtn = document.getElementById("inlineFeedbackSubmitBtn");
  submitBtn.disabled = true;
  submitBtn.textContent = "Submitting...";

  try {
    // Link feedback to current detection result with metadata
    const feedbackData = {
      rating: inlineSelectedRating,
      comment: comment,
      detection_method: currentResult
        ? currentResult.method || "Unknown"
        : "Unknown",
      risk_score: currentResult ? currentResult.risk_score || 0 : 0,
      prediction: currentResult
        ? currentResult.prediction || "Unknown"
        : "Unknown",
    };

    const response = await submitFeedbackAPI(feedbackData);

    if (response.success) {
      // Hide form, show success confirmation
      document.getElementById("inlineRatingButtons").style.display = "none";
      document.getElementById("inlineCommentWrap").style.display = "none";
      submitBtn.style.display = "none";
      document.getElementById("inlineRatingError").style.display = "none";

      // Show updated accuracy metrics + improvement suggestion
      const metrics = response.accuracy_metrics;
      document.getElementById("inlineSatisfactionMsg").textContent =
        `📊 User Satisfaction Rate: ${metrics.user_satisfaction_rate}% ` +
        `(${metrics.positive_ratings} accurate out of ${metrics.total_feedback} total)`;
      document.getElementById("inlineImprovementMsg").textContent =
        `💡 ${response.model_improvement_suggestion}`;

      // Show thank you message
      document.getElementById("inlineFeedbackSuccess").style.display = "block";
    } else {
      alert(
        "Error: " + (response.error || "Feedback failed. Please try again."),
      );
      submitBtn.disabled = false;
      submitBtn.textContent = "📤 Submit Feedback";
    }
  } catch (error) {
    alert("Network error. Please check your connection.");
    submitBtn.disabled = false;
    submitBtn.textContent = "📤 Submit Feedback";
  }
}

function resetInlineFeedback() {
  inlineSelectedRating = null;

  const thumbsUp = document.getElementById("inlineThumbsUp");
  const thumbsDown = document.getElementById("inlineThumbsDown");
  if (thumbsUp) thumbsUp.classList.remove("selected");
  if (thumbsDown) thumbsDown.classList.remove("selected");

  const commentEl = document.getElementById("inlineFeedbackComment");
  if (commentEl) commentEl.value = "";

  const charCountEl = document.getElementById("inlineCharCount");
  if (charCountEl) charCountEl.textContent = "0";

  const ratingError = document.getElementById("inlineRatingError");
  if (ratingError) ratingError.style.display = "none";

  const successEl = document.getElementById("inlineFeedbackSuccess");
  if (successEl) successEl.style.display = "none";

  const ratingBtns = document.getElementById("inlineRatingButtons");
  if (ratingBtns) ratingBtns.style.display = "flex";

  const commentWrap = document.getElementById("inlineCommentWrap");
  if (commentWrap) commentWrap.style.display = "block";

  const submitBtn = document.getElementById("inlineFeedbackSubmitBtn");
  if (submitBtn) {
    submitBtn.style.display = "block";
    submitBtn.disabled = false;
    submitBtn.textContent = "📤 Submit Feedback";
  }
}
