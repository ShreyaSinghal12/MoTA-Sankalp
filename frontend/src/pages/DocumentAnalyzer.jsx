import { useState } from "react";
import { getToken } from "../api.js";

const API_ROOT = "http://127.0.0.1:8000";

export default function DocumentAnalyzer() {
  const [applicationId, setApplicationId] = useState("1");
  const [documentType, setDocumentType] = useState("CASTE_CERTIFICATE");
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");

  async function analyze() {
    if (!file) {
      setError("Please select a document image.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);
    setStatus("Uploading document...");

    try {
      const formData = new FormData();

      formData.append("application_id", applicationId);
      formData.append("document_type", documentType);
      formData.append("file", file);

      setStatus("AI is analyzing the document...");

      const response = await fetch(
        `${API_ROOT}/api/v1/documents/analyze`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${getToken()}`,
          },
          body: formData,
        }
      );

      console.log("Response status:", response.status);

      const responseText = await response.text();

      console.log("Backend response:", responseText);

      if (!response.ok) {
        let message = "Document analysis failed";

        try {
          const errorData = JSON.parse(responseText);
          message = errorData.detail || message;
        } catch {
          message = responseText || message;
        }

        throw new Error(message);
      }

      let data;

      try {
        data = JSON.parse(responseText);
      } catch {
        throw new Error(
          "Backend returned an invalid JSON response."
        );
      }

      console.log("Analysis result:", data);

      setResult(data);
      setStatus("Analysis completed successfully.");
    } catch (err) {
      console.error("Document analysis error:", err);
      setError(err.message || "Document analysis failed.");
      setStatus("");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        padding: "24px",
        maxWidth: "1000px",
        margin: "0 auto",
      }}
    >
      <h1>AI Document Analyzer</h1>

      <p style={{ color: "#666" }}>
        Upload a scholarship document to run OCR, YOLO detection,
        document-type verification and tampering checks.
      </p>

      <div
        style={{
          background: "#fff",
          padding: "20px",
          borderRadius: "12px",
          marginTop: "20px",
        }}
      >
        <div style={{ marginBottom: "16px" }}>
          <label>Application ID</label>
          <br />

          <input
            type="number"
            value={applicationId}
            onChange={(e) => setApplicationId(e.target.value)}
            style={{
              padding: "8px",
              marginTop: "6px",
              width: "200px",
            }}
          />
        </div>

        <div style={{ marginBottom: "16px" }}>
          <label>Document Type</label>
          <br />

          <select
            value={documentType}
            onChange={(e) => setDocumentType(e.target.value)}
            style={{
              padding: "8px",
              marginTop: "6px",
              width: "220px",
            }}
          >
            <option value="CASTE_CERTIFICATE">
              Caste Certificate
            </option>

            <option value="INCOME_CERTIFICATE">
              Income Certificate
            </option>

            <option value="MARK_SHEET">
              Mark Sheet
            </option>
          </select>
        </div>

        <div style={{ marginBottom: "16px" }}>
          <label>Document Image</label>
          <br />

          <input
            type="file"
            accept=".jpg,.jpeg,.png"
            onChange={(e) => setFile(e.target.files[0])}
            style={{ marginTop: "8px" }}
          />
        </div>

        <button
          onClick={analyze}
          disabled={loading}
          style={{
            padding: "10px 18px",
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "Analyzing..." : "Analyze Document"}
        </button>

        {status && (
          <p
            style={{
              marginTop: "16px",
              color: "blue",
              fontWeight: "500",
            }}
          >
            {status}
          </p>
        )}

        {error && (
          <div
            style={{
              marginTop: "16px",
              padding: "12px",
              background: "#ffe5e5",
              color: "red",
              borderRadius: "8px",
            }}
          >
            <strong>Error:</strong> {error}
          </div>
        )}
      </div>

      {result && (
        <div
          style={{
            background: "#fff",
            padding: "20px",
            borderRadius: "12px",
            marginTop: "20px",
          }}
        >
          <h2>Analysis Result</h2>

          <p>
            <strong>Recommendation:</strong>{" "}
            {result.recommendation || "N/A"}
          </p>

          <p>
            <strong>Declared Type:</strong>{" "}
            {result.declared_document_type || "N/A"}
          </p>

          <p>
            <strong>Detected Type:</strong>{" "}
            {result.ocr?.detected_document_type || "UNKNOWN"}
          </p>

          <p>
            <strong>OCR Confidence:</strong>{" "}
            {result.ocr?.confidence ?? 0}
          </p>

          <p>
            <strong>Type Match Score:</strong>{" "}
            {result.ocr?.type_match_score ?? 0}
          </p>

          <h3>Flags</h3>

          {Array.isArray(result.flags) && result.flags.length > 0 ? (
            <ul>
              {result.flags.map((flag, index) => (
                <li key={index}>{flag}</li>
              ))}
            </ul>
          ) : (
            <p>No issues found.</p>
          )}

          <h3>YOLO Detection</h3>

          <pre
            style={{
              background: "#f5f5f5",
              padding: "12px",
              overflowX: "auto",
              borderRadius: "8px",
            }}
          >
            {JSON.stringify(
              result.yolo_detection,
              null,
              2
            )}
          </pre>

          <h3>OCR Text</h3>

          <pre
            style={{
              background: "#f5f5f5",
              padding: "12px",
              whiteSpace: "pre-wrap",
              borderRadius: "8px",
            }}
          >
            {result.ocr?.text || "No text detected"}
          </pre>
        </div>
      )}
    </div>
  );
}