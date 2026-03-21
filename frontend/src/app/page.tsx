'use client'

import Image from 'next/image'
import Link from 'next/link'
import {
  Camera,
  Eye,
  FlaskConical,
  BarChart3,
  ArrowRight,
  Shield,
  Zap,
  Cpu,
  ChevronRight,
} from 'lucide-react'

const features = [
  {
    icon: Camera,
    title: '自动抓拍',
    desc: '工业相机定时或触发式抓拍仪表盘画面，支持多相机多点位同步采集',
  },
  {
    icon: Eye,
    title: '智能识别',
    desc: '基于大语言模型的 OCR 识别引擎，精准提取仪表读数，适应各类表盘样式',
  },
  {
    icon: FlaskConical,
    title: '实验管理',
    desc: '支持运动粘度、表观粘度、表面张力等多种实验类型的全流程管理',
  },
  {
    icon: BarChart3,
    title: '数据汇总',
    desc: '自动汇总实验结果，生成结构化数据报告，便于后续分析与存档',
  },
]

const advantages = [
  {
    icon: Shield,
    title: '数据准确可靠',
    desc: 'AI 视觉识别替代人工读数，消除人为误差，确保实验数据一致性',
  },
  {
    icon: Zap,
    title: '效率大幅提升',
    desc: '7×24 小时无人值守运行，实验员可同时管理多组实验流程',
  },
  {
    icon: Cpu,
    title: '灵活可扩展',
    desc: '模块化设计，支持接入新实验类型和自定义识别规则，适应业务变化',
  },
]

export default function Home() {
  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 bg-white/90 backdrop-blur border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3">
            <Image src="/logo.png" alt="WEWODON" width={120} height={80} className="h-9 w-auto" />
            <span className="font-bold text-gray-900 text-lg tracking-tight hidden sm:block">
              智能实验方舱
            </span>
          </Link>

          <div className="flex items-center gap-1">
            <Link
              href="/"
              className="px-3 py-2 text-sm font-medium rounded-lg"
              style={{ color: '#2E5EAA' }}
            >
              首页
            </Link>
            <Link
              href="/dashboard"
              className="px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-lg transition"
            >
              控制台
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section
        className="relative overflow-hidden"
        style={{ background: 'linear-gradient(135deg, #2E5EAA 0%, #1E4488 50%, #162F5A 100%)' }}
      >
        {/* Background decoration */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-10 w-72 h-72 bg-white rounded-full blur-3xl" />
          <div className="absolute bottom-10 right-10 w-96 h-96 rounded-full blur-3xl" style={{ background: '#F7941D' }} />
        </div>

        <div className="relative max-w-6xl mx-auto px-4 sm:px-6 py-20 sm:py-28">
          <div className="max-w-2xl">
            <div
              className="inline-flex items-center gap-2 px-3 py-1 bg-white/15 rounded-full text-sm mb-6"
              style={{ color: '#c8ddf5' }}
            >
              <Camera size={14} />
              仪表自动抓拍识别系统
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white leading-tight tracking-tight">
              智能实验方舱
            </h1>
            <p className="mt-5 text-lg sm:text-xl leading-relaxed max-w-xl" style={{ color: '#c8ddf5' }}>
              面向石油化工实验室的智能仪表读数采集系统。工业相机自动抓拍，
              AI 视觉识别精准提取读数，让实验数据管理更高效、更可靠。
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 px-6 py-3 font-semibold rounded-xl hover:opacity-90 transition shadow-lg"
                style={{ background: '#F7941D', color: '#fff' }}
              >
                进入控制台
                <ArrowRight size={18} />
              </Link>
              <a
                href="#features"
                className="inline-flex items-center gap-2 px-6 py-3 bg-white/10 text-white font-semibold rounded-xl hover:bg-white/20 transition border border-white/20"
              >
                了解更多
                <ChevronRight size={18} />
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold text-gray-900 tracking-tight">核心功能</h2>
            <p className="mt-3 text-gray-500 max-w-lg mx-auto">
              覆盖实验数据采集、识别、管理的完整流程
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((f) => (
              <div
                key={f.title}
                className="bg-white rounded-2xl p-6 shadow-sm hover:shadow-md transition group"
              >
                <div
                  className="w-11 h-11 rounded-xl flex items-center justify-center mb-4 transition"
                  style={{ background: '#EBF0F8', color: '#2E5EAA' }}
                >
                  <f.icon size={22} />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{f.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Advantages */}
      <section className="py-20 bg-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 tracking-tight">
                为什么选择智能实验方舱
              </h2>
              <p className="mt-4 text-gray-500 leading-relaxed">
                传统人工读数方式耗时且容易出错。我们的系统通过工业相机自动采集、AI
                智能识别，实现实验数据的全自动化管理，帮助实验室显著提升效率和数据质量。
              </p>

              <div className="mt-8 space-y-6">
                {advantages.map((a) => (
                  <div key={a.title} className="flex gap-4">
                    <div
                      className="shrink-0 w-10 h-10 text-white rounded-xl flex items-center justify-center"
                      style={{ background: '#2E5EAA' }}
                    >
                      <a.icon size={20} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{a.title}</h3>
                      <p className="mt-1 text-sm text-gray-500 leading-relaxed">{a.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Visual card */}
            <div
              className="rounded-2xl p-8 sm:p-12 flex items-center justify-center min-h-[360px]"
              style={{ background: 'linear-gradient(135deg, #EBF0F8 0%, #F5F0E8 100%)' }}
            >
              <div className="text-center">
                <Image src="/logo.png" alt="WEWODON" width={160} height={107} className="mx-auto mb-5 w-auto h-16" />
                <h3 className="text-xl font-bold text-gray-800">智能实验方舱</h3>
                <p className="mt-2 text-gray-500 text-sm">仪表自动抓拍识别系统</p>
                <div className="mt-6 flex justify-center gap-3">
                  <div
                    className="px-3 py-1.5 bg-white rounded-lg shadow text-xs font-medium"
                    style={{ color: '#2E5EAA' }}
                  >
                    运动粘度
                  </div>
                  <div
                    className="px-3 py-1.5 bg-white rounded-lg shadow text-xs font-medium"
                    style={{ color: '#2E5EAA' }}
                  >
                    表观粘度
                  </div>
                  <div
                    className="px-3 py-1.5 bg-white rounded-lg shadow text-xs font-medium"
                    style={{ color: '#2E5EAA' }}
                  >
                    表面张力
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16" style={{ background: '#2E5EAA' }}>
        <div className="max-w-6xl mx-auto px-4 sm:px-6 text-center">
          <h2 className="text-3xl font-bold text-white tracking-tight">
            开始使用智能实验方舱
          </h2>
          <p className="mt-3 max-w-lg mx-auto" style={{ color: '#c8ddf5' }}>
            进入控制台，创建您的第一个实验，体验自动化数据采集与识别的便捷。
          </p>
          <Link
            href="/dashboard"
            className="mt-8 inline-flex items-center gap-2 px-8 py-3.5 font-semibold rounded-xl hover:opacity-90 transition shadow-lg"
            style={{ background: '#F7941D', color: '#fff' }}
          >
            进入控制台
            <ArrowRight size={18} />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 py-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <Image src="/logo.png" alt="WEWODON" width={100} height={67} className="h-6 w-auto brightness-0 invert opacity-70" />
              <span className="font-semibold text-gray-400 text-sm">
                智能实验方舱
              </span>
            </div>
            <p className="text-gray-500 text-sm">
              &copy; {new Date().getFullYear()} WEWODON &mdash; 智能实验方舱 仪表自动抓拍识别系统
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
