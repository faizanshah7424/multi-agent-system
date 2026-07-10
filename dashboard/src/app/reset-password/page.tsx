'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { Activity, ShieldAlert, CheckCircle, ArrowRight, Loader } from 'lucide-react';

function ResetPasswordContent() {
  const { resetPassword, error, setError } = useAuth();
  const searchParams = useSearchParams();
  
  const token = searchParams.get('token');
  const [newPassword, setNewPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    setError(null);
  }, [setError]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) {
      setError('Reset token is missing in URL.');
      return;
    }
    setIsSubmitting(true);
    try {
      await resetPassword(token, newPassword);
      setSuccess(true);
    } catch {
      // Error is handled by context
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full max-w-md bg-zinc-900/60 backdrop-blur-xl border border-zinc-800/80 rounded-2xl p-8 shadow-2xl relative z-10 animate-in fade-in duration-300">
      
      {/* Header Branding */}
      <div className="flex flex-col items-center mb-8">
        <div className="p-3 rounded-2xl bg-indigo-600/10 text-indigo-400 border border-indigo-500/20 mb-4 shadow-inner">
          <Activity className="h-8 w-8 animate-pulse" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-white font-sans">Set New Password</h2>
        <p className="text-sm text-zinc-400 mt-1.5 text-center">
          Enter your new password below to recover your account
        </p>
      </div>

      {success ? (
        <div className="space-y-6 text-center animate-in zoom-in duration-200">
          <div className="flex justify-center">
            <div className="p-3 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <CheckCircle className="h-10 w-10" />
            </div>
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-bold text-white">Password Updated</h3>
            <p className="text-sm text-zinc-400">
              Your password has been successfully reset. You can now login using your new password.
            </p>
          </div>
          <div className="pt-4 border-t border-zinc-800">
            <Link
              href="/login"
              className="w-full inline-flex justify-center py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-xl text-sm transition"
            >
              Sign In
            </Link>
          </div>
        </div>
      ) : (
        <>
          {error && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start space-x-3 text-red-400 text-sm animate-in shake duration-300">
              <ShieldAlert className="h-5 w-5 shrink-0 mt-0.5" />
              <span className="leading-relaxed">{error}</span>
            </div>
          )}

          {!token && (
            <div className="mb-6 p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-xl flex items-start space-x-3 text-yellow-400 text-sm">
              <ShieldAlert className="h-5 w-5 shrink-0 mt-0.5" />
              <span className="leading-relaxed">
                Warning: No reset token was detected in the URL query string. Please check your reset link.
              </span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-2">
                New Password
              </label>
              <input
                type="password"
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full bg-zinc-950/80 border border-zinc-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/30 text-white rounded-xl px-4 py-3 text-sm transition outline-none"
                placeholder="Min 6 characters"
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting || !token}
              className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white font-medium rounded-xl text-sm transition-all duration-200 flex items-center justify-center space-x-2 shadow-lg shadow-indigo-600/20 disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-indigo-600/30 active:scale-[0.98]"
            >
              {isSubmitting ? (
                <>
                  <Loader className="h-4 w-4 animate-spin" />
                  <span>Updating password...</span>
                </>
              ) : (
                <>
                  <span>Save Password</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          <div className="mt-8 text-center text-sm text-zinc-400 border-t border-zinc-800/60 pt-6">
            <Link href="/login" className="text-indigo-400 hover:text-indigo-300 font-semibold transition">
              Back to Login
            </Link>
          </div>
        </>
      )}

    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col justify-center items-center p-4 relative overflow-hidden font-sans">
      {/* Background Decorative Gradients */}
      <div className="absolute top-1/4 left-1/4 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full bg-indigo-500/10 blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 translate-x-1/2 translate-y-1/2 w-96 h-96 rounded-full bg-purple-500/10 blur-3xl" />

      <Suspense fallback={
        <div className="w-full max-w-md bg-zinc-900/60 backdrop-blur-xl border border-zinc-800/80 rounded-2xl p-8 shadow-2xl relative z-10 text-center text-white">
          <Loader className="h-10 w-10 text-indigo-500 animate-spin mx-auto mb-4" />
          <p className="text-sm text-zinc-400">Loading reset context...</p>
        </div>
      }>
        <ResetPasswordContent />
      </Suspense>
    </div>
  );
}
