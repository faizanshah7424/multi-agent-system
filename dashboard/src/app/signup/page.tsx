'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { Activity, ShieldAlert, CheckCircle, ArrowRight, Loader } from 'lucide-react';

export default function SignupPage() {
  const { signup, isAuthenticated, error, setError } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('member');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successInfo, setSuccessInfo] = useState<{ message: string; verificationToken?: string } | null>(null);
  const router = useRouter();

  useEffect(() => {
    setError(null);
    if (isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, router, setError]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSuccessInfo(null);
    try {
      const res = await signup(email, password, role);
      setSuccessInfo({
        message: res.message,
        verificationToken: res.verification_token
      });
    } catch {
      // Error is handled by context
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col justify-center items-center p-4 relative overflow-hidden font-sans">
      {/* Background Decorative Gradients */}
      <div className="absolute top-1/4 left-1/4 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full bg-indigo-500/10 blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 translate-x-1/2 translate-y-1/2 w-96 h-96 rounded-full bg-purple-500/10 blur-3xl" />

      {/* Main Card */}
      <div className="w-full max-w-md bg-zinc-900/60 backdrop-blur-xl border border-zinc-800/80 rounded-2xl p-8 shadow-2xl relative z-10 animate-in fade-in duration-300">
        
        {/* Header Branding */}
        <div className="flex flex-col items-center mb-8">
          <div className="p-3 rounded-2xl bg-indigo-600/10 text-indigo-400 border border-indigo-500/20 mb-4 shadow-inner">
            <Activity className="h-8 w-8 animate-pulse" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Create Account</h2>
          <p className="text-sm text-zinc-400 mt-1.5 text-center">
            Register to join the Antigravity agent cluster
          </p>
        </div>

        {/* Success State */}
        {successInfo ? (
          <div className="space-y-6 text-center animate-in zoom-in duration-300">
            <div className="flex justify-center mb-2">
              <div className="p-3 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <CheckCircle className="h-10 w-10" />
              </div>
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-bold text-white">Registration Successful!</h3>
              <p className="text-sm text-zinc-400">{successInfo.message}</p>
            </div>

            {successInfo.verificationToken && (
              <div className="bg-zinc-950/80 border border-zinc-800 rounded-xl p-4 text-left space-y-3">
                <span className="block text-xs font-semibold text-zinc-500 uppercase tracking-widest">
                  Self-Verification Console
                </span>
                <p className="text-xs text-zinc-400">
                  Since email services are mocked in SQLite, you can manually trigger verification by clicking below:
                </p>
                <Link
                  href={`/verify-email?token=${successInfo.verificationToken}`}
                  className="inline-flex w-full justify-center items-center py-2 px-3 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-lg text-xs transition"
                >
                  Verify Account Now
                </Link>
              </div>
            )}

            <div className="pt-4 border-t border-zinc-800">
              <Link
                href="/login"
                className="w-full inline-flex justify-center py-2.5 px-4 bg-zinc-800 hover:bg-zinc-700 text-white font-medium rounded-xl text-sm transition"
              >
                Proceed to Login
              </Link>
            </div>
          </div>
        ) : (
          /* Sign Up Form */
          <>
            {error && (
              <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start space-x-3 text-red-400 text-sm animate-in shake duration-300">
                <ShieldAlert className="h-5 w-5 shrink-0 mt-0.5" />
                <span className="leading-relaxed">{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-2">
                  Email Address
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-zinc-950/80 border border-zinc-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/30 text-white rounded-xl px-4 py-3 text-sm transition outline-none"
                  placeholder="name@company.com"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-2">
                  Password
                </label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-zinc-950/80 border border-zinc-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/30 text-white rounded-xl px-4 py-3 text-sm transition outline-none"
                  placeholder="Min 6 characters"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-2">
                  System Role
                </label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full bg-zinc-950/80 border border-zinc-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/30 text-white rounded-xl px-4 py-3 text-sm transition outline-none appearance-none"
                >
                  <option value="member">Member (Read Telemetry)</option>
                  <option value="developer">Developer (Trigger Executions)</option>
                  <option value="admin">Administrator (Full Control)</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white font-medium rounded-xl text-sm transition-all duration-200 flex items-center justify-center space-x-2 shadow-lg shadow-indigo-600/20 disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-indigo-600/30 active:scale-[0.98]"
              >
                {isSubmitting ? (
                  <>
                    <Loader className="h-4 w-4 animate-spin" />
                    <span>Deploying profile...</span>
                  </>
                ) : (
                  <>
                    <span>Sign Up</span>
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </form>

            <div className="mt-8 text-center text-sm text-zinc-400 border-t border-zinc-800/60 pt-6">
              Already have an account?{' '}
              <Link href="/login" className="text-indigo-400 hover:text-indigo-300 font-semibold transition">
                Sign in
              </Link>
            </div>
          </>
        )}

      </div>
    </div>
  );
}
