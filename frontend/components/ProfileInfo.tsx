"use client";

import { useSession } from "next-auth/react";
import { useUserProfile } from "@/hooks/useUserProfile";
import { User, Calendar } from "lucide-react";

interface ProfileInfoProps {
  compact?: boolean;
}

export default function ProfileInfo({ compact = false }: ProfileInfoProps) {
  const { data: session } = useSession();
  const { profile } = useUserProfile();

  if (!session?.user) return null;

  const formatDate = (dateString?: string) => {
    if (!dateString) return "Not provided";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const getGenderLabel = (gender?: string) => {
    if (!gender) return "Not provided";
    return gender.charAt(0).toUpperCase() + gender.slice(1).replace("-", " ");
  };

  if (compact) {
    return (
      <div className="glass rounded-2xl border border-white/80 p-4 md:min-w-fit">
        <div className="flex items-center gap-3">
          <div className="relative">
            {session.user.image ? (
              // eslint-disable-next-line @next/next/no-img-element
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
            {profile?.gender && (
              <p className="text-xs text-slate-500">
                {getGenderLabel(profile.gender)} • {formatDate(profile.dob)}
              </p>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="glass rounded-3xl border border-white/80 p-6 md:p-8">
      <h2 className="text-xl font-bold text-slate-900 mb-6">Profile Information</h2>

      <div className="space-y-6">
        {/* Profile Section */}
        <div className="flex items-center gap-4 pb-6 border-b border-slate-200">
          <div className="relative">
            {session.user.image ? (
              // eslint-disable-next-line @next/next/no-img-element
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

        {/* Gender and DOB */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <User size={16} className="text-orange-600" />
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-600">
                Gender
              </p>
            </div>
            <p className="text-base font-semibold text-slate-900">
              {getGenderLabel(profile?.gender)}
            </p>
          </div>

          <div>
            <div className="flex items-center gap-2 mb-2">
              <Calendar size={16} className="text-orange-600" />
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-600">
                Date of Birth
              </p>
            </div>
            <p className="text-base font-semibold text-slate-900">
              {formatDate(profile?.dob)}
            </p>
          </div>
        </div>

        {/* Organization and Role */}
        {profile?.organization && (
          <div className="pt-4 border-t border-slate-200">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-600 mb-2">
                  Organization
                </p>
                <p className="text-base font-semibold text-slate-900">
                  {profile.organization}
                </p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-600 mb-2">
                  Role
                </p>
                <p className="text-base font-semibold text-slate-900 capitalize">
                  {profile.role}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
