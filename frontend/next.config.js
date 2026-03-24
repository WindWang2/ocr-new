/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8001/:path*',
      },
      {
        source: '/images/:path*',
        destination: 'http://localhost:8001/images/:path*',
      },
    ]
  },
}

module.exports = nextConfig
