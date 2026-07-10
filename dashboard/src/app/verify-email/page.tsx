'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { Activity, ShieldAlert, CheckCircle, Loader } from 'lucide-react';

function VerifyEmailContent() {
  const { verifyEmail } = useAuth();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying');
  const [errMessage, setErrMessage] = useState('');

  const token = searchParams.get('token');

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setErrMessage('Verification token is missing.');
      return;
    }

    const executeVerification = async () => {
      try {
        await verifyEmail(token);
        setStatus('success');
      } catch (err) {
        setStatus('error');
        const message = err instanceof Error ? err.message : 'Verification failed. The token may be invalid or expired.';
        setErrMessage(message);
      }
    };

    executeVerification();
  }, [token, verifyEmail]);

  return (
    <div className="w-full max-w-md bg-zinc-900/60 backdrop-blur-xl border border-zinc-800/80 rounded-2xl p-8 shadow-2xl relative z-10 text-center animate-in fade-in duration-300">
      
      {/* Header Branding */}
      <div className="flex flex-col items-center mb-6">
        <div className="p-3 rounded-2xl bg-indigo-600/10 text-indigo-400 border border-indigo-500/20 mb-4 shadow-inner">
          <Activity className="h-8 w-8" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Email Verification</h2>
      </div>

      {status === 'verifying' && (
        <div className="py-6 flex flex-col items-center space-y-4">
          <Loader className="h-10 w-10 text-indigo-500 animate-spin" />
          <p className="text-zinc-400 text-sm">Validating your verification token...</p>
        </div>
      )}

      {status === 'success' && (
        <div className="space-y-6 animate-in zoom-in duration-200">
          <div className="flex justify-center">
            <div className="p-3 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <CheckCircle className="h-10 w-10" />
            </div>
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-bold text-white font-sans">Verification Successful!</h3>
            <p className="text-sm text-zinc-400">
              Your email address has been successfully verified. You can now login.
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
      )}

      {status === 'error' && (
        <div className="space-y-6 animate-in zoom-in duration-200">
          <div className="flex justify-center">
            <div className="p-3 rounded-full bg-red-500/10 text-red-400 border border-red-500/20">
              <ShieldAlert className="h-10 w-10" />
            </div>
          </div>
          <div className="space-y-2">
            <h3 className="text-lg font-bold text-white">Verification Failed</h3>
            <p className="text-sm text-zinc-400 leading-relaxed">{errMessage}</p>
          </div>
          <div className="pt-4 border-t border-zinc-800 flex flex-col space-y-3">
            <Link
              href="/signup"
              className="w-full inline-flex justify-center py-2.5 px-4 bg-zinc-800 hover:bg-zinc-700 text-white font-medium rounded-xl text-sm transition"
            >
              Back to Signup
            </Link>
            <Link
              href="/login"
              className="text-xs text-indigo-400 hover:text-indigo-300 transition"
            >
              Return to Login
            </Link>
          </div>
        </div>
      )}

    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col justify-center items-center p-4 relative overflow-hidden font-sans">
      {/* Background Decorative Gradients */}
      <div className="absolute top-1/4 left-1/4 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full bg-indigo-500/10 blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 translate-x-1/2 translate-y-1/2 w-96 h-96 rounded-full bg-purple-500/10 blur-3xl" />

      <Suspense fallback={
        <div className="w-full max-w-md bg-zinc-900/60 backdrop-blur-xl border border-zinc-800/80 rounded-2xl p-8 shadow-2xl relative z-10 text-center text-white">
          <Loader className="h-10 w-10 text-indigo-500 animate-spin mx-auto mb-4" />
          <p className="text-sm text-zinc-400">Loading verification context...</p>
        </div>
      }>
        <VerifyEmailContent />
      </Suspense>
    </div>
  );
}
