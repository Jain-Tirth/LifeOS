import React, { useRef } from 'react';
import { Link } from 'react-router-dom';
import { motion, useInView } from 'framer-motion';
import {
  Sparkles,
  UtensilsCrossed,
  Brain,
  BookOpen,
  HeartPulse,
  ShoppingCart,
  ArrowRight,
  Zap,
  Shield,
  Users,
  ChevronRight,
  Star,
  CheckCircle2,
  Rocket,
  UserPlus,
  Settings2,
  Bot,
} from 'lucide-react';

/* ───────────────────────── helpers ───────────────────────── */

const fadeUp = {
  hidden: { opacity: 0, y: 40 },
  visible: (i = 0) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.12, duration: 0.6, ease: 'easeOut' },
  }),
};

const Section = ({ children, className = '' }) => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '-80px' });
  return (
    <motion.section
      ref={ref}
      initial="hidden"
      animate={inView ? 'visible' : 'hidden'}
      className={className}
    >
      {children}
    </motion.section>
  );
};

/* ───────────────────────── navbar ────────────────────────── */

const Navbar = () => (
  <nav className="fixed top-0 inset-x-0 z-50 backdrop-blur-xl bg-slate-900/70 border-b border-white/10">
    <div className="max-w-7xl mx-auto flex items-center justify-between px-6 py-4">
      <Link to="/" className="flex items-center gap-2 group">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center shadow-lg shadow-purple-500/25 group-hover:shadow-purple-500/40 transition-shadow">
          <Sparkles className="text-white" size={18} />
        </div>
        <span className="text-xl font-bold text-white font-display tracking-tight">
          LifeOS
        </span>
      </Link>

      <div className="hidden md:flex items-center gap-8 text-sm text-white/60">
        <a href="#features" className="hover:text-white transition-colors">
          Features
        </a>
        <a href="#how-it-works" className="hover:text-white transition-colors">
          How It Works
        </a>
        <a href="#testimonials" className="hover:text-white transition-colors">
          Testimonials
        </a>
      </div>

      <div className="flex items-center gap-3">
        <Link
          to="/login"
          className="px-4 py-2 text-sm font-medium text-white/80 hover:text-white border border-white/15 rounded-xl hover:border-white/30 transition-all"
        >
          Log In
        </Link>
        <Link
          to="/register"
          className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl hover:from-blue-600 hover:to-purple-600 shadow-lg shadow-purple-500/25 hover:shadow-purple-500/40 transition-all"
        >
          Sign Up
        </Link>
      </div>
    </div>
  </nav>
);

/* ───────────────────────── hero ──────────────────────────── */

const Hero = () => (
  <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-20">
    {/* Gradient orbs */}
    <div className="absolute -top-32 -left-32 w-[500px] h-[500px] bg-purple-600/30 rounded-full blur-[120px] animate-pulse-slow pointer-events-none" />
    <div className="absolute -bottom-40 -right-40 w-[600px] h-[600px] bg-blue-600/20 rounded-full blur-[140px] animate-pulse-slow pointer-events-none" />
    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] bg-indigo-500/10 rounded-full blur-[100px] pointer-events-none" />

    <div className="relative z-10 max-w-4xl mx-auto text-center px-6">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="inline-flex items-center gap-2 px-4 py-1.5 mb-8 text-xs font-medium text-purple-300 bg-purple-500/15 border border-purple-500/25 rounded-full"
      >
        <Zap size={14} />
        AI-Powered Personal Life Management
      </motion.div>

      <motion.h1
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.15 }}
        className="text-5xl md:text-7xl font-bold text-white font-display leading-tight tracking-tight"
      >
        Your Life,{' '}
        <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
          Intelligently
        </span>{' '}
        Managed
      </motion.h1>

      <motion.p
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.3 }}
        className="mt-6 text-lg md:text-xl text-white/60 max-w-2xl mx-auto leading-relaxed"
      >
        LifeOS brings together AI-powered agents for meal planning, productivity,
        studying, wellness, and shopping — all in one beautiful dashboard.
      </motion.p>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, delay: 0.45 }}
        className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
      >
        <Link
          to="/register"
          className="group flex items-center gap-2 px-8 py-3.5 text-white font-semibold bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl hover:from-blue-600 hover:to-purple-600 shadow-xl shadow-purple-500/25 hover:shadow-purple-500/40 transition-all text-base"
        >
          Get Started Free
          <ArrowRight
            size={18}
            className="group-hover:translate-x-1 transition-transform"
          />
        </Link>
        <Link
          to="/login"
          className="flex items-center gap-2 px-8 py-3.5 text-white/80 font-semibold border border-white/15 rounded-2xl hover:bg-white/5 hover:border-white/30 transition-all text-base"
        >
          Sign In
          <ChevronRight size={18} />
        </Link>
      </motion.div>

      {/* Trust badges */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8, delay: 0.7 }}
        className="mt-16 flex flex-wrap items-center justify-center gap-6 text-white/30 text-sm"
      >
        <span className="flex items-center gap-1.5">
          <Shield size={14} /> Secure & Private
        </span>
        <span className="flex items-center gap-1.5">
          <Zap size={14} /> AI-Powered
        </span>
        <span className="flex items-center gap-1.5">
          <Users size={14} /> Built for Everyone
        </span>
      </motion.div>
    </div>
  </section>
);

/* ───────────────────────── features ─────────────────────── */

const features = [
  {
    icon: UtensilsCrossed,
    title: 'Meal Planner',
    desc: 'Get personalized meal plans tailored to your dietary preferences, goals, and schedule.',
    color: 'from-emerald-500 to-green-600',
    shadow: 'shadow-emerald-500/20',
  },
  {
    icon: Brain,
    title: 'Productivity',
    desc: 'Manage tasks, track habits, and boost your productivity with intelligent suggestions.',
    color: 'from-violet-500 to-purple-600',
    shadow: 'shadow-violet-500/20',
  },
  {
    icon: BookOpen,
    title: 'Study Buddy',
    desc: 'Organize study sessions, get topic summaries, and track your learning progress.',
    color: 'from-blue-500 to-cyan-600',
    shadow: 'shadow-blue-500/20',
  },
  {
    icon: HeartPulse,
    title: 'Wellness',
    desc: 'Log workouts, meditations, and wellness activities to maintain a healthy lifestyle.',
    color: 'from-rose-500 to-pink-600',
    shadow: 'shadow-rose-500/20',
  },
  {
    icon: ShoppingCart,
    title: 'Shopping',
    desc: 'Smart shopping lists generated from your meal plans and personal needs.',
    color: 'from-amber-500 to-orange-600',
    shadow: 'shadow-amber-500/20',
  },
];

const Features = () => (
  <Section
    className="relative py-28 px-6"
    id="features"
  >
    <div className="max-w-7xl mx-auto" id="features">
      <motion.div variants={fadeUp} className="text-center mb-16">
        <span className="inline-flex items-center gap-2 px-3 py-1 text-xs font-medium text-blue-300 bg-blue-500/15 border border-blue-500/25 rounded-full mb-4">
          <Sparkles size={14} /> Powerful Features
        </span>
        <h2 className="text-3xl md:text-5xl font-bold text-white font-display">
          Everything You Need,{' '}
          <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            One Platform
          </span>
        </h2>
        <p className="mt-4 text-white/50 max-w-xl mx-auto">
          Five specialized AI agents working together to help you manage every
          aspect of your daily life.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {features.map((f, i) => (
          <motion.div
            key={f.title}
            variants={fadeUp}
            custom={i}
            className={`group relative p-6 rounded-2xl bg-white/5 backdrop-blur-sm border border-white/10 hover:border-white/20 transition-all duration-300 hover:-translate-y-1 ${
              i === 4 ? 'md:col-span-2 lg:col-span-1' : ''
            }`}
          >
            <div
              className={`w-12 h-12 rounded-xl bg-gradient-to-br ${f.color} flex items-center justify-center mb-4 shadow-lg ${f.shadow} group-hover:scale-110 transition-transform`}
            >
              <f.icon size={22} className="text-white" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2 font-display">
              {f.title}
            </h3>
            <p className="text-sm text-white/50 leading-relaxed">{f.desc}</p>
          </motion.div>
        ))}
      </div>
    </div>
  </Section>
);

/* ──────────────────── how it works ──────────────────────── */

const steps = [
  {
    icon: UserPlus,
    title: 'Create Your Account',
    desc: 'Sign up in seconds and set up your personal profile with your goals and preferences.',
    color: 'from-blue-500 to-indigo-600',
  },
  {
    icon: Settings2,
    title: 'Customize Your Agents',
    desc: 'Choose which AI agents you want — meals, productivity, study, wellness, or shopping.',
    color: 'from-purple-500 to-violet-600',
  },
  {
    icon: Bot,
    title: 'Let AI Do the Work',
    desc: 'Chat with your agents, get smart suggestions, and watch your life become more organized.',
    color: 'from-pink-500 to-rose-600',
  },
];

const HowItWorks = () => (
  <Section className="relative py-28 px-6" id="how-it-works">
    <div className="max-w-5xl mx-auto" id="how-it-works">
      <motion.div variants={fadeUp} className="text-center mb-16">
        <span className="inline-flex items-center gap-2 px-3 py-1 text-xs font-medium text-purple-300 bg-purple-500/15 border border-purple-500/25 rounded-full mb-4">
          <Rocket size={14} /> Simple Setup
        </span>
        <h2 className="text-3xl md:text-5xl font-bold text-white font-display">
          Up and Running in{' '}
          <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            3 Steps
          </span>
        </h2>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {steps.map((s, i) => (
          <motion.div
            key={s.title}
            variants={fadeUp}
            custom={i}
            className="relative text-center"
          >
            {/* connector line */}
            {i < steps.length - 1 && (
              <div className="hidden md:block absolute top-10 left-[60%] w-[80%] h-px bg-gradient-to-r from-white/20 to-transparent" />
            )}

            <div
              className={`mx-auto w-20 h-20 rounded-2xl bg-gradient-to-br ${s.color} flex items-center justify-center mb-6 shadow-xl relative`}
            >
              <s.icon size={32} className="text-white" />
              <span className="absolute -top-2 -right-2 w-7 h-7 rounded-full bg-slate-900 border-2 border-white/20 flex items-center justify-center text-xs font-bold text-white">
                {i + 1}
              </span>
            </div>
            <h3 className="text-lg font-semibold text-white mb-2 font-display">
              {s.title}
            </h3>
            <p className="text-sm text-white/50 leading-relaxed max-w-xs mx-auto">
              {s.desc}
            </p>
          </motion.div>
        ))}
      </div>
    </div>
  </Section>
);

/* ──────────────────── testimonials ──────────────────────── */

const testimonials = [
  {
    name: 'Arjun M.',
    role: 'Graduate Student',
    quote:
      'LifeOS completely changed how I manage my study sessions. The AI Study Buddy alone saved me hours every week!',
  },
  {
    name: 'Priya S.',
    role: 'Fitness Enthusiast',
    quote:
      'The wellness tracker and meal planner work so well together. I finally have a health routine that sticks.',
  },
  {
    name: 'Rahul K.',
    role: 'Startup Founder',
    quote:
      'As someone juggling a hundred things, the productivity agent is a lifesaver. My task completion rate doubled!',
  },
];

const Testimonials = () => (
  <Section className="relative py-28 px-6" id="testimonials">
    <div className="max-w-6xl mx-auto" id="testimonials">
      <motion.div variants={fadeUp} className="text-center mb-16">
        <span className="inline-flex items-center gap-2 px-3 py-1 text-xs font-medium text-amber-300 bg-amber-500/15 border border-amber-500/25 rounded-full mb-4">
          <Star size={14} /> Loved by Users
        </span>
        <h2 className="text-3xl md:text-5xl font-bold text-white font-display">
          What People{' '}
          <span className="bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent">
            Are Saying
          </span>
        </h2>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {testimonials.map((t, i) => (
          <motion.div
            key={t.name}
            variants={fadeUp}
            custom={i}
            className="p-6 rounded-2xl bg-white/5 backdrop-blur-sm border border-white/10 hover:border-white/20 transition-all"
          >
            <div className="flex gap-1 mb-4">
              {[...Array(5)].map((_, j) => (
                <Star
                  key={j}
                  size={14}
                  className="text-amber-400 fill-amber-400"
                />
              ))}
            </div>
            <p className="text-white/70 text-sm leading-relaxed mb-6 italic">
              "{t.quote}"
            </p>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-sm font-bold">
                {t.name.charAt(0)}
              </div>
              <div>
                <p className="text-white text-sm font-medium">{t.name}</p>
                <p className="text-white/40 text-xs">{t.role}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  </Section>
);

/* ──────────────────── CTA banner ────────────────────────── */

const CTABanner = () => (
  <Section className="py-28 px-6">
    <motion.div
      variants={fadeUp}
      className="max-w-4xl mx-auto text-center p-12 md:p-16 rounded-3xl bg-gradient-to-br from-blue-600/30 via-purple-600/30 to-pink-600/30 backdrop-blur-xl border border-white/15 relative overflow-hidden"
    >
      {/* decorative blobs */}
      <div className="absolute -top-20 -left-20 w-60 h-60 bg-purple-500/20 rounded-full blur-[80px] pointer-events-none" />
      <div className="absolute -bottom-20 -right-20 w-60 h-60 bg-blue-500/20 rounded-full blur-[80px] pointer-events-none" />

      <div className="relative z-10">
        <h2 className="text-3xl md:text-5xl font-bold text-white font-display mb-4">
          Ready to Transform Your Life?
        </h2>
        <p className="text-white/60 max-w-lg mx-auto mb-8">
          Join LifeOS today and let AI help you plan, organize, and thrive —
          completely free.
        </p>
        <Link
          to="/register"
          className="group inline-flex items-center gap-2 px-8 py-3.5 text-white font-semibold bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl hover:from-blue-600 hover:to-purple-600 shadow-xl shadow-purple-500/25 hover:shadow-purple-500/40 transition-all"
        >
          Get Started Now
          <ArrowRight
            size={18}
            className="group-hover:translate-x-1 transition-transform"
          />
        </Link>
      </div>
    </motion.div>
  </Section>
);

/* ───────────────────── footer ───────────────────────────── */

const Footer = () => (
  <footer className="border-t border-white/10 py-10 px-6">
    <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center">
          <Sparkles className="text-white" size={14} />
        </div>
        <span className="text-white font-display font-semibold">LifeOS</span>
      </div>

      <div className="flex items-center gap-6 text-sm text-white/40">
        <a href="#features" className="hover:text-white/70 transition-colors">
          Features
        </a>
        <a
          href="#how-it-works"
          className="hover:text-white/70 transition-colors"
        >
          How It Works
        </a>
        <Link to="/login" className="hover:text-white/70 transition-colors">
          Login
        </Link>
        <Link to="/register" className="hover:text-white/70 transition-colors">
          Sign Up
        </Link>
      </div>

      <p className="text-xs text-white/30">
        &copy; {new Date().getFullYear()} LifeOS. All rights reserved.
      </p>
    </div>
  </footer>
);

/* ────────────────── main landing page ───────────────────── */

const LandingPage = () => (
  <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-950 to-slate-900 overflow-x-hidden">
    <Navbar />
    <Hero />
    <Features />
    <HowItWorks />
    <Testimonials />
    <CTABanner />
    <Footer />
  </div>
);

export default LandingPage;
