/** @type {import('next').NextConfig} */

// 后端地址：由 next.config.mjs rewrites 代理使用（server 端，不暴露给浏览器）
const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";

const nextConfig = {
  // 前端 /api/** 代理到后端，同源无跨域
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${BACKEND}/api/:path*` }];
  },
};

export default nextConfig;
