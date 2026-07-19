'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { Activity, ShieldAlert, ArrowRight, Loader, Lock, Mail } from 'lucide-react';

export const LoginForm: React.FC = () => {
  const { login, error, setError } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login(email, password);
      router.push('/');
    } catch {
      // Error handled by AuthContext
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSocialLogin = (provider: string) => {
    // Fill credentials for quick demonstration
    setEmail(`demo_${provider.toLowerCase()}@codeorbit.ai`);
    setPassword('demoPassword123');
  };

  return (
    <div className="w-full max-w-md bg-zinc-900/80 backdrop-blur-2xl border border-zinc-800/80 rounded-3xl p-8 shadow-2xl relative z-10 space-y-6 animate-in fade-in duration-300">
      
      {/* Header Branding */}
      <div className="flex flex-col items-center text-center">
        <div className="p-3 rounded-2xl bg-indigo-600/10 text-indigo-400 border border-indigo-500/20 mb-3 shadow-inner">
          <Activity className="h-7 w-7 animate-pulse" />
        </div>
        <h2 className="text-2xl font-extrabold tracking-tight text-white">CodeOrbit AI</h2>
        <p className="text-xs text-zinc-400 mt-1">
          Sign in to access your Autonomous AI Software Factory
        </p>
      </div>

      {/* Error Alert Box */}
      {error && (
        <div className="p-3.5 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start space-x-2.5 text-red-400 text-xs animate-in shake duration-300">
          <ShieldAlert className="h-4 w-4 shrink-0 mt-0.5" />
          <span className="leading-relaxed">{error}</span>
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-[11px] font-bold text-zinc-300 uppercase tracking-wider mb-1.5">
            Email Address
          </label>
          <div className="relative flex items-center">
            <Mail className="absolute left-3.5 h-4 w-4 text-zinc-500 pointer-events-none" />
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-zinc-950/80 border border-zinc-800 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 text-white rounded-xl pl-10 pr-4 py-2.5 text-xs transition outline-none"
              placeholder="name@company.com"
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between items-center mb-1.5">
            <label className="block text-[11px] font-bold text-zinc-300 uppercase tracking-wider">
              Password
            </label>
            <Link 
              href="/forgot-password" 
              className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold transition"
            >
              Forgot Password?
            </Link>
          </div>
          <div className="relative flex items-center">
            <Lock className="absolute left-3.5 h-4 w-4 text-zinc-500 pointer-events-none" />
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-zinc-950/80 border border-zinc-800 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 text-white rounded-xl pl-10 pr-4 py-2.5 text-xs transition outline-none"
              placeholder="••••••••"
            />
          </div>
        </div>

        <div className="flex items-center justify-between pt-1">
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="rounded border-zinc-800 bg-zinc-950 text-indigo-600 focus:ring-indigo-500/20 h-3.5 w-3.5"
            />
            <span className="text-xs text-zinc-400">Remember session</span>
          </label>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full py-3 px-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 active:scale-[0.98] text-white font-bold rounded-xl text-xs transition-all duration-200 flex items-center justify-center space-x-2 shadow-lg shadow-indigo-600/30 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? (
            <>
              <Loader className="h-4 w-4 animate-spin" />
              <span>Verifying authentication...</span>
            </>
          ) : (
            <>
              <span>Sign In to CodeOrbit AI</span>
              <ArrowRight className="h-4 w-4" />
            </>
          )}
        </button>
      </form>

      {/* Divider */}
      <div className="relative flex items-center justify-center">
        <div className="border-t border-zinc-800/80 w-full" />
        <span className="bg-zinc-900 px-3 text-[10px] uppercase font-bold text-zinc-500 tracking-wider shrink-0 absolute">
          Or Continue With
        </span>
      </div>

      {/* Social Logins */}
      <div className="grid grid-cols-2 gap-2.5 pt-1">
        <button
          type="button"
          onClick={() => handleSocialLogin('GitHub')}
          className="py-2.5 px-3 bg-zinc-950/80 border border-zinc-800 hover:bg-zinc-800/60 rounded-xl text-xs font-semibold text-zinc-200 transition flex items-center justify-center space-x-2"
        >
          <svg className="h-4 w-4 fill-current" viewBox="0 0 24 24">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
          </svg>
          <span>GitHub</span>
        </button>

        <button
          type="button"
          onClick={() => handleSocialLogin('Google')}
          className="py-2.5 px-3 bg-zinc-950/80 border border-zinc-800 hover:bg-zinc-800/60 rounded-xl text-xs font-semibold text-zinc-200 transition flex items-center justify-center space-x-2"
        >
          <svg className="h-4 w-4" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
          </svg>
          <span>Google</span>
        </button>
      </div>

      {/* Footer Info */}
      <div className="text-center text-xs text-zinc-400 border-t border-zinc-800/60 pt-4">
        Don&apos;t have an account?{' '}
        <Link href="/signup" className="text-indigo-400 hover:text-indigo-300 font-bold transition">
          Create Account
        </Link>
      </div>

    </div>
  );
};
