"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import { User } from "@/types";
import { api } from "@/services/api";
import { formatDate } from "@/lib/utils";
import {
  User as UserIcon,
  Mail,
  Lock,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ShieldAlert
} from "lucide-react";

export default function ProfilePage() {
  const router = useRouter();

  const [user, setUser] = useState<User | null>(null);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");

  const [profileMsg, setProfileMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [passMsg, setPassMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const [loading, setLoading] = useState(true);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  useEffect(() => {
    async function loadProfile() {
      try {
        const u = await api.getMe();
        setUser(u);
        setName(u.name);
        setEmail(u.email);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadProfile();
  }, []);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileMsg(null);
    try {
      const updated = await api.updateProfile({ name, email });
      setUser(updated);
      setProfileMsg({ type: "success", text: "Profile details updated successfully." });
    } catch (err: any) {
      setProfileMsg({ type: "error", text: err.message || "Failed to update profile." });
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPassMsg(null);
    try {
      await api.changePassword({ current_password: currentPassword, new_password: newPassword });
      setPassMsg({ type: "success", text: "Password changed successfully." });
      setCurrentPassword("");
      setNewPassword("");
    } catch (err: any) {
      setPassMsg({ type: "error", text: err.message || "Failed to change password." });
    }
  };

  const handleDeleteAccount = async () => {
    try {
      await api.deleteAccount();
      await api.logout();
      router.push("/register");
    } catch (err: any) {
      alert("Failed to delete account: " + err.message);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#09090b] text-zinc-100 flex">
        <Sidebar />
        <main className="flex-1 flex items-center justify-center p-8">
          <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 flex">
      <Sidebar />

      <main className="flex-1 p-8 overflow-y-auto z-10">
        <div className="max-w-4xl mx-auto space-y-6">
          
          {/* Header */}
          <div className="pb-4 border-b border-zinc-800/80">
            <h1 className="text-2xl font-bold text-zinc-100 tracking-tight">Account Profile Settings</h1>
            <p className="text-xs text-zinc-400 mt-0.5">
              Manage your personal information, security credentials, and account settings.
            </p>
          </div>

          {/* Edit Profile Info Form */}
          <div className="p-6 rounded-xl tech-card space-y-4">
            <h2 className="text-base font-bold text-zinc-100 flex items-center gap-2">
              <UserIcon className="w-4 h-4 text-indigo-400" />
              <span>Personal Information</span>
            </h2>

            {profileMsg && (
              <div
                className={`p-3 rounded-lg text-xs flex items-center gap-2 ${
                  profileMsg.type === "success"
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                    : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                }`}
              >
                {profileMsg.type === "success" ? <CheckCircle2 className="w-3.5 h-3.5" /> : <AlertCircle className="w-3.5 h-3.5" />}
                <span>{profileMsg.text}</span>
              </div>
            )}

            <form onSubmit={handleUpdateProfile} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-zinc-300 font-mono mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-lg tech-input text-xs text-zinc-100"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-300 font-mono mb-1">Email Address</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-lg tech-input text-xs text-zinc-100"
                />
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-sm shadow-indigo-500/20 transition-all"
                >
                  Save Profile Changes
                </button>
              </div>
            </form>
          </div>

          {/* Change Password Form */}
          <div className="p-6 rounded-xl tech-card space-y-4">
            <h2 className="text-base font-bold text-zinc-100 flex items-center gap-2">
              <Lock className="w-4 h-4 text-indigo-400" />
              <span>Change Password</span>
            </h2>

            {passMsg && (
              <div
                className={`p-3 rounded-lg text-xs flex items-center gap-2 ${
                  passMsg.type === "success"
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                    : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                }`}
              >
                {passMsg.type === "success" ? <CheckCircle2 className="w-3.5 h-3.5" /> : <AlertCircle className="w-3.5 h-3.5" />}
                <span>{passMsg.text}</span>
              </div>
            )}

            <form onSubmit={handleChangePassword} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-zinc-300 font-mono mb-1">Current Password</label>
                <input
                  type="password"
                  required
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-3.5 py-2 rounded-lg tech-input text-xs text-zinc-100"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-300 font-mono mb-1">New Password</label>
                <input
                  type="password"
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-3.5 py-2 rounded-lg tech-input text-xs text-zinc-100"
                />
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-sm shadow-indigo-500/20 transition-all"
                >
                  Update Password
                </button>
              </div>
            </form>
          </div>

          {/* Delete Account Box */}
          <div className="p-6 rounded-xl bg-rose-500/5 border border-rose-500/20 space-y-3">
            <h2 className="text-base font-bold text-rose-400 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4" />
              <span>Danger Zone</span>
            </h2>
            <p className="text-xs text-zinc-400">
              Permanently delete your user account and erase all associated searches, saved patents, and report history.
            </p>

            <button
              onClick={() => setShowDeleteModal(true)}
              className="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-medium text-xs shadow-sm shadow-rose-600/20 transition-all"
            >
              Delete Account
            </button>
          </div>

        </div>
      </main>

      {/* Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 bg-[#09090b]/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="p-6 rounded-xl tech-card max-w-sm w-full text-center space-y-4">
            <Trash2 className="w-8 h-8 text-rose-500 mx-auto" />
            <h3 className="text-base font-bold text-zinc-100">Confirm Account Deletion</h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Are you sure you want to permanently delete your account? This action cannot be undone.
            </p>
            <div className="flex gap-2 pt-1">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="flex-1 py-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300 text-xs font-medium hover:bg-zinc-800 transition-all"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteAccount}
                className="flex-1 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-medium transition-all shadow-sm shadow-rose-600/20"
              >
                Yes, Delete
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
