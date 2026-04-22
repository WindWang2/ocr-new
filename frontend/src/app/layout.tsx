import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'WANGJ-OCR | 工业视觉智控中心',
  description: '高精度工业仪表视觉识别系统 - 边缘计算与实时监测引擎',
  icons: {
    icon: '/favicon.ico',
  }
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">{children}</body>
    </html>
  )
}
