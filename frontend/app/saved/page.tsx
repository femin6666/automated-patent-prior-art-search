"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Sidebar from "@/components/Sidebar";
import { SavedPatent } from "@/types";
import { api } from "@/services/api";
import { formatDate } from "@/lib/utils";
import {
  Bookmark,
  Building2,
  Calendar,
  Trash2,
  Edit3,
  ExternalLink,
  Loader2,
  Check
} from "lucide-react";

export default function SavedPatentsPage() {
  const [savedList, setSavedList] = useState<SavedPatent[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [noteText, setNoteText] = useState("");

  const loadSaved = async () => {
    try {
      const data = await api.getSavedPatents();
      setSavedList(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSaved();
  }, []);

  const handleUnsave = async (patentId: string) => {
    try {
      await api.unsavePatent(patentId);
      setSavedList(savedList.filter((s) => s.patent_id !== patentId));
    } catch (err: any) {
      alert("Failed to unsave patent: " + err.message);
    }
  };

  const startEditNote = (saved: SavedPatent) => {
    setEditingId(saved.patent_id);
    setNoteText(saved.notes || "");
  };

  const saveNote = async (patentId: string) => {
    try {
      const updated = await api.savePatent(patentId, noteText);
      setSavedList(savedList.map((s) => (s.patent_id === patentId ? updated : s)));
      setEditingId(null);
    } catch (err: any) {
      alert("Failed to save notes: " + err.message);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 flex">
      <Sidebar />

      <main className="flex-1 p-8 overflow-y-auto z-10">
        <div className="max-w-6xl mx-auto space-y-6">
          
          {/* Header */}
          <div className="pb-4 border-b border-zinc-800/80">
            <h1 className="text-2xl font-bold text-zinc-100 tracking-tight">Saved Patents</h1>
            <p className="text-xs text-zinc-400 mt-0.5">
              Your bookmarked prior-art patents and research annotations.
            </p>
          </div>

          {loading ? (
            <div className="py-12 text-center">
              <Loader2 className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
            </div>
          ) : savedList.length === 0 ? (
            <div className="p-12 text-center rounded-xl tech-card space-y-2 text-xs text-zinc-500">
              <Bookmark className="w-6 h-6 text-zinc-600 mx-auto" />
              <p>You haven't saved any patents yet.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {savedList.map((item) => {
                const p = item.patent;
                const isEditing = editingId === p.id;

                return (
                  <div
                    key={item.id}
                    className="p-5 rounded-xl tech-card space-y-3 relative"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-zinc-800/80">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-zinc-900 text-zinc-300 border border-zinc-800">
                            {p.domain}
                          </span>
                          <span className="font-mono text-xs font-semibold text-indigo-400">{p.patent_number}</span>
                        </div>
                        <Link href={`/patents/${p.id}`} className="text-base font-bold text-zinc-100 hover:text-indigo-400 transition-colors">
                          {p.title}
                        </Link>
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleUnsave(p.id)}
                          className="px-2.5 py-1 rounded-lg bg-zinc-900 text-rose-400 hover:bg-zinc-800 border border-zinc-800 text-xs font-medium flex items-center gap-1.5 transition-all"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                          <span>Remove</span>
                        </button>
                      </div>
                    </div>

                    <p className="text-xs text-zinc-300 line-clamp-2 leading-relaxed">{p.abstract}</p>

                    {/* Personal Notes Section */}
                    <div className="p-3.5 rounded-lg bg-zinc-950 border border-zinc-800 space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-mono font-semibold text-zinc-500 uppercase tracking-wider">
                          Personal Research Notes
                        </span>
                        {!isEditing && (
                          <button
                            onClick={() => startEditNote(item)}
                            className="text-xs text-indigo-400 hover:underline flex items-center gap-1 font-mono"
                          >
                            <Edit3 className="w-3 h-3" />
                            <span>{item.notes ? "Edit Note" : "Add Note"}</span>
                          </button>
                        )}
                      </div>

                      {isEditing ? (
                        <div className="space-y-2">
                          <textarea
                            rows={3}
                            value={noteText}
                            onChange={(e) => setNoteText(e.target.value)}
                            placeholder="Add your research observations, potential claim overlaps..."
                            className="w-full p-2.5 rounded-lg tech-input text-xs text-zinc-100 placeholder-zinc-500"
                          />
                          <div className="flex justify-end gap-2">
                            <button
                              onClick={() => setEditingId(null)}
                              className="px-3 py-1 rounded-lg bg-zinc-900 border border-zinc-800 text-xs text-zinc-400 hover:bg-zinc-800 transition-all"
                            >
                              Cancel
                            </button>
                            <button
                              onClick={() => saveNote(p.id)}
                              className="px-3 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium flex items-center gap-1 shadow-sm shadow-indigo-500/20 transition-all"
                            >
                              <Check className="w-3.5 h-3.5" />
                              <span>Save Note</span>
                            </button>
                          </div>
                        </div>
                      ) : (
                        <p className="text-xs text-zinc-300 italic">
                          {item.notes || "No research notes added yet."}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

        </div>
      </main>
    </div>
  );
}
