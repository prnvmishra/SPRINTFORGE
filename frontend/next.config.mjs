/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  eslint: { ignoreDuringBuilds: true },
  // Lets a verification build run into its own directory without clobbering the
  // .next cache of a dev server that is already running.
  distDir: process.env.NEXT_DIST_DIR || ".next",
};

export default nextConfig;
