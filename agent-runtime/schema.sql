-- Canonical schema for the Supabase-backed universal agent runtime.
create extension if not exists pgcrypto;
create table if not exists public.agent_jobs (
  id uuid primary key default gen_random_uuid(), created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
  status text not null default 'pending' check (status in ('pending','claimed','running','succeeded','failed','cancelled')),
  target text not null default 'any', kind text not null default 'exec', payload jsonb not null default '{}'::jsonb,
  claimed_by text, claimed_at timestamptz, lease_until timestamptz, started_at timestamptz, finished_at timestamptz, result jsonb, error text
);
create index if not exists agent_jobs_poll_idx on public.agent_jobs (status, target, created_at);
create table if not exists public.agent_workers (
  id text primary key, created_at timestamptz not null default now(), updated_at timestamptz not null default now(), last_seen timestamptz,
  status text not null default 'offline', capabilities jsonb not null default '{}'::jsonb, metadata jsonb not null default '{}'::jsonb, token_sha256 text unique
);
create table if not exists public.agent_events (
  id bigint generated always as identity primary key, created_at timestamptz not null default now(), job_id uuid references public.agent_jobs(id) on delete cascade,
  worker_id text, level text not null default 'info', event jsonb not null default '{}'::jsonb
);
create index if not exists agent_events_job_idx on public.agent_events (job_id, created_at);
create table if not exists public.agent_kv (key text primary key, value jsonb not null, updated_at timestamptz not null default now());
alter table public.agent_jobs enable row level security;
alter table public.agent_workers enable row level security;
alter table public.agent_events enable row level security;
alter table public.agent_kv enable row level security;
revoke all on public.agent_jobs, public.agent_workers, public.agent_events, public.agent_kv from anon, authenticated;
grant all on public.agent_jobs, public.agent_workers, public.agent_events, public.agent_kv to service_role;
grant usage, select on sequence public.agent_events_id_seq to service_role;
