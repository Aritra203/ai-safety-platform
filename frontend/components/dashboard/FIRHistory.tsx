"use client";

import { useEffect, useState } from "react";
import { Download, FileText, Calendar, User, AlertCircle, Loader2 } from "lucide-react";
import toast from "react-hot-toast";
import { downloadFIR, getFIRHistory } from "@/services/api";

interface FIRItem {
  fir_id: string;
  status: string;
  complainant_name: string;
  accused_name?: string;
  incident_date: string;
  incident_location?: string;
  created_at: string;
  finalized_at?: string;
  pdf_url?: string;
}

export default function FIRHistory() {
  const [firs, setFirs] = useState<FIRItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    fetchFIRHistory();
  }, []);

  const fetchFIRHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getFIRHistory(50, 0);
      setFirs(response.firs);
      setTotalCount(response.total);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to fetch FIR history";
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadFIR = (firId: string) => {
    try {
      downloadFIR(firId);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to download FIR";
      toast.error(message);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString("en-IN", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return dateString || "—";
    }
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      draft: "bg-yellow-100 text-yellow-800",
      finalized: "bg-green-100 text-green-800",
      pending: "bg-blue-100 text-blue-800",
    };
    return styles[status as keyof typeof styles] || "bg-gray-100 text-gray-800";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 size={20} className="animate-spin text-orange-500 mr-2" />
        <p className="text-slate-600">Loading FIR history...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-4">
        <div className="flex items-start gap-3">
          <AlertCircle size={18} className="text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-red-900">Error loading FIR history</p>
            <p className="text-sm text-red-700 mt-1">{error}</p>
            <button
              onClick={fetchFIRHistory}
              className="mt-3 px-3 py-1.5 text-sm font-semibold text-red-700 hover:bg-red-100 rounded transition"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (firs.length === 0) {
    return (
      <div className="text-center py-12">
        <FileText size={40} className="mx-auto text-slate-300 mb-3" />
        <p className="text-slate-600 font-medium">No FIR reports yet</p>
        <p className="text-sm text-slate-500 mt-1">Generate your first FIR from an analysis result</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-bold text-slate-900">FIR History</h3>
          <p className="text-sm text-slate-500 mt-0.5">{totalCount} total report{totalCount !== 1 ? "s" : ""}</p>
        </div>
        <button
          onClick={fetchFIRHistory}
          className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-300 hover:bg-slate-50 transition"
        >
          Refresh
        </button>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-200">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">FIR ID</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Complainant</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Against</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Date</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700">Status</th>
              <th className="px-4 py-3 text-center font-semibold text-slate-700">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {firs.map((fir) => (
              <tr key={fir.fir_id} className="hover:bg-slate-50 transition">
                <td className="px-4 py-3">
                  <code className="text-xs font-mono bg-slate-100 px-2 py-1 rounded text-slate-700">
                    {fir.fir_id}
                  </code>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <User size={14} className="text-slate-400" />
                    <span className="text-slate-900 font-medium truncate max-w-[200px]">
                      {fir.complainant_name || "—"}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3 text-slate-700 truncate max-w-[200px]">
                  {fir.accused_name || "—"}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <Calendar size={14} className="text-slate-400" />
                    <span className="text-slate-700">{formatDate(fir.incident_date)}</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold ${getStatusBadge(
                      fir.status
                    )}`}
                  >
                    {fir.status.charAt(0).toUpperCase() + fir.status.slice(1)}
                  </span>
                </td>
                <td className="px-4 py-3 text-center">
                  {fir.status === "finalized" ? (
                    <button
                      onClick={() => handleDownloadFIR(fir.fir_id)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-orange-600 hover:bg-orange-50 rounded transition"
                      title="Download PDF"
                    >
                      <Download size={14} />
                      Download
                    </button>
                  ) : (
                    <span className="text-xs text-slate-500">Not Ready</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
