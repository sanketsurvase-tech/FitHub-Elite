"use client";

import {
  Activity, ArrowDown, ArrowRight, ArrowUpRight, BadgeCheck, BarChart3, CalendarDays,
  Check, ChevronDown, CreditCard, Dumbbell, HeartPulse, Menu, QrCode, ShieldCheck,
  Sparkles, Users, Wallet, X,
} from "lucide-react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useEffect, useRef, useState } from "react";

gsap.registerPlugin(ScrollTrigger);

const capabilities = [
  { icon: Users, name: "Member relationships", copy: "Profiles, secure documents, emergency contacts and a complete membership timeline." },
  { icon: CreditCard, name: "Memberships & payments", copy: "Packages, renewals, payment records and expiry workflows in one place." },
  { icon: QrCode, name: "Attendance that flows", copy: "QR check-in and check-out with a clear, searchable attendance history." },
  { icon: Dumbbell, name: "Coaching & progress", copy: "Workout plans, nutrition logs and fitness measurements connected to the member." },
  { icon: CalendarDays, name: "Classes & bookings", copy: "Manage sessions, reservations and capacity from a shared schedule." },
  { icon: BarChart3, name: "Business visibility", copy: "See revenue, visits, memberships and the day-to-day signals that matter." },
];

const roles = [
  { title: "Owners & admins", icon: BarChart3, copy: "See the operation clearly, control access and make informed decisions." },
  { title: "Front desk", icon: QrCode, copy: "Move check-ins, member records and everyday requests along smoothly." },
  { title: "Coaches", icon: Dumbbell, copy: "Keep plans, classes and member progress connected to your coaching." },
  { title: "Members", icon: HeartPulse, copy: "Stay close to memberships, bookings and your own fitness journey." },
];

function Brand() {
  return (
    <a href="#top" className="flex items-center gap-2.5" aria-label="FitHub Elite home">
      <span className="grid h-10 w-10 place-items-center rounded-xl bg-[#c4f36b] text-[#122019]"><Activity size={21} strokeWidth={2.5} /></span>
      <span className="font-semibold tracking-tight text-white">FitHub <span className="text-[#c4f36b]">Elite</span></span>
    </a>
  );
}

function DashboardPreview() {
  return (
    <div className="landing-preview relative mx-auto w-full max-w-[610px]">
      <div className="landing-image absolute inset-4 rounded-[30px]" aria-hidden="true" />
      <div className="landing-orbit landing-orbit-one absolute -right-7 -top-8 h-40 w-40 rounded-full" aria-hidden="true" />
      <div className="landing-orbit landing-orbit-two absolute -bottom-8 -left-7 h-32 w-32 rounded-full" aria-hidden="true" />
      <div className="relative rounded-[26px] border border-white/15 bg-[#111812]/90 p-3 shadow-[0_35px_110px_rgba(0,0,0,.45)] backdrop-blur-xl sm:p-4">
        <div className="flex items-center justify-between border-b border-white/10 px-2 pb-3">
          <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-[#c4f36b]" /><span className="text-[11px] font-medium text-white/85">Your gym, in focus</span></div>
          <span className="rounded-full border border-white/10 px-2.5 py-1 text-[9px] uppercase tracking-[.15em] text-white/50">Workspace preview</span>
        </div>
        <div className="grid grid-cols-2 gap-2.5 py-3 sm:grid-cols-4">
          {[
            ["MEMBERS", Users, "Connected"],
            ["ATTENDANCE", QrCode, "Live check-in"],
            ["COACHING", Dumbbell, "Plans & progress"],
            ["OPERATIONS", Wallet, "One clear view"],
          ].map(([label, Icon, text]) => {
            const IconComponent = Icon as typeof Users;
            return <div key={String(label)} className="rounded-xl border border-white/[.08] bg-white/[.04] p-3">
              <div className="flex items-center justify-between text-white/45"><span className="text-[8px] font-semibold tracking-[.13em]">{String(label)}</span><IconComponent size={14} /></div>
              <p className="mt-4 text-[10px] font-medium text-white/90">{String(text)}</p>
            </div>;
          })}
        </div>
        <div className="rounded-2xl border border-white/[.08] bg-[#19221b] p-4 sm:p-5">
          <div className="flex items-start justify-between gap-4">
            <div><p className="text-[9px] font-semibold uppercase tracking-[.16em] text-white/45">A connected operation</p><p className="mt-1 text-lg font-medium tracking-tight text-white sm:text-xl">Every detail has its place.</p></div>
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#c4f36b]/10 text-[#c4f36b]"><Sparkles size={17} /></span>
          </div>
          <div className="mt-5 flex h-[112px] items-end gap-1.5 overflow-hidden rounded-xl bg-[linear-gradient(180deg,rgba(196,243,107,.06),rgba(196,243,107,0))] px-3 pt-3 sm:h-[145px] sm:gap-2">
            {[22, 32, 27, 47, 39, 61, 49, 69, 58, 84, 70, 96, 78, 100, 87, 112, 93, 120, 108, 132, 111, 143].map((height, index) => (
              <span key={index} className="preview-bar min-w-1 flex-1 rounded-t-sm bg-[#c4f36b]" style={{ height: `${height}px`, opacity: .18 + index * .026 }} />
            ))}
          </div>
          <div className="mt-3 flex items-center justify-between text-[9px] text-white/40"><span>People</span><span>Plans</span><span>Progress</span><span>Momentum</span></div>
        </div>
        <div className="mt-2.5 flex flex-wrap items-center justify-between gap-2 px-1 text-[9px] text-white/50">
          <span className="flex items-center gap-1.5"><span className="h-1.5 w-1.5 rounded-full bg-[#c4f36b]" /> Designed for the whole team</span>
          <span>One secure workspace</span>
        </div>
      </div>
      <div className="landing-float absolute -bottom-6 -left-3 flex items-center gap-3 rounded-2xl border border-white/10 bg-[#1a241d]/95 px-4 py-3 shadow-2xl backdrop-blur-xl sm:-left-10">
        <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#c4f36b] text-[#152017]"><BadgeCheck size={18} /></span>
        <span><span className="block text-[10px] font-semibold text-white">Roles, clearly defined</span><span className="mt-0.5 block text-[9px] text-white/50">Admin · coach · front desk · member</span></span>
      </div>
    </div>
  );
}

export default function LandingPage({ onAuth, notice }: { onAuth: (register: boolean) => void; notice?: string }) {
  const root = useRef<HTMLElement>(null);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    if (!root.current) return;
    const context = gsap.context(() => {
      const motion = gsap.matchMedia();
      motion.add("(prefers-reduced-motion: no-preference)", () => {
        gsap.timeline({ defaults: { ease: "power3.out" } })
          .from(".landing-nav", { y: -24, opacity: 0, duration: .7 })
          .from(".hero-eyebrow, .hero-title, .hero-copy, .hero-actions, .hero-note", {
            y: 24, opacity: 0, duration: .72, stagger: .1,
          }, "-=.36")
          .from(".landing-preview", { y: 44, opacity: 0, scale: .96, duration: 1 }, "-=.72")
          .from(".landing-float", { y: 16, opacity: 0, duration: .55 }, "-=.4");

        gsap.utils.toArray<HTMLElement>(".reveal").forEach((element) => {
          gsap.fromTo(element, { y: 36, opacity: 0 }, {
            y: 0,
            opacity: 1,
            duration: .8,
            ease: "power3.out",
            scrollTrigger: { trigger: element, start: "top 86%", once: true },
          });
        });

        gsap.to(".landing-orbit-one", {
          yPercent: 28,
          rotate: 36,
          ease: "none",
          scrollTrigger: { trigger: ".landing-hero", start: "top top", end: "bottom top", scrub: .8 },
        });
        gsap.to(".landing-image", {
          yPercent: 12,
          ease: "none",
          scrollTrigger: { trigger: ".landing-hero", start: "top top", end: "bottom top", scrub: .8 },
        });
      }, root);
      return () => motion.revert();
    }, root);
    return () => context.revert();
  }, []);

  function navigateToAuth(register = false) {
    setMenuOpen(false);
    onAuth(register);
  }

  return (
    <main ref={root} id="top" className="landing-page min-h-screen overflow-hidden bg-[#101510] text-white">
      <div className="landing-grain pointer-events-none fixed inset-0 z-30" aria-hidden="true" />
      {notice && <div role="status" className="fixed bottom-4 left-1/2 z-40 max-w-[calc(100%-2rem)] -translate-x-1/2 rounded-xl border border-amber-200/20 bg-[#1d281e] px-4 py-3 text-center text-xs text-white/85 shadow-2xl">{notice}</div>}
      <header className="landing-nav absolute inset-x-0 top-0 z-20 border-b border-white/[.08]">
        <nav className="mx-auto flex h-[76px] max-w-[1320px] items-center justify-between px-5 sm:px-8 lg:px-12" aria-label="Main navigation">
          <Brand />
          <div className="hidden items-center gap-8 md:flex">
            <a className="landing-link" href="#platform">Platform</a>
            <a className="landing-link" href="#capabilities">Capabilities</a>
            <a className="landing-link" href="#teams">For your team</a>
          </div>
          <div className="hidden items-center gap-3 md:flex">
            <button onClick={() => navigateToAuth(false)} className="rounded-full px-4 py-2.5 text-sm font-medium text-white/75 transition hover:text-white">Sign in</button>
            <button onClick={() => navigateToAuth(true)} className="group flex items-center gap-2 rounded-full bg-[#c4f36b] px-5 py-2.5 text-sm font-semibold text-[#142019] transition hover:bg-[#d3ff80]">
              Enter your workspace <ArrowUpRight size={15} className="transition group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </button>
          </div>
          <button onClick={() => setMenuOpen(!menuOpen)} aria-label={menuOpen ? "Close menu" : "Open menu"} aria-expanded={menuOpen} className="grid h-10 w-10 place-items-center rounded-xl border border-white/10 text-white md:hidden">
            {menuOpen ? <X size={19} /> : <Menu size={19} />}
          </button>
        </nav>
        {menuOpen && <div className="border-t border-white/10 bg-[#101510]/95 px-5 py-5 backdrop-blur-xl md:hidden">
          <div className="mx-auto flex max-w-[1320px] flex-col gap-4">
            {["Platform", "Capabilities", "For your team"].map((item) => <a key={item} href={`#${item === "For your team" ? "teams" : item.toLowerCase()}`} onClick={() => setMenuOpen(false)} className="text-sm text-white/75">{item}</a>)}
            <button onClick={() => navigateToAuth(false)} className="mt-1 rounded-full bg-[#c4f36b] px-5 py-3 text-sm font-semibold text-[#142019]">Sign in or create an account</button>
          </div>
        </div>}
      </header>

      <section className="landing-hero relative flex min-h-[820px] items-center pb-24 pt-32 sm:min-h-[850px] sm:pb-28 sm:pt-36 lg:min-h-[900px]">
        <div className="landing-grid pointer-events-none absolute inset-0 opacity-30" aria-hidden="true" />
        <div className="landing-glow landing-glow-hero pointer-events-none absolute" aria-hidden="true" />
        <div className="relative mx-auto grid w-full max-w-[1320px] items-center gap-16 px-5 sm:px-8 lg:grid-cols-[.94fr_1.06fr] lg:gap-8 lg:px-12">
          <div className="relative z-10 max-w-[600px]">
            <div className="hero-eyebrow mb-7 inline-flex items-center gap-2.5 rounded-full border border-white/10 bg-white/[.035] px-3.5 py-2 text-[10px] font-semibold uppercase tracking-[.19em] text-white/70">
              <span className="relative flex h-2 w-2"><span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#c4f36b] opacity-40" /><span className="relative inline-flex h-2 w-2 rounded-full bg-[#c4f36b]" /></span>
              The operating system for modern fitness
            </div>
            <h1 className="hero-title max-w-[660px] text-[clamp(3.3rem,7.3vw,6.65rem)] font-medium leading-[.94] tracking-[-.075em]">
              A stronger gym<br />starts <span className="landing-title-accent">behind</span><br />the scenes.
            </h1>
            <p className="hero-copy mt-7 max-w-[480px] text-base leading-7 text-white/60 sm:text-lg sm:leading-8">
              One thoughtful workspace for the people, plans and daily details that move your fitness business forward.
            </p>
            <div className="hero-actions mt-9 flex flex-col gap-3 sm:flex-row sm:items-center">
              <button onClick={() => navigateToAuth(true)} className="group inline-flex items-center justify-center gap-2 rounded-full bg-[#c4f36b] px-6 py-3.5 text-sm font-semibold text-[#142019] transition hover:-translate-y-0.5 hover:bg-[#d3ff80]">
                Get started <ArrowRight size={16} className="transition group-hover:translate-x-1" />
              </button>
              <a href="#platform" className="inline-flex items-center justify-center gap-2 rounded-full border border-white/15 px-6 py-3.5 text-sm font-medium text-white/80 transition hover:border-white/35 hover:text-white">
                Explore the platform <ArrowDown size={15} />
              </a>
            </div>
            <div className="hero-note mt-8 flex items-center gap-3 text-xs text-white/45">
              <ShieldCheck size={15} className="text-[#c4f36b]" />
              Role-aware access. Your member data stays in your workspace.
            </div>
          </div>
          <DashboardPreview />
        </div>
        <a href="#platform" aria-label="Scroll to platform overview" className="absolute bottom-8 left-1/2 hidden -translate-x-1/2 items-center gap-2 text-[9px] uppercase tracking-[.2em] text-white/35 transition hover:text-white/70 sm:flex">
          Scroll to explore <ArrowDown size={13} />
        </a>
      </section>

      <section id="platform" className="landing-light relative scroll-mt-12 overflow-hidden bg-[#e8eddf] py-24 text-[#19211a] sm:py-32">
        <div className="landing-light-glow pointer-events-none absolute -right-44 top-0 h-[540px] w-[540px] rounded-full" aria-hidden="true" />
        <div className="relative mx-auto grid max-w-[1320px] gap-12 px-5 sm:px-8 lg:grid-cols-[.8fr_1.2fr] lg:items-end lg:gap-20 lg:px-12">
          <div className="reveal">
            <p className="landing-kicker">Less busywork. More human work.</p>
            <h2 className="mt-5 max-w-[600px] text-4xl font-medium leading-[1.03] tracking-[-.06em] sm:text-6xl">Everything your gym runs on, <span className="text-[#719649]">working together.</span></h2>
          </div>
          <div className="reveal max-w-[610px] lg:justify-self-end">
            <p className="text-base leading-7 text-[#616d60] sm:text-lg sm:leading-8">Member records connect to memberships. Attendance connects to real check-ins. Training connects to progress. A joined-up view helps your team spend less time chasing details and more time helping people move.</p>
            <button onClick={() => navigateToAuth(false)} className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-[#365a2d] transition hover:gap-3">Open your workspace <ArrowRight size={15} /></button>
          </div>
        </div>
        <div className="relative mx-auto mt-16 grid max-w-[1320px] gap-4 px-5 sm:px-8 md:grid-cols-3 lg:px-12">
          {[
            { number: "01", title: "Know your people", copy: "Keep member details, key contacts and membership history together, with access appropriate to each role." },
            { number: "02", title: "Keep the day moving", copy: "Check-ins, bookings, packages and payments belong to one connected operating flow." },
            { number: "03", title: "Coach the whole journey", copy: "Bring workout plans, nutrition logs and fitness progress into the same member story." },
          ].map((item) => <article key={item.number} className="reveal group rounded-[24px] border border-[#d6ddcf] bg-white/55 p-6 transition duration-300 hover:-translate-y-1 hover:bg-white sm:p-8">
            <span className="font-mono text-xs text-[#7b9271]">{item.number} / 03</span>
            <h3 className="mt-12 text-xl font-medium tracking-tight sm:mt-16">{item.title}</h3>
            <p className="mt-3 text-sm leading-6 text-[#687267]">{item.copy}</p>
            <div className="mt-7 h-px w-full bg-[#d8dfd3]"><span className="block h-px w-0 bg-[#719649] transition-all duration-500 group-hover:w-full" /></div>
          </article>)}
        </div>
      </section>

      <section id="capabilities" className="relative scroll-mt-12 bg-[#101510] py-24 sm:py-32">
        <div className="landing-glow landing-glow-section pointer-events-none absolute" aria-hidden="true" />
        <div className="relative mx-auto max-w-[1320px] px-5 sm:px-8 lg:px-12">
          <div className="reveal flex flex-col justify-between gap-6 md:flex-row md:items-end">
            <div><p className="landing-kicker">One connected platform</p><h2 className="mt-5 max-w-[680px] text-4xl font-medium leading-[1.02] tracking-[-.06em] sm:text-6xl">The details behind a great member experience.</h2></div>
            <p className="max-w-[360px] text-sm leading-6 text-white/50">Purpose-built tools for the everyday work of running a gym, from the front desk to the training floor.</p>
          </div>
          <div className="mt-14 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {capabilities.map(({ icon: Icon, name, copy }, index) => <article key={name} className="reveal group relative overflow-hidden rounded-[22px] border border-white/[.09] bg-white/[.025] p-6 transition duration-300 hover:-translate-y-1 hover:border-[#c4f36b]/35 hover:bg-white/[.045] sm:min-h-[230px] sm:p-7">
              <span className="absolute right-6 top-6 font-mono text-[10px] text-white/25">0{index + 1}</span>
              <span className="grid h-11 w-11 place-items-center rounded-xl border border-[#c4f36b]/20 bg-[#c4f36b]/[.07] text-[#c4f36b] transition duration-300 group-hover:rotate-[-6deg] group-hover:bg-[#c4f36b] group-hover:text-[#142019]"><Icon size={19} /></span>
              <h3 className="mt-7 text-lg font-medium tracking-tight">{name}</h3>
              <p className="mt-2 max-w-[310px] text-sm leading-6 text-white/50">{copy}</p>
              <ArrowUpRight size={16} className="absolute bottom-7 right-7 text-white/20 transition group-hover:-translate-y-1 group-hover:translate-x-1 group-hover:text-[#c4f36b]" />
            </article>)}
          </div>
        </div>
      </section>

      <section id="teams" className="relative scroll-mt-12 overflow-hidden bg-[#17201a] py-24 sm:py-32">
        <div className="landing-grid landing-grid-subtle pointer-events-none absolute inset-0" aria-hidden="true" />
        <div className="relative mx-auto grid max-w-[1320px] gap-14 px-5 sm:px-8 lg:grid-cols-[.8fr_1.2fr] lg:gap-24 lg:px-12">
          <div className="reveal lg:sticky lg:top-32 lg:self-start">
            <p className="landing-kicker">One gym. Every role.</p>
            <h2 className="mt-5 text-4xl font-medium leading-[1.03] tracking-[-.06em] sm:text-6xl">A shared rhythm, with the right boundaries.</h2>
            <p className="mt-6 max-w-[440px] text-base leading-7 text-white/55">Give every person a focused view of the work they do. Role-based permissions keep sensitive operations in the right hands.</p>
            <div className="mt-8 inline-flex items-center gap-2 rounded-full border border-white/10 px-4 py-2.5 text-xs text-white/60"><ShieldCheck size={15} className="text-[#c4f36b]" /> Built around protected access</div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {roles.map(({ title, icon: Icon, copy }, index) => <article key={title} className={`reveal rounded-[22px] border border-white/[.09] p-6 transition duration-300 hover:border-[#c4f36b]/35 ${index % 2 ? "bg-white/[.045] sm:translate-y-9" : "bg-white/[.025]"}`}>
              <div className="flex items-center justify-between"><span className="grid h-10 w-10 place-items-center rounded-xl bg-[#c4f36b]/10 text-[#c4f36b]"><Icon size={18} /></span><span className="font-mono text-[10px] text-white/25">0{index + 1}</span></div>
              <h3 className="mt-9 text-lg font-medium">{title}</h3>
              <p className="mt-2 text-sm leading-6 text-white/50">{copy}</p>
            </article>)}
            <article className="reveal rounded-[22px] border border-[#c4f36b]/25 bg-[#c4f36b]/[.06] p-6 sm:col-span-2 sm:mt-9 sm:flex sm:items-center sm:justify-between sm:gap-8">
              <div className="max-w-[480px]"><div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[.12em] text-[#c4f36b]"><Sparkles size={15} /> Optional AI studio</div><h3 className="mt-4 text-lg font-medium">A useful first draft, always under your direction.</h3><p className="mt-2 text-sm leading-6 text-white/50">Ask Codestral for workout, nutrition or operational drafts when your backend is configured. Review every suggestion before using it.</p></div>
              <span className="mt-6 grid h-14 w-14 shrink-0 place-items-center rounded-2xl border border-[#c4f36b]/20 text-[#c4f36b] sm:mt-0"><Sparkles size={23} /></span>
            </article>
          </div>
        </div>
      </section>

      <section className="landing-light relative overflow-hidden bg-[#e8eddf] py-24 text-[#19211a] sm:py-32">
        <div className="relative mx-auto max-w-[1320px] px-5 sm:px-8 lg:px-12">
          <div className="reveal grid gap-10 lg:grid-cols-[.9fr_1.1fr] lg:items-end">
            <div><p className="landing-kicker">A calmer kind of control</p><h2 className="mt-5 text-4xl font-medium leading-[1.03] tracking-[-.06em] sm:text-6xl">Ready for the rush. Ready for the long view.</h2></div>
            <p className="max-w-[510px] text-base leading-7 text-[#616d60] lg:justify-self-end">Start with the moments that keep your gym moving. Find the context behind them. Then take the next useful action without hopping between disconnected tools.</p>
          </div>
          <div className="mt-14 grid gap-4 md:grid-cols-3">
            {[
              { step: "01", title: "Check in", copy: "Scan a member QR ID or record a manual visit. See active membership status in context.", icon: QrCode },
              { step: "02", title: "Stay connected", copy: "Move from the member profile to bookings, payments, coaching or their progress history.", icon: Activity },
              { step: "03", title: "Make the next move", copy: "Review real operating records, follow up on renewals and keep the team aligned.", icon: ArrowUpRight },
            ].map(({ step, title, copy, icon: Icon }) => <article key={step} className="reveal border-t border-[#c9d2c3] pt-5">
              <div className="flex items-center justify-between"><span className="font-mono text-xs text-[#7b9271]">{step} — THE DAILY FLOW</span><Icon size={17} className="text-[#719649]" /></div>
              <h3 className="mt-9 text-2xl font-medium tracking-tight">{title}</h3>
              <p className="mt-3 max-w-[340px] text-sm leading-6 text-[#687267]">{copy}</p>
            </article>)}
          </div>
        </div>
      </section>

      <section className="relative bg-[#101510] py-24 sm:py-32">
        <div className="mx-auto grid max-w-[1320px] gap-12 px-5 sm:px-8 lg:grid-cols-[.8fr_1.2fr] lg:gap-24 lg:px-12">
          <div className="reveal"><p className="landing-kicker">A few useful answers</p><h2 className="mt-5 text-4xl font-medium leading-[1.03] tracking-[-.06em] sm:text-5xl">Know what you’re stepping into.</h2></div>
          <div className="reveal divide-y divide-white/10">
            {[
              ["Who is FitHub Elite for?", "Gym owners and teams that want member management, attendance, memberships, payments, coaching and class operations in one workspace."],
              ["Can members create their own account?", "Yes. Member registration is available from the app. Each new account receives the member role; staff access is managed separately by an administrator."],
              ["Is AI required?", "No. The AI studio is optional. It uses Mistral Codestral through your Django backend when you configure a Mistral API key; there is no silent provider switch."],
              ["Where do I configure my deployment?", "Keep the API base URL in Vercel as NEXT_PUBLIC_API_BASE_URL, pointing to your Render API with the /api suffix. Keep database and Django secrets on Render."],
            ].map(([question, answer]) => <details key={question} className="group border-t border-white/10 py-5 first:border-t-0">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-5 text-sm font-medium text-white/90 marker:hidden">
                {question}<ChevronDown size={16} className="shrink-0 text-white/45 transition group-open:rotate-180" />
              </summary>
              <p className="max-w-[600px] pt-3 text-sm leading-6 text-white/50">{answer}</p>
            </details>)}
          </div>
        </div>
      </section>

      <section className="relative overflow-hidden px-5 pb-20 sm:px-8 sm:pb-28 lg:px-12">
        <div className="landing-cta-glow pointer-events-none absolute inset-x-0 bottom-0 mx-auto h-[450px] max-w-[1000px] rounded-full" aria-hidden="true" />
        <div className="reveal relative mx-auto max-w-[1320px] overflow-hidden rounded-[30px] border border-white/10 bg-[#18231a] px-6 py-14 text-center sm:px-12 sm:py-20">
          <div className="landing-cta-grid pointer-events-none absolute inset-0 opacity-40" aria-hidden="true" />
          <span className="relative mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-[#c4f36b] text-[#142019]"><Activity size={23} /></span>
          <p className="landing-kicker relative mt-7">Your next chapter starts here</p>
          <h2 className="relative mx-auto mt-4 max-w-[750px] text-4xl font-medium leading-[1.02] tracking-[-.06em] sm:text-6xl">Make space for the work that matters.</h2>
          <p className="relative mx-auto mt-5 max-w-[490px] text-sm leading-6 text-white/55 sm:text-base">Bring your gym’s daily operations into focus with FitHub Elite.</p>
          <button onClick={() => navigateToAuth(true)} className="group relative mt-8 inline-flex items-center gap-2 rounded-full bg-[#c4f36b] px-6 py-3.5 text-sm font-semibold text-[#142019] transition hover:-translate-y-0.5 hover:bg-[#d3ff80]">
            Enter your workspace <ArrowRight size={16} className="transition group-hover:translate-x-1" />
          </button>
          <div className="relative mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-[10px] text-white/40"><span className="inline-flex items-center gap-1.5"><Check size={12} className="text-[#c4f36b]" /> Secure role-based access</span><span className="inline-flex items-center gap-1.5"><Check size={12} className="text-[#c4f36b]" /> Connected gym operations</span></div>
        </div>
      </section>

      <footer className="border-t border-white/[.08]">
        <div className="mx-auto flex max-w-[1320px] flex-col justify-between gap-5 px-5 py-7 text-xs text-white/40 sm:flex-row sm:items-center sm:px-8 lg:px-12">
          <Brand />
          <p>Thoughtful tools for people who move people.</p>
          <p>© {new Date().getFullYear()} FitHub Elite</p>
        </div>
      </footer>
    </main>
  );
}
