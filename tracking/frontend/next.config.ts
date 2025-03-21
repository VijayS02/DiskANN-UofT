import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  rewrites : async () => {
    return [
      {
        source: '/:path*',
        destination: 'http://localhost:5000/:path*',
      },
      {
        source: '/socket.io/:path*',
        destination: 'http://localhost:5000/:path*',
      },
    ]
  }
};

export default nextConfig;
