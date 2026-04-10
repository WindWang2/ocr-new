/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  pageExtensions: ['tsx', 'ts', 'jsx', 'js'],
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
