import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: '智能实验方舱 - 仪表自动抓拍识别系统',
  description: '面向石油化工实验室的智能仪表读数采集系统，工业相机自动抓拍，AI 视觉识别精准提取读数',
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
