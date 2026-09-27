/** @type {import('next').NextConfig} */
const nextConfig = {
  // Set NEXT_STANDALONE=true in Docker builds to produce a self-contained server.js.
  // Vercel manages its own build output and must NOT have `output: "standalone"` set.
  ...(process.env.NEXT_STANDALONE === "true" ? { output: "standalone" } : {}),
};

export default nextConfig;
