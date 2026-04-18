import axios from "axios";
import { AnalysisResult, ConversationMessage } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
});

// Response interceptor for error handling
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const message =
      err.response?.data?.detail || err.message || "An unexpected error occurred";
    return Promise.reject(new Error(message));
  }
);

// ── Text Analysis ────────────────────────────────────────────────
export async function analyzeText(text: string): Promise<AnalysisResult> {
  const { data } = await api.post("/analyze-text", { text });
  return data;
}

// ── Image Analysis ───────────────────────────────────────────────
export async function analyzeImage(formData: FormData): Promise<AnalysisResult> {
  const { data } = await api.post("/analyze-image", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

// ── Conversation Context Analysis ────────────────────────────────
export async function analyzeContext(
  messages: ConversationMessage[]
): Promise<AnalysisResult> {
  const { data } = await api.post("/analyze-context", { messages });
  return data;
}

// ── FIR Generation ───────────────────────────────────────────────
export async function generateFIR(
  analysisId: string
): Promise<{ fir_id: string }> {
  const { data } = await api.post("/generate-fir", { analysis_id: analysisId });
  return data;
}

export async function generateFIRPDF(payload: {
  fir_id: string;
  analysis_id: string;
  complainant_name: string;
  complainant_contact: string;
  complainant_address?: string;
  accused_name?: string;
  accused_details?: string;
  incident_date: string;
  incident_time?: string;
  incident_location?: string;
  additional_info?: string;
  legal_sections: string[];
  evidence_urls: string[];
}): Promise<void> {
  await api.post("/finalize-fir", payload);
}

export function downloadFIR(firId: string): void {
  window.open(`${API_BASE}/download-fir/${firId}`, "_blank");
}

// ── FIR History ──────────────────────────────────────────────────
export async function getFIRHistory(limit: number = 50, skip: number = 0) {
  const { data } = await api.get("/fir-history", { params: { limit, skip } });
  return data;
}

// ── Analytics ────────────────────────────────────────────────────
export async function fetchAnalytics() {
  const { data } = await api.get("/analytics");
  return data;
}
