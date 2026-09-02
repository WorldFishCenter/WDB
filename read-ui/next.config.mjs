/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // The read UI is local-only: it proxies to the Phase-A1 FastAPI through a server route
  // handler (app/api/answer), so the browser never talks cross-origin and the API stays
  // untouched (no CORS middleware added to wdb_api). Override the target with WDB_API_URL.
  env: {
    // surfaced only so the health banner can show where it's pointing; the proxy reads it server-side
    WDB_API_URL_PUBLIC: process.env.WDB_API_URL || "http://127.0.0.1:8000",
  },
};

export default nextConfig;
