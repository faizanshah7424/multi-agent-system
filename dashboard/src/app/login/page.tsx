'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { LandingShowcase } from '@/components/landing/LandingShowcase';
import { LoginForm } from '@/components/auth/LoginForm';

export default function LoginPage() {
  const { isAuthenticated, setError } = useAuth();
  const router = useRouter();

  useEffect(() => {
    setError(null);
    if (isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, router, setError]);

  return (
    <div className="min-h-screen bg-zinc-950 text-white font-sans relative overflow-x-hidden">
      
      {/* Background Lighting Gradients */}
      <div className="fixed top-0 left-1/4 -translate-x-1/2 w-[600px] h-[600px] rounded-full bg-indigo-600/10 blur-[140px] pointer-events-none" />
      <div className="fixed bottom-0 right-1/4 translate-x-1/2 w-[600px] h-[600px] rounded-full bg-purple-600/10 blur-[140px] pointer-events-none" />
      <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-blue-600/5 blur-[160px] pointer-events-none" />

      {/* Ambient Grid Overlay */}
      <div className="fixed inset-0 bg-[linear-gradient(to_right,#1f293715_1px,transparent_1px),linear-gradient(to_bottom,#1f293715_1px,transparent_1px)] bg-[size:4rem_4rem] pointer-events-none" />

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* Left Side: Investor-Grade Platform Experience */}
          <div className="lg:col-span-7">
            <LandingShowcase />
          </div>

          {/* Right Side: Glass Authentication Card */}
          <div className="lg:col-span-5 lg:sticky lg:top-8 flex justify-center py-6">
            <LoginForm />
          </div>

        </div>

        {/* Global Footer */}
        <footer className="mt-16 pt-8 border-t border-zinc-800/60 flex flex-col sm:flex-row items-center justify-between text-xs text-zinc-500 gap-4">
          <div className="flex items-center space-x-2">
            <span className="font-extrabold text-zinc-300 uppercase tracking-wider">CodeOrbit AI</span>
            <span>— Autonomous AI Software Engineering Platform</span>
          </div>
          <p>© 2026 CodeOrbit AI Inc. All rights reserved.</p>
        </footer>

      </div>
    </div>
  );
}
