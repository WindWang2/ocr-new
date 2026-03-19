import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'OCR 仪表读数系统',
  description: '实验室仪器自动拍照识别',
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
