"use client";

import {
  Activity, ArrowRight, ArrowUpRight, BarChart3,
  Bell, CalendarDays, ChevronDown, ChevronLeft, ChevronRight,
  ClipboardList, CreditCard, Dumbbell, Download, FileText, HeartPulse, LayoutDashboard,
  LogOut, Menu, Moon, Plus, Search, Settings2, ShieldCheck, Sparkles, Sun,
  Users, Wallet, X, Check,
} from "lucide-react";
import { BrowserQRCodeReader } from "@zxing/browser";
import {
  Area, AreaChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, ApiError, ApiList, clearToken, getApiBase, getToken, saveToken } from "@/lib/api";
import { Field, ModuleSpec, modules } from "@/lib/modules";
import LandingPage from "@/app/landing-page";

type UserInfo = { id: number; username: string; first_name: string; last_name: string; email: string; role: string };
type DashboardData = {
  revenue_this_month: number;
  attendance_today: number;
  active_memberships: number;
  expiring_memberships: number;
  total_members?: number;
  equipment_attention?: number;
  revenue_months?: { month: string; revenue: number }[];
  attendance_week: { date: string; visits: number }[];
  recent_payments: { id: number; member: string; amount: string; paid_at: string; method: string }[];
  upcoming_classes?: { id: number; name: string; starts_at: string; location: string }[];
};
type Row = Record<string, unknown> & { id: number };
type FormValue = string | number | boolean | null | undefined | File;

const iconMap: Record<string, typeof Users> = {
  Dashboard: LayoutDashboard, People: Users, Operations: ClipboardList, Finance: Wallet,
  Training: Dumbbell, Insights: BarChart3,
};

function display(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "boolean") return value ? "Active" : "Inactive";
  if (typeof value === "object") {
    if ("first_name" in value && "last_name" in value) {
      return `${value.first_name || ""} ${value.last_name || ""}`.trim() || "—";
    }
    return JSON.stringify(value);
  }
  return String(value);
}

function formatCurrency(value: string | number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(Number(value));
}

function getError(error: unknown) {
  return error instanceof ApiError ? error.message : "Something went wrong. Please try again.";
}

function AuthScreen({ onLogin, onBack, initialRegister }: {
  onLogin: () => void; onBack: () => void; initialRegister: boolean;
}) {
  const [register, setRegister] = useState(initialRegister);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData(event.currentTarget);
    try {
      if (register) {
        await api("/auth/register/", {
          method: "POST",
          body: JSON.stringify({
            username: form.get("username"), email: form.get("email"), password: form.get("password"),
            first_name: form.get("first_name"), last_name: form.get("last_name"), phone: form.get("phone"),
          }),
        });
        setRegister(false);
        setError("Account created. Sign in with your new credentials.");
      } else {
        const tokens = await api<{ access: string; refresh: string }>("/auth/token/", {
          method: "POST",
          body: JSON.stringify({ username: form.get("username"), password: form.get("password") }),
        });
        saveToken(tokens.access, tokens.refresh);
        onLogin();
      }
    } catch (reason) {
      setError(getError(reason));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="canvas flex min-h-screen items-center justify-center p-5">
      <div className="grid w-full max-w-5xl overflow-hidden rounded-[30px] border border-line surface shadow-soft lg:grid-cols-[1.05fr_.95fr]">
        <section className="relative hidden min-h-[620px] flex-col justify-between overflow-hidden bg-[#163b2a] p-11 text-white lg:flex">
          <div className="absolute -right-32 -top-20 h-96 w-96 rounded-full border border-white/10" />
          <div className="absolute -right-10 top-12 h-72 w-72 rounded-full border border-white/10" />
          <div className="relative flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-lime text-forest"><Activity size={21} /></div>
            <span className="text-lg font-semibold tracking-tight">FitHub <span className="text-lime">Elite</span></span>
          </div>
          <div className="relative max-w-md">
            <span className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/20 px-3 py-1.5 text-xs text-white/80">
              <Sparkles size={13} className="text-lime" /> One workspace. Better outcomes.
            </span>
            <h1 className="text-4xl font-semibold leading-[1.15] tracking-tight">Run a stronger gym, from the inside out.</h1>
            <p className="mt-4 max-w-sm text-sm leading-6 text-white/65">Bring your members, team, training and business insights together in one calm, connected workspace.</p>
            <div className="mt-9 flex items-end gap-3">
              {[32, 48, 39, 65, 50, 76, 62, 92, 72, 100, 84, 112].map((height, index) => (
                <span key={index} className="w-full rounded-t-sm bg-lime/80" style={{ height }} />
              ))}
            </div>
            <div className="mt-4 flex items-center justify-between border-t border-white/15 pt-4 text-xs text-white/55">
              <span>Member momentum</span><span className="flex items-center gap-1 text-lime"><ArrowUpRight size={14} /> Growing together</span>
            </div>
          </div>
          <p className="relative text-xs text-white/45">Thoughtful tools for people who move people.</p>
        </section>
        <section className="flex min-h-[620px] flex-col justify-center px-7 py-12 sm:px-12">
          <button onClick={onBack} className="mb-7 w-fit text-xs font-medium text-subtle transition hover:text-main">← Back to FitHub Elite</button>
          <div className="mb-10 flex items-center gap-3 lg:hidden">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-forest text-lime"><Activity size={20} /></div>
            <span className="text-lg font-semibold">FitHub <span className="text-forest">Elite</span></span>
          </div>
          <div className="mb-8">
            <p className="mb-2 text-xs font-semibold uppercase tracking-[.18em] text-[#67913c]">{register ? "Join the community" : "Welcome back"}</p>
            <h2 className="text-3xl font-semibold tracking-tight">{register ? "Create your account" : "Sign in to your gym"}</h2>
            <p className="mt-2 text-sm text-subtle">{register ? "Start with a member account. Your gym team can help you get set up." : "Your people, progress and plans are right where you left them."}</p>
          </div>
          <form onSubmit={submit} className="space-y-4">
            {register && <div className="grid grid-cols-2 gap-3">
              <Input label="First name" name="first_name" autoComplete="given-name" />
              <Input label="Last name" name="last_name" autoComplete="family-name" />
            </div>}
            <Input label="Username" name="username" autoComplete="username" required />
            {register && <><Input label="Email address" name="email" type="email" autoComplete="email" required /><Input label="Phone number" name="phone" type="tel" /></>}
            <Input label="Password" name="password" type="password" autoComplete={register ? "new-password" : "current-password"} required minLength={8} />
            {error && <p role="alert" className={`rounded-xl px-3 py-2 text-sm ${error.startsWith("Account") ? "bg-green-50 text-green-800" : "bg-red-50 text-red-700"}`}>{error}</p>}
            <button disabled={busy} className="mt-2 flex w-full items-center justify-center gap-2 rounded-xl bg-forest px-4 py-3.5 text-sm font-semibold text-white transition hover:bg-[#204d36] disabled:opacity-60">
              {busy ? "Please wait…" : register ? "Create account" : "Sign in"} <ArrowRight size={16} />
            </button>
          </form>
          <p className="mt-6 text-center text-sm text-subtle">
            {register ? "Already have an account?" : "New to FitHub?"}{" "}
            <button onClick={() => { setRegister(!register); setError(""); }} className="font-semibold text-forest underline-offset-4 hover:underline">
              {register ? "Sign in" : "Create a member account"}
            </button>
          </p>
          <p className="mt-10 flex items-center justify-center gap-2 text-xs text-subtle"><ShieldCheck size={14} /> Your account is protected with secure sign-in</p>
        </section>
      </div>
    </main>
  );
}

function Input({ label, name, type = "text", required, autoComplete, minLength }: {
  label: string; name: string; type?: string; required?: boolean; autoComplete?: string; minLength?: number;
}) {
  return <label className="block text-xs font-medium text-main">{label}
    <input name={name} type={type} required={required} minLength={minLength} autoComplete={autoComplete}
      className="mt-1.5 w-full rounded-xl border border-line surface px-3.5 py-3 text-sm outline-none transition focus:border-[#89ad56] focus:ring-4 focus:ring-lime/20" />
  </label>;
}

function Dashboard({ data, loading, role }: { data: DashboardData | null; loading: boolean; role: string }) {
  const today = new Intl.DateTimeFormat("en", {
    weekday: "long", month: "long", day: "numeric", timeZone: "UTC",
  }).format(new Date());
  const cards = [
    { title: role === "member" ? "Paid this month" : role === "trainer" ? "Assigned revenue" : "Revenue this month", value: data ? formatCurrency(data.revenue_this_month) : "—", meta: role === "member" ? "Your recorded payments" : "Payments recorded", icon: Wallet, tint: "bg-[#f0f7e9] text-[#54802d]" },
    { title: role === "member" ? "My memberships" : role === "trainer" ? "Assigned members" : "Active members", value: data?.total_members ?? data?.active_memberships ?? "—", meta: role === "member" ? "Current plans" : "With an active account", icon: Users, tint: "bg-[#eaf2ff] text-[#5479b8]" },
    { title: "Visits today", value: data?.attendance_today ?? "—", meta: "Check-ins recorded", icon: Activity, tint: "bg-[#fff2e7] text-[#c47a3e]" },
    { title: "Expiring soon", value: data?.expiring_memberships ?? "—", meta: "Next 7 days", icon: CalendarDays, tint: "bg-[#f7eefa] text-[#a66bb4]" },
  ];
  return <div className="animate-rise space-y-6">
    <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
      <div><p className="text-sm text-subtle">{today}</p><h1 className="mt-1 text-2xl font-semibold tracking-tight sm:text-[30px]">Your gym at a glance</h1></div>
      <p className="text-sm text-subtle">A little more momentum, every day.</p>
    </div>
    {loading && <div className="h-24 animate-pulse rounded-2xl soft" />}
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map(({ title, value, meta, icon: Icon, tint }) => <article key={title} className="surface rounded-2xl border border-line p-5 shadow-soft">
        <div className="flex items-center justify-between"><span className="text-sm text-subtle">{title}</span><span className={`grid h-9 w-9 place-items-center rounded-xl ${tint}`}><Icon size={17} /></span></div>
        <p className="mt-4 text-[28px] font-semibold tracking-tight">{value}</p><p className="mt-1 text-xs text-subtle">{meta}</p>
      </article>)}
    </div>
    <div className="grid gap-5 xl:grid-cols-[1.5fr_1fr]">
      <section className="surface rounded-2xl border border-line p-5 shadow-soft sm:p-6">
        <div className="mb-5 flex items-center justify-between"><div><h2 className="font-semibold">Revenue overview</h2><p className="mt-1 text-xs text-subtle">Recorded payments · last 6 months</p></div><span className="rounded-lg soft px-3 py-1.5 text-xs text-subtle">6 months</span></div>
        <div className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data?.revenue_months || []} margin={{ top: 8, right: 4, left: -18, bottom: 0 }}>
              <defs><linearGradient id="revenueFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#9bcb61" stopOpacity={0.28} /><stop offset="95%" stopColor="#9bcb61" stopOpacity={0} /></linearGradient></defs>
              <CartesianGrid stroke="var(--border)" strokeDasharray="4 5" vertical={false} />
              <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: "var(--subtle)", fontSize: 11 }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: "var(--subtle)", fontSize: 11 }} />
              <Tooltip formatter={(value) => [formatCurrency(Number(value)), "Revenue"]} contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 12, color: "var(--text)" }} />
              <Area type="monotone" dataKey="revenue" stroke="#79a942" strokeWidth={2.5} fill="url(#revenueFill)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </section>
      <section className="surface rounded-2xl border border-line p-5 shadow-soft sm:p-6">
        <div className="flex items-center justify-between"><div><h2 className="font-semibold">This week&apos;s activity</h2><p className="mt-1 text-xs text-subtle">Member visits by day</p></div><span className="rounded-lg bg-[#edf6e3] px-2.5 py-1 text-xs font-medium text-[#578134]">7 days</span></div>
        <div className="mt-5 flex h-[155px] items-end justify-between gap-2">
          {(data?.attendance_week || []).map((day) => {
            const max = Math.max(1, ...(data?.attendance_week || []).map((item) => item.visits));
            const height = Math.max(6, (day.visits / max) * 112);
            return <div key={day.date} className="flex h-full flex-1 flex-col items-center justify-end gap-2">
              <span className="text-[10px] text-subtle">{day.visits || ""}</span>
              <div className={`w-full max-w-8 rounded-t-md ${day.date === new Date().toISOString().slice(0, 10) ? "bg-forest" : "bg-[#c6e49d]"}`} style={{ height }} />
              <span className="text-[10px] text-subtle">{new Date(`${day.date}T12:00:00`).toLocaleDateString("en", { weekday: "short" })}</span>
            </div>;
          })}
        </div>
        <div className="mt-5 rounded-xl bg-[#f3f8ed] p-3.5 dark:bg-[#243425]">
          <p className="flex items-center gap-2 text-xs font-semibold text-[#4f7632] dark:text-lime"><Sparkles size={14} /> Keep the energy going</p>
          <p className="mt-1.5 text-xs leading-5 text-subtle">Your team&apos;s consistency creates a better member experience. Check in on upcoming renewals to keep the momentum.</p>
        </div>
      </section>
    </div>
    <div className="grid gap-5 xl:grid-cols-[1.1fr_.9fr]">
      <section className="surface overflow-hidden rounded-2xl border border-line shadow-soft">
        <div className="flex items-center justify-between border-b border-line px-5 py-4"><div><h2 className="font-semibold">Recent payments</h2><p className="mt-1 text-xs text-subtle">Latest transactions on record</p></div><CreditCard size={18} className="text-subtle" /></div>
        <div className="divide-y divide-[var(--border)]">
          {(data?.recent_payments || []).slice(0, 4).map((payment) => <div key={payment.id} className="flex items-center justify-between px-5 py-3.5">
            <div><p className="text-sm font-medium">{payment.member || "Member"}</p><p className="mt-1 text-xs capitalize text-subtle">{payment.method} · {new Date(payment.paid_at).toLocaleDateString()}</p></div>
            <span className="text-sm font-semibold">{formatCurrency(payment.amount)}</span>
          </div>)}
          {!data?.recent_payments?.length && <p className="px-5 py-8 text-center text-sm text-subtle">No payments recorded yet.</p>}
        </div>
      </section>
      <section className="surface overflow-hidden rounded-2xl border border-line shadow-soft">
        <div className="flex items-center justify-between border-b border-line px-5 py-4"><div><h2 className="font-semibold">Coming up</h2><p className="mt-1 text-xs text-subtle">Next scheduled group classes</p></div><CalendarDays size={18} className="text-subtle" /></div>
        <div className="divide-y divide-[var(--border)]">
          {(data?.upcoming_classes || []).slice(0, 4).map((item) => <div key={item.id} className="flex items-center gap-3 px-5 py-3.5">
            <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[#f1f6e9] text-[#638c3c]"><Dumbbell size={17} /></div>
            <div className="min-w-0 flex-1"><p className="truncate text-sm font-medium">{item.name}</p><p className="mt-1 text-xs text-subtle">{item.location || "Main studio"}</p></div>
            <span className="whitespace-nowrap text-xs text-subtle">{new Date(item.starts_at).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}</span>
          </div>)}
          {!data?.upcoming_classes?.length && <p className="px-5 py-8 text-center text-sm text-subtle">No upcoming classes scheduled.</p>}
        </div>
      </section>
    </div>
  </div>;
}

function RecordForm({ spec, record, onClose, onSave }: {
  spec: ModuleSpec; record: Row | null; onClose: () => void; onSave: (values: Record<string, FormValue>) => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData(event.currentTarget);
    const values: Record<string, FormValue> = {};
    for (const field of spec.fields) {
      const raw = form.get(field.name);
      if (raw === null || raw === "") continue;
      if (field.kind === "file") {
        if (raw instanceof File && raw.size > 0) values[field.name] = raw;
        continue;
      }
      if (field.kind === "number") values[field.name] = Number(raw);
      else if (field.kind === "json") {
        try { values[field.name] = JSON.parse(String(raw)) as FormValue; }
        catch { setError(`${field.label} must be valid JSON.`); setBusy(false); return; }
      } else if (field.kind === "datetime-local") values[field.name] = new Date(String(raw)).toISOString();
      else values[field.name] = String(raw);
    }
    try { await onSave(values); onClose(); }
    catch (reason) { setError(getError(reason)); }
    finally { setBusy(false); }
  }
  return <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#09130d]/45 p-4 backdrop-blur-sm" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
    <section className="surface flex max-h-[90vh] w-full max-w-xl flex-col rounded-2xl border border-line shadow-2xl">
      <header className="flex items-start justify-between border-b border-line px-6 py-5"><div><h2 className="text-lg font-semibold">{record ? "Edit record" : "Add record"}</h2><p className="mt-1 text-xs text-subtle">{spec.label} · required fields are marked</p></div><button onClick={onClose} className="rounded-lg p-2 text-subtle hover:soft" aria-label="Close dialog"><X size={18} /></button></header>
      <form onSubmit={submit} className="scrollbar-thin overflow-y-auto px-6 py-5">
        <div className="grid gap-4 sm:grid-cols-2">
          {spec.fields.map((field) => {
            const nestedUser = record?.user;
            const value = field.name === "user_id" && nestedUser && typeof nestedUser === "object" && "id" in nestedUser
              ? nestedUser.id : record?.[field.name];
            return <FieldInput key={field.name} field={field} value={value} />;
          })}
        </div>
        {error && <p role="alert" className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        <div className="mt-6 flex justify-end gap-3 border-t border-line pt-4"><button type="button" onClick={onClose} className="rounded-lg border border-line px-4 py-2.5 text-sm font-medium hover:soft">Cancel</button><button disabled={busy} className="rounded-lg bg-forest px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#204d36] disabled:opacity-60">{busy ? "Saving…" : "Save record"}</button></div>
      </form>
    </section>
  </div>;
}

function FieldInput({ field, value }: { field: Field; value: unknown }) {
  const base = "mt-1.5 w-full rounded-lg border border-line surface px-3 py-2.5 text-sm outline-none focus:border-[#89ad56] focus:ring-4 focus:ring-lime/20";
  const initial = useMemo(() => {
    if (value == null) return "";
    if (field.kind === "file") return "";
    if (field.kind === "json") return typeof value === "string" ? value : JSON.stringify(value, null, 2);
    if (field.kind === "datetime-local") return String(value).slice(0, 16);
    return String(value);
  }, [field.kind, value]);
  return <label className={`block text-xs font-medium text-main ${field.kind === "textarea" || field.kind === "json" ? "sm:col-span-2" : ""}`}>
    {field.label}{field.required && <span className="text-red-500"> *</span>}
    {field.kind === "textarea" || field.kind === "json" ? <textarea name={field.name} required={field.required} defaultValue={initial} rows={field.kind === "json" ? 4 : 3} className={`${base} resize-y`} placeholder={field.kind === "json" ? '[{"exercise":"Squat","sets":3,"reps":10}]' : ""} /> :
      field.kind === "select" ? <select name={field.name} required={field.required} defaultValue={initial} className={base}>
        {!field.required && <option value="">Select…</option>}{field.options?.map((option) => <option value={option} key={option}>{option || "All audiences"}</option>)}
      </select> :
        <input name={field.name} type={field.kind || "text"} required={field.required} accept={field.kind === "file" ? field.name === "document" ? ".pdf,.jpg,.jpeg,.png" : ".jpg,.jpeg,.png,.webp" : undefined} defaultValue={initial} min={field.kind === "number" ? 0 : undefined} step={field.kind === "number" ? "any" : undefined} className={base} />}
  </label>;
}

function CheckInPanel({ onDone }: { onDone: () => void }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const controlsRef = useRef<{ stop: () => void } | null>(null);
  const [qr, setQr] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [scanning, setScanning] = useState(false);

  async function checkIn(qrId: string) {
    if (!qrId.trim()) return;
    setBusy(true); setMessage("");
    try {
      const result = await api<{ action: string }>("/attendance/check-in/", { method: "POST", body: JSON.stringify({ qr_id: qrId.trim() }) });
      setMessage(result.action === "check_in" ? "Member checked in successfully." : "Member checked out successfully.");
      setQr("");
      onDone();
    } catch (reason) { setMessage(getError(reason)); }
    finally { setBusy(false); }
  }

  async function toggleCamera() {
    if (scanning) {
      controlsRef.current?.stop();
      controlsRef.current = null;
      setScanning(false);
      return;
    }
    if (!videoRef.current) return;
    try {
      const reader = new BrowserQRCodeReader();
      controlsRef.current = await reader.decodeFromVideoDevice(undefined, videoRef.current, (result) => {
        if (result) {
          const value = result.getText();
          setQr(value);
          controlsRef.current?.stop();
          setScanning(false);
          void checkIn(value);
        }
      });
      setScanning(true);
      setMessage("");
    } catch { setMessage("Camera access is unavailable. Use a QR scanner or enter the member ID below."); }
  }

  useEffect(() => () => controlsRef.current?.stop(), []);
  return <section className="surface mb-5 rounded-2xl border border-line p-5 shadow-soft">
    <div className="mb-4 flex items-center gap-3"><div className="grid h-10 w-10 place-items-center rounded-xl bg-[#eff6e7] text-[#648b3a]"><Activity size={18} /></div><div><h2 className="font-semibold">Quick check-in</h2><p className="mt-0.5 text-xs text-subtle">Scan a member&apos;s QR ID. A second scan checks them out.</p></div></div>
    <div className="flex flex-col gap-3 sm:flex-row">
      <input value={qr} onChange={(event) => setQr(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") void checkIn(qr); }} placeholder="Paste or scan member QR ID" className="min-w-0 flex-1 rounded-xl border border-line surface px-3.5 py-3 text-sm outline-none focus:border-[#89ad56]" />
      <button disabled={busy || !qr.trim()} onClick={() => void checkIn(qr)} className="rounded-xl bg-forest px-5 py-3 text-sm font-semibold text-white disabled:opacity-50">{busy ? "Checking…" : "Check in"}</button>
      <button onClick={() => void toggleCamera()} className="flex items-center justify-center gap-2 rounded-xl border border-line px-4 py-3 text-sm font-medium hover:soft"><Activity size={16} />{scanning ? "Stop camera" : "Use camera"}</button>
    </div>
    {scanning && <video ref={videoRef} className="mt-4 max-h-64 w-full rounded-xl bg-black object-cover" muted playsInline />}
    {message && <p role="status" className="mt-3 text-sm text-subtle">{message}</p>}
  </section>;
}

function ModuleView({ spec, role }: { spec: ModuleSpec; role: string }) {
  const [items, setItems] = useState<Row[]>([]);
  const [next, setNext] = useState<string | null>(null);
  const [previous, setPrevious] = useState<string | null>(null);
  const [count, setCount] = useState(0);
  const [query, setQuery] = useState("");
  const [pageUrl, setPageUrl] = useState(`/${spec.key}/`);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [modal, setModal] = useState<Row | null | undefined>(undefined);
  const mayWrite = !spec.roles || spec.roles.includes(role);
  const isReadOnly = spec.key === "notifications" || spec.key === "audit-logs";
  const formSpec = role === "member" && ["bookings", "feedback"].includes(spec.key)
    ? { ...spec, fields: spec.fields.filter((field) => field.name !== "member") }
    : spec;
  const currentPage = Number(new URL(pageUrl, "http://localhost").searchParams.get("page") || 1);
  const firstRecord = count ? (currentPage - 1) * 20 + 1 : 0;
  const lastRecord = Math.min(currentPage * 20, count);
  const progressData = items.map((item) => ({
    date: String(item.recorded_at).slice(0, 10),
    weight: item.weight_kg == null ? null : Number(item.weight_kg),
    bodyFat: item.body_fat_percent == null ? null : Number(item.body_fat_percent),
  }));

  const load = useCallback(async (url: string, search = "") => {
    setLoading(true); setError("");
    try {
      const separator = url.includes("?") ? "&" : "?";
      const target = search ? `${url}${separator}search=${encodeURIComponent(search)}` : url;
      const result = await api<ApiList<Row>>(target);
      setItems(result.results); setCount(result.count); setNext(result.next); setPrevious(result.previous);
      setPageUrl(url);
    } catch (reason) { setError(getError(reason)); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(`/${spec.key}/`, query); }, 300);
    return () => window.clearTimeout(timer);
  }, [query, spec.key, load]);

  async function save(values: Record<string, FormValue>) {
    const hasFile = Object.values(values).some((value) => value instanceof File);
    let body: BodyInit;
    if (hasFile) {
      const multipart = new FormData();
      for (const [key, value] of Object.entries(values)) {
        if (value === undefined || value === null) continue;
        multipart.append(key, value instanceof File ? value : typeof value === "object" ? JSON.stringify(value) : String(value));
      }
      body = multipart;
    } else {
      body = JSON.stringify(values);
    }
    if (modal === null) await api(`/${spec.key}/`, { method: "POST", body });
    else if (modal) await api(`/${spec.key}/${modal.id}/`, { method: "PATCH", body });
    await load(`/${spec.key}/`, query);
  }

  async function remove(row: Row) {
    if (!window.confirm(`Delete record #${row.id}? This cannot be undone.`)) return;
    try { await api(`/${spec.key}/${row.id}/`, { method: "DELETE" }); await load(pageUrl, query); }
    catch (reason) { setError(getError(reason)); }
  }

  async function membershipAction(row: Row, action: "freeze" | "unfreeze" | "renew") {
    let body: Record<string, number> = {};
    if (action === "freeze") {
      const days = window.prompt("Freeze for how many days? Choose 1–30.", "7");
      if (days === null) return;
      body = { days: Number(days) };
    }
    try {
      await api(`/${spec.key}/${row.id}/${action}/`, { method: "POST", body: JSON.stringify(body) });
      await load(pageUrl, query);
    } catch (reason) { setError(getError(reason)); }
  }

  function exportRows(format: string) {
    const base = getApiBase();
    const token = getToken();
    void fetch(`${base}/exports/${spec.key}/?output=${format}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then(async (response) => {
        if (!response.ok) throw new Error(await response.text() || "Export failed.");
        const blob = await response.blob();
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = `${spec.key}.${format === "excel" ? "xlsx" : format}`;
        link.click();
        URL.revokeObjectURL(link.href);
      })
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Export failed."));
  }

  async function downloadReceipt(row: Row) {
    const base = getApiBase();
    const token = getToken();
    try {
      const response = await fetch(`${base}/payments/${row.id}/receipt/`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!response.ok) throw new Error("Could not download this payment receipt.");
      const objectUrl = URL.createObjectURL(await response.blob());
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = `receipt-${row.id}.pdf`;
      link.click();
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not download this payment receipt.");
    }
  }

  return <div className="animate-rise">
    <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
      <div><p className="text-xs font-medium uppercase tracking-[.16em] text-[#739c4c]">{spec.group}</p><h1 className="mt-1 text-2xl font-semibold tracking-tight">{spec.label}</h1><p className="mt-1 text-sm text-subtle">{spec.description}</p></div>
      <div className="flex gap-2">
        {["members", "payments", "attendance", "memberships"].includes(spec.key) && <div className="group relative">
          <button className="flex items-center gap-2 rounded-xl border border-line surface px-3.5 py-2.5 text-sm font-medium hover:soft"><Download size={15} /> Export <ChevronDown size={14} /></button>
          <div className="invisible absolute right-0 top-full z-10 mt-1 w-32 rounded-xl border border-line surface p-1 opacity-0 shadow-soft group-focus-within:visible group-hover:visible group-hover:opacity-100">
            {["csv", "excel", "pdf"].map((format) => <button key={format} onClick={() => exportRows(format)} className="block w-full rounded-lg px-3 py-2 text-left text-sm capitalize hover:soft">{format === "excel" ? "Excel" : format.toUpperCase()}</button>)}
          </div>
        </div>}
        {mayWrite && !isReadOnly && spec.fields.length > 0 && <button onClick={() => setModal(null)} className="flex items-center gap-2 rounded-xl bg-forest px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#204d36]"><Plus size={16} /> Add record</button>}
      </div>
    </div>
    {spec.key === "attendance" && mayWrite && <CheckInPanel onDone={() => void load(pageUrl, query)} />}
    {error && <div role="alert" className="mb-4 flex items-center justify-between rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"><span>{error}</span><button aria-label="Dismiss error" onClick={() => setError("")}><X size={16} /></button></div>}
    {spec.key === "progress" && progressData.length > 0 && <section className="surface mb-5 rounded-2xl border border-line p-5 shadow-soft">
      <div className="mb-4"><h2 className="font-semibold">Progress trends</h2><p className="mt-1 text-xs text-subtle">Measurements from recorded check-ins</p></div>
      <div className="h-[220px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={progressData} margin={{ top: 8, right: 12, left: -18, bottom: 0 }}>
            <CartesianGrid stroke="var(--border)" strokeDasharray="4 5" vertical={false} />
            <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: "var(--subtle)", fontSize: 10 }} />
            <YAxis yAxisId="weight" axisLine={false} tickLine={false} tick={{ fill: "var(--subtle)", fontSize: 10 }} />
            <YAxis yAxisId="fat" orientation="right" axisLine={false} tickLine={false} tick={{ fill: "var(--subtle)", fontSize: 10 }} />
            <Tooltip contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 12, color: "var(--text)" }} />
            <Line yAxisId="weight" connectNulls type="monotone" dataKey="weight" name="Weight (kg)" stroke="#719e47" strokeWidth={2.5} dot={{ r: 3 }} />
            <Line yAxisId="fat" connectNulls type="monotone" dataKey="bodyFat" name="Body fat (%)" stroke="#7192cc" strokeWidth={2} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>}
    <section className="surface overflow-hidden rounded-2xl border border-line shadow-soft">
      <div className="flex flex-col gap-3 border-b border-line p-4 sm:flex-row sm:items-center sm:justify-between">
        <label className="flex max-w-md flex-1 items-center gap-2 rounded-xl border border-line px-3 py-2.5"><Search size={16} className="shrink-0 text-subtle" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={`Search ${spec.label.toLowerCase()}…`} className="w-full bg-transparent text-sm outline-none placeholder:text-subtle" /></label>
        <span className="text-xs text-subtle">{count.toLocaleString()} {count === 1 ? "record" : "records"}</span>
      </div>
      <div className="scrollbar-thin overflow-x-auto">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="soft text-[11px] uppercase tracking-wider text-subtle"><tr>{spec.columns.map((column) => <th key={column} className="px-4 py-3 font-semibold first:pl-5">{column.replaceAll("_", " ")}</th>)}{mayWrite && !isReadOnly || spec.key === "payments" || spec.key === "notifications" ? <th className="px-4 py-3 text-right font-semibold">Actions</th> : null}</tr></thead>
          <tbody className="divide-y divide-[var(--border)]">
            {!loading && items.map((item) => <tr key={item.id} className="transition hover:bg-[var(--soft)]">
              {spec.columns.map((column) => <td key={column} className="max-w-[220px] truncate px-4 py-3.5 first:pl-5">
                {column === "active" || column === "resolved" ? <span className={`rounded-full px-2.5 py-1 text-[11px] font-medium ${item[column] ? "bg-green-50 text-green-700" : "soft text-subtle"}`}>{display(item[column])}</span> :
                  column === "status" ? <span className="rounded-full bg-[#f1f6e9] px-2.5 py-1 text-[11px] font-medium capitalize text-[#638c3c]">{display(item[column])}</span> :
                    <span className={column === "amount" || column === "price" ? "font-medium" : "text-main"} title={display(item[column])}>{display(item[column])}</span>}
              </td>)}
              {(mayWrite && !isReadOnly || spec.key === "notifications" && !item.read_at || spec.key === "payments") && <td className="px-4 py-3 text-right"><div className="flex justify-end gap-1">
                {spec.key === "payments" && <button onClick={() => void downloadReceipt(item)} title="Download receipt" className="rounded-lg p-2 text-subtle hover:bg-[var(--soft)]"><Download size={15} /></button>}
                {spec.key === "notifications" && !item.read_at && <button onClick={() => {
                  void api(`/${spec.key}/${item.id}/mark-read/`, { method: "POST" }).then(() => load(pageUrl, query)).catch((reason: unknown) => setError(getError(reason)));
                }} title="Mark as read" className="rounded-lg p-2 text-subtle hover:bg-[var(--soft)]"><Check size={15} /></button>}
                {spec.key === "memberships" && item.status === "active" && <button onClick={() => void membershipAction(item, "freeze")} title="Freeze membership" className="rounded-lg p-2 text-subtle hover:bg-[#f1f6e9] hover:text-[#638c3c]"><Moon size={15} /></button>}
                {spec.key === "memberships" && item.status === "frozen" && <button onClick={() => void membershipAction(item, "unfreeze")} title="Unfreeze membership" className="rounded-lg p-2 text-subtle hover:bg-[#f1f6e9] hover:text-[#638c3c]"><Sun size={15} /></button>}
                {spec.key === "memberships" && <button onClick={() => void membershipAction(item, "renew")} title="Renew membership" className="rounded-lg p-2 text-subtle hover:bg-[#f1f6e9] hover:text-[#638c3c]"><ArrowUpRight size={15} /></button>}
                <button onClick={() => setModal(item)} title="Edit record" className="rounded-lg p-2 text-subtle hover:soft"><Settings2 size={15} /></button>
                <button onClick={() => void remove(item)} title="Delete record" className="rounded-lg p-2 text-subtle hover:bg-red-50 hover:text-red-600"><X size={15} /></button>
              </div></td>}
            </tr>)}
            {loading && <tr><td colSpan={spec.columns.length + 1} className="px-5 py-14 text-center text-sm text-subtle">Loading {spec.label.toLowerCase()}…</td></tr>}
            {!loading && !items.length && <tr><td colSpan={spec.columns.length + 1} className="px-5 py-14 text-center"><div className="mx-auto grid h-11 w-11 place-items-center rounded-xl soft text-subtle"><FileText size={19} /></div><p className="mt-3 text-sm font-medium">Nothing here yet</p><p className="mt-1 text-xs text-subtle">{query ? "Try a different search." : "Records you add will appear here."}</p></td></tr>}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between border-t border-line px-5 py-3.5 text-xs text-subtle">
        <span>Showing {firstRecord}–{lastRecord} of {count}</span>
        <div className="flex gap-2"><button disabled={!previous || loading} onClick={() => previous && void load(previous, query)} className="rounded-lg border border-line p-2 disabled:opacity-40" aria-label="Previous page"><ChevronLeft size={15} /></button><button disabled={!next || loading} onClick={() => next && void load(next, query)} className="rounded-lg border border-line p-2 disabled:opacity-40" aria-label="Next page"><ChevronRight size={15} /></button></div>
      </div>
    </section>
    {modal !== undefined && <RecordForm spec={formSpec} record={modal} onClose={() => setModal(undefined)} onSave={save} />}
  </div>;
}

function AIStudio() {
  const [prompt, setPrompt] = useState("");
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const suggestions = [
    { label: "Workout draft", icon: Dumbbell, prompt: "Draft a balanced 3-day beginner strength workout plan with sets, reps, rest, and progression guidance. Include modifications and safety notes." },
    { label: "Nutrition draft", icon: HeartPulse, prompt: "Draft a practical one-day balanced meal plan with approximate calories, protein, carbs, and fats. State assumptions and remind the reader this is general information, not medical advice." },
    { label: "Gym insights", icon: BarChart3, prompt: "What useful weekly business and member-retention insights should a gym manager review? Give an actionable checklist without inventing performance data." },
  ];
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(""); setAnswer("");
    try { const result = await api<{ answer: string }>("/ai/advice/", { method: "POST", body: JSON.stringify({ prompt }) }); setAnswer(result.answer); }
    catch (reason) { setError(getError(reason)); }
    finally { setBusy(false); }
  }
  return <div className="animate-rise mx-auto max-w-4xl">
    <div className="mb-7"><p className="text-xs font-medium uppercase tracking-[.16em] text-[#739c4c]">FitHub assistant</p><h1 className="mt-1 text-2xl font-semibold tracking-tight">AI studio</h1><p className="mt-1 text-sm text-subtle">Thoughtful starting points for training, nutrition and gym operations.</p></div>
    <div className="mb-5 grid gap-3 sm:grid-cols-3">{suggestions.map(({ label, icon: Icon, prompt: text }) => <button key={label} onClick={() => setPrompt(text)} className="surface flex items-center gap-3 rounded-xl border border-line p-4 text-left shadow-soft transition hover:-translate-y-0.5"><span className="grid h-9 w-9 place-items-center rounded-lg bg-[#eff6e7] text-[#638c3c]"><Icon size={17} /></span><span className="text-sm font-medium">{label}</span><ArrowRight size={14} className="ml-auto text-subtle" /></button>)}</div>
    <section className="surface rounded-2xl border border-line p-5 shadow-soft sm:p-7">
      <form onSubmit={submit}><label htmlFor="ai-prompt" className="mb-2 block text-sm font-semibold">What would you like help with?</label><textarea id="ai-prompt" value={prompt} onChange={(event) => setPrompt(event.target.value)} maxLength={4000} rows={6} placeholder="Share a goal, training context or business question…" className="w-full resize-y rounded-xl border border-line surface p-4 text-sm outline-none focus:border-[#89ad56] focus:ring-4 focus:ring-lime/20" /><div className="mt-3 flex items-center justify-between gap-3"><span className="text-xs text-subtle">{prompt.length}/4000 · Powered by Mistral Codestral</span><button disabled={busy || !prompt.trim()} className="flex items-center gap-2 rounded-xl bg-forest px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50"><Sparkles size={15} />{busy ? "Thinking…" : "Generate draft"}</button></div></form>
      {error && <p role="alert" className="mt-5 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}
      {answer && <div className="mt-6 rounded-xl border border-[#dce9cf] bg-[#f8fbf4] p-5 dark:bg-[#1d2b20]"><p className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#648b3a]"><Sparkles size={14} /> Your draft</p><div className="whitespace-pre-wrap text-sm leading-7">{answer}</div><p className="mt-4 border-t border-line pt-3 text-xs text-subtle">Review AI-generated content before sharing. Not medical advice.</p></div>}
    </section>
    <p className="mt-4 text-xs leading-5 text-subtle">AI requests are securely proxied by the gym API to Mistral&apos;s <code>codestral-latest</code> model. Configure <code>MISTRAL_API_KEY</code> on the backend to enable this feature.</p>
  </div>;
}

function Shell({ user, onLogout }: { user: UserInfo; onLogout: () => void }) {
  const [active, setActive] = useState("Dashboard");
  const [menuOpen, setMenuOpen] = useState(false);
  const [dark, setDark] = useState(() => typeof window !== "undefined" && window.localStorage.getItem("fithub_theme") === "dark");
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [dashLoading, setDashLoading] = useState(true);
  const [dashError, setDashError] = useState("");

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    window.localStorage.setItem("fithub_theme", dark ? "dark" : "light");
  }, [dark]);
  const loadDashboard = useCallback(() => {
    setDashLoading(true); setDashError("");
    void api<DashboardData>("/dashboard/")
      .then(setDashboard).catch((reason: unknown) => setDashError(getError(reason))).finally(() => setDashLoading(false));
  }, []);
  useEffect(() => { void Promise.resolve().then(loadDashboard); }, [loadDashboard]);

  const availableModules = modules.filter((item) => !item.visibleRoles || item.visibleRoles.includes(user.role));
  const groups = useMemo(() => {
    const grouped = new Map<string, ModuleSpec[]>();
    for (const item of availableModules) grouped.set(item.group, [...(grouped.get(item.group) || []), item]);
    return grouped;
  }, [availableModules]);
  const selected = modules.find((item) => item.label === active);
  const initials = `${user.first_name?.[0] || user.username[0]}${user.last_name?.[0] || ""}`.toUpperCase();

  function navigate(label: string) { setActive(label); setMenuOpen(false); }

  return <div className="canvas min-h-screen">
    <aside className={`fixed inset-y-0 left-0 z-40 flex w-[260px] flex-col border-r border-line surface transition-transform lg:translate-x-0 ${menuOpen ? "translate-x-0" : "-translate-x-full"}`}>
      <div className="flex h-[76px] items-center gap-3 border-b border-line px-6">
        <div className="grid h-10 w-10 place-items-center rounded-xl bg-forest text-lime"><Activity size={21} /></div>
        <div><p className="font-semibold tracking-tight">FitHub <span className="text-[#719649]">Elite</span></p><p className="text-[10px] text-subtle">GYM MANAGEMENT</p></div>
        <button onClick={() => setMenuOpen(false)} className="ml-auto rounded-lg p-2 text-subtle lg:hidden" aria-label="Close menu"><X size={18} /></button>
      </div>
      <nav className="scrollbar-thin flex-1 overflow-y-auto px-3 py-5">
        <button onClick={() => navigate("Dashboard")} className={`mb-5 flex w-full items-center gap-3 rounded-xl px-3.5 py-3 text-sm font-medium transition ${active === "Dashboard" ? "bg-[#edf5e6] text-[#42692e] dark:bg-[#263826] dark:text-lime" : "text-subtle hover:soft"}`}><LayoutDashboard size={17} /> Overview</button>
        {[...groups.entries()].map(([group, entries]) => <div key={group} className="mb-5">
          <p className="mb-2 px-3.5 text-[10px] font-semibold uppercase tracking-[.15em] text-subtle">{group}</p>
          <div className="space-y-0.5">{entries.map((item) => {
            const Icon = iconMap[group] || FileText;
            return <button key={item.key} onClick={() => navigate(item.label)} className={`flex w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-left text-[13px] transition ${active === item.label ? "bg-[#edf5e6] font-medium text-[#42692e] dark:bg-[#263826] dark:text-lime" : "text-subtle hover:soft"}`}><Icon size={16} /><span className="flex-1">{item.label}</span></button>;
          })}</div>
        </div>)}
        <button onClick={() => navigate("AI studio")} className={`flex w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-left text-[13px] transition ${active === "AI studio" ? "bg-[#edf5e6] font-medium text-[#42692e] dark:bg-[#263826] dark:text-lime" : "text-subtle hover:soft"}`}><Sparkles size={16} /> AI studio <span className="ml-auto rounded-full bg-[#eff6e7] px-2 py-0.5 text-[9px] font-semibold text-[#648b3a] dark:bg-[#30402e]">BETA</span></button>
      </nav>
      <div className="border-t border-line p-3">
        <div className="flex items-center gap-3 rounded-xl p-2.5">
          <div className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-[#e6eedb] text-xs font-semibold text-[#4e7135]">{initials}</div>
          <div className="min-w-0 flex-1"><p className="truncate text-xs font-semibold">{user.first_name || user.username} {user.last_name}</p><p className="truncate text-[10px] capitalize text-subtle">{user.role}</p></div>
          <button onClick={onLogout} title="Sign out" className="rounded-lg p-2 text-subtle hover:bg-red-50 hover:text-red-600"><LogOut size={15} /></button>
        </div>
      </div>
    </aside>
    {menuOpen && <button className="fixed inset-0 z-30 bg-black/30 lg:hidden" aria-label="Close navigation" onClick={() => setMenuOpen(false)} />}
    <div className="min-h-screen lg:pl-[260px]">
      <header className="sticky top-0 z-20 flex h-[76px] items-center justify-between border-b border-line surface/95 px-4 backdrop-blur sm:px-7">
        <div className="flex items-center gap-3"><button onClick={() => setMenuOpen(true)} className="rounded-lg p-2 text-subtle hover:soft lg:hidden" aria-label="Open menu"><Menu size={19} /></button><div className="hidden items-center gap-2 text-xs text-subtle sm:flex"><span>Workspace</span><ChevronRight size={13} /><span className="font-medium text-main">{active}</span></div><span className="text-sm font-medium sm:hidden">{active}</span></div>
        <div className="flex items-center gap-2">
          <span className="mr-2 hidden rounded-full bg-[#f0f5eb] px-3 py-1.5 text-[11px] font-medium capitalize text-[#5b7d3d] dark:bg-[#253626] dark:text-lime sm:inline-flex">{user.role} workspace</span>
          <button onClick={() => setDark(!dark)} title={dark ? "Switch to light theme" : "Switch to dark theme"} className="rounded-xl border border-line p-2.5 text-subtle hover:soft">{dark ? <Sun size={16} /> : <Moon size={16} />}</button>
          <button title="Notifications" onClick={() => navigate("Notifications")} className="relative rounded-xl border border-line p-2.5 text-subtle hover:soft"><Bell size={16} /><span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-[#a5ce64]" /></button>
          <div className="ml-1 grid h-9 w-9 place-items-center rounded-full bg-forest text-[11px] font-semibold text-lime">{initials}</div>
        </div>
      </header>
      <main className="mx-auto max-w-[1500px] px-4 py-6 sm:px-7 sm:py-8">
        {active === "Dashboard" ? <>{dashError && <p role="alert" className="mb-4 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{dashError}</p>}<Dashboard data={dashboard} loading={dashLoading} role={user.role} /></> :
          active === "AI studio" ? <AIStudio /> :
          <ModuleView key={selected?.key || "audit-logs"} spec={selected || modules.find((item) => item.key === "audit-logs")!} role={user.role} />}
        <footer className="mt-9 flex flex-col justify-between gap-2 border-t border-line pt-4 text-[11px] text-subtle sm:flex-row"><span>© {new Date().getFullYear()} FitHub Elite · Built for better movement.</span><span>Protected workspace</span></footer>
      </main>
    </div>
  </div>;
}

export default function Home() {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [checking, setChecking] = useState(true);
  const [authError, setAuthError] = useState("");
  const [showAuth, setShowAuth] = useState(false);
  const [initialRegister, setInitialRegister] = useState(false);
  const loadProfile = useCallback(async () => {
    const token = getToken();
    if (!token) { setUser(null); setChecking(false); return; }
    try { setUser(await api<UserInfo>("/auth/me/")); setAuthError(""); }
    catch (reason) {
      setUser(null);
      setAuthError(getError(reason));
      clearToken();
    } finally { setChecking(false); }
  }, []);
  useEffect(() => { void Promise.resolve().then(loadProfile); }, [loadProfile]);
  function logout() { clearToken(); setUser(null); }
  if (checking) return <main className="canvas grid min-h-screen place-items-center"><div className="flex items-center gap-3 text-sm text-subtle"><span className="h-5 w-5 animate-spin rounded-full border-2 border-[#b8ce9a] border-t-forest" /> Loading your workspace…</div></main>;
  if (!user) return showAuth
    ? <AuthScreen onLogin={() => void loadProfile()} initialRegister={initialRegister} onBack={() => setShowAuth(false)} />
    : <LandingPage notice={authError} onAuth={(register) => { setInitialRegister(register); setShowAuth(true); }} />;
  return <Shell user={user} onLogout={logout} />;
}
