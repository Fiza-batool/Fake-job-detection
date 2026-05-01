// ========================================
// services/api.js
// API calls for Frontend to Backend
// FR1: Authentication
// FR2: Text Detection
// FR3: Image Detection
// FR4: URL Verification
// FR7: Report Job
// FR11: User Feedback & Model Improvement  ← NEW
// ========================================

const API_BASE_URL = "http://127.0.0.1:5000";

// ========================================
// Helper Functions
// ========================================

// Convert File to Base64
function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      const base64 = reader.result.split(",")[1];
      resolve(base64);
    };
    reader.onerror = (error) => reject(error);
  });
}

// ========================================
// FR1: AUTHENTICATION
// ========================================

function registerUser(data) {
  return fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success && data.token) {
        localStorage.setItem("token", data.token);
        localStorage.setItem("userName", data.user.name);
        localStorage.setItem("userEmail", data.user.email);
      }
      return data;
    });
}

function loginUser(data) {
  return fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success && data.token) {
        localStorage.setItem("token", data.token);
        localStorage.setItem("userName", data.user.name);
        localStorage.setItem("userEmail", data.user.email);
      }
      return data;
    });
}

// ========================================
// FR2: TEXT DETECTION
// ✅ FIX: risk_score ab probabilities.fake se aa raha hai
// Pehle problem:
//   Fake job 60% confidence → risk_score = 60% → Medium dikhta tha
// Ab fix:
//   probabilities.fake directly use → 95% fake = 95% risk = HIGH
// ========================================

async function detectTextAPI(data) {
  try {
    const res = await fetch(`${API_BASE_URL}/job/detect/text`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    const result = await res.json();

    if (!result.success) {
      return result;
    }

    // ✅ FIXED: probabilities.fake directly = risk score
    // Pehle: result.prediction === "Fake" ? result.confidence : 100 - result.confidence
    const riskScore = Math.round(
      result.probabilities
        ? result.probabilities.fake
        : result.prediction === "Fake"
          ? result.confidence
          : 100 - result.confidence,
    );

    return {
      success: result.success,
      prediction: result.prediction,
      confidence: result.confidence,
      risk_score: riskScore, // ✅ FIXED
      is_fake: result.prediction === "Fake",
      method: "Text Analysis (NLP)",
      model_used: result.model_used,
      indicators: [
        result.prediction === "Fake"
          ? "⚠ Suspicious language patterns detected"
          : "✓ Professional job description",
        `Model confidence: ${result.confidence.toFixed(1)}%`,
        result.prediction === "Fake"
          ? "⚠ Common scam indicators found"
          : "✓ Legitimate indicators present",
      ],
      reasons: [
        `AI Model detected ${result.confidence.toFixed(1)}% probability of ${result.prediction.toLowerCase()} job`,
        result.prediction === "Fake"
          ? "Text contains patterns found in fraudulent ads"
          : "Job description follows professional standards",
        `Analyzed using ${result.model_used} with ${result.model_accuracy} accuracy`,
      ],
      recommendations:
        result.prediction === "Fake"
          ? [
              "❌ DO NOT provide personal information",
              "❌ DO NOT make any payments",
              "🔍 Verify company independently",
              "📢 Report if confirmed fake",
            ]
          : [
              "✓ Still verify company details",
              "✓ Check company reviews online",
              "✓ Never pay for job applications",
              "✓ Use official company emails",
            ],
    };
  } catch (error) {
    console.error("Text detection error:", error);
    return { success: false, error: error.message };
  }
}

// ========================================
// FR3: IMAGE DETECTION (BASE64)
// ✅ FIX: Same risk_score fix as text detection
// ========================================

async function detectImageAPI(imageFile) {
  try {
    const base64Image = await fileToBase64(imageFile);

    const res = await fetch(`${API_BASE_URL}/job/detect/image`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        image: base64Image,
        filename: imageFile.name,
      }),
    });

    const result = await res.json();

    if (!result.success) {
      return result;
    }

    // ✅ FIXED: Same fix as detectTextAPI
    const riskScore = Math.round(
      result.probabilities
        ? result.probabilities.fake
        : result.prediction === "Fake"
          ? result.confidence
          : 100 - result.confidence,
    );

    return {
      success: result.success,
      prediction: result.prediction,
      confidence: result.confidence,
      risk_score: riskScore, // ✅ FIXED
      is_fake: result.prediction === "Fake",
      method: "Image Analysis (OCR + NLP)",
      extracted_text: result.extracted_text,
      ocr_confidence: result.ocr_confidence,
      model_used: result.model_used,
      indicators: [
        `📷 OCR confidence: ${result.ocr_confidence.toFixed(1)}%`,
        result.prediction === "Fake"
          ? "⚠ Suspicious content in image"
          : "✓ Legitimate content detected",
        "✓ Text successfully extracted and analyzed",
      ],
      reasons: [
        `Text extracted from image with ${result.ocr_confidence.toFixed(1)}% confidence`,
        `AI Model detected ${result.confidence.toFixed(1)}% probability of ${result.prediction.toLowerCase()} job`,
        result.prediction === "Fake"
          ? "Fraudulent patterns found in extracted text"
          : "Professional content detected",
      ],
      recommendations:
        result.prediction === "Fake"
          ? [
              "❌ DO NOT trust this job posting",
              "❌ DO NOT provide personal information",
              "📢 Report this image if confirmed fake",
            ]
          : [
              "✓ Verify company through official channels",
              "✓ Check for additional red flags",
              "✓ Research company independently",
            ],
    };
  } catch (error) {
    console.error("Image detection error:", error);
    return { success: false, error: error.message };
  }
}

// ========================================
// FR4: URL VERIFICATION
// (Koi change nahi — URL ka apna scoring system hai)
// ========================================

async function verifyUrlAPI(data) {
  try {
    const res = await fetch(`${API_BASE_URL}/job/verify/url`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    const result = await res.json();

    if (!result.success) {
      return result;
    }

    return {
      success: result.success,
      is_safe: result.is_safe,
      risk_score: result.risk_score,
      is_fake: !result.is_safe,
      method: "URL/Domain Verification",
      domain_info: result.domain_info,
      ssl_status: result.ssl_status,
      domain_age: result.domain_age,
      trust_score: result.trust_score,
      indicators: [
        result.ssl_status === "Valid"
          ? "✓ Valid SSL certificate"
          : "✗ No SSL certificate",
        result.domain_age > 365
          ? `✓ Domain age: ${Math.floor(result.domain_age / 365)} years`
          : `⚠ Recently registered (${result.domain_age} days)`,
        result.trust_score > 70 ? "✓ High trust score" : "⚠ Low trust score",
      ],
      reasons: [
        !result.is_safe
          ? "Domain has suspicious characteristics"
          : "Domain appears legitimate",
        result.domain_age < 90
          ? "Very recently registered domain (red flag)"
          : "Domain has established history",
        result.ssl_status !== "Valid"
          ? "Website lacks proper security"
          : "Security properly configured",
      ],
      recommendations: !result.is_safe
        ? [
            "❌ Avoid this website",
            "❌ DO NOT enter personal information",
            "❌ DO NOT make payments",
            "🔍 Search for official company website",
          ]
        : [
            "✓ Domain appears safe but verify",
            "✓ Check company contact information",
            "✓ Look for company reviews",
            "✓ Ensure it's the official website",
          ],
    };
  } catch (error) {
    console.error("URL verification error:", error);
    return { success: false, error: error.message };
  }
}

// ========================================
// FR7: REPORT JOB
// ========================================

async function reportJobAPI(data) {
  try {
    const res = await fetch(`${API_BASE_URL}/job/report`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    const result = await res.json();
    return result;
  } catch (error) {
    console.error("Report job error:", error);
    return { success: false, error: error.message };
  }
}

// ========================================
// Backward Compatibility
// ========================================

async function detectJobAPI(data) {
  console.warn("detectJobAPI is deprecated. Use detectTextAPI instead.");
  return await detectTextAPI(data);
}

// ========================================
// ATTACH TO WINDOW (Global Access)
// ========================================

window.registerUser = registerUser;
window.loginUser = loginUser;
window.detectTextAPI = detectTextAPI;
window.detectImageAPI = detectImageAPI;
window.verifyUrlAPI = verifyUrlAPI;
window.detectJobAPI = detectJobAPI;
window.reportJobAPI = reportJobAPI;

// ========================================
// FR11: USER FEEDBACK & MODEL IMPROVEMENT
// ← ALL NEW CODE — nothing above changed
// ========================================

/**
 * FR11: Submit user feedback on detection result
 * Sends rating + comment + detection metadata to backend
 * Returns: confirmation + accuracy metrics + improvement suggestion
 */
async function submitFeedbackAPI(data) {
  try {
    const res = await fetch(`${API_BASE_URL}/job/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    const result = await res.json();
    return result;
  } catch (error) {
    console.error("Feedback error:", error);
    return { success: false, error: error.message };
  }
}

/**
 * FR11: Get feedback statistics for feedback.html dashboard
 * Returns: total, positive, negative, satisfaction_rate, all feedback list
 */
async function getFeedbackStatsAPI() {
  try {
    const res = await fetch(`${API_BASE_URL}/job/feedback/stats`);
    const result = await res.json();
    return result;
  } catch (error) {
    console.error("Feedback stats error:", error);
    return { success: false, error: error.message };
  }
}

// FR11: Attach to window for global access
window.submitFeedbackAPI = submitFeedbackAPI;
window.getFeedbackStatsAPI = getFeedbackStatsAPI;
