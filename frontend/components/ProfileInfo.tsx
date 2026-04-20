"use client";

import { useSession } from "next-auth/react";

interface ProfileInfoProps {
  compact?: boolean;
}

export default function ProfileInfo({ compact = false }: ProfileInfoProps) {
  const { data: session } = useSession();

  if (!session?.user) return null;

  if (compact) {
    return (
      <div className="glass rounded-2xl border border-white/80 p-4 md:min-w-fit">
        <div className="flex items-center gap-3">
          <div className="relative">
            {session.user.image ? (
              <img
                src={session.user.image}
                alt={session.user.name || "User"}
                className="h-10 w-10 rounded-full border-2 border-orange-400 object-cover"
              />
            ) : (
              <div className="h-10 w-10 rounded-full border-2 border-orange-400 bg-gradient-to-br from-orange-400 to-amber-500 flex items-center justify-center text-white text-xs font-bold">
                {session.user.name?.charAt(0).toUpperCase() || "U"}
              </div>
            )}
          </div>
          <div className="text-sm">
            <p className="font-semibold text-slate-900">{session.user.name}</p>
            <p className="text-xs text-slate-600">{session.user.email}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="glass rounded-3xl border border-white/80 p-6 md:p-8">
      <h2 className="text-xl font-bold text-slate-900 mb-6">Profile Information</h2>

      <div className="space-y-6">
        <div className="flex items-center gap-4 pb-6 border-b border-slate-200">
          <div className="relative">
            {session.user.image ? (
              <img
                src={session.user.image}
                alt={session.user.name || "User"}
                className="h-20 w-20 rounded-full border-2 border-orange-400 object-cover"
              />
            ) : (
              <div className="h-20 w-20 rounded-full border-2 border-orange-400 bg-gradient-to-br from-orange-400 to-amber-500 flex items-center justify-center text-white text-2xl font-bold">
                {session.user.name?.charAt(0).toUpperCase() || "U"}
              </div>
            )}
          </div>
          <div>
            <p className="text-lg font-bold text-slate-900">{session.user.name}</p>
            <p className="text-sm text-slate-600">{session.user.email}</p>
          </div>
        </div>

      </div>
    </div>
  );
}
