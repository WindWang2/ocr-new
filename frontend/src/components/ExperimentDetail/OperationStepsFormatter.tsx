import React from 'react'

export default function OperationStepsFormatter({ text, svg }: { text?: string, svg?: string }) {
  if (!text) return null

  // 预处理文本：在没有换行符的长字符串中，尝试根据常见序号强制分行
  // 匹配类似 "一、", "1、", "1)", "①", "步骤 1：" 等模式，在其前面加上换行符（如果它前面不是换行符的话）
  let formattedText = text
    .replace(/(?<!\n)(一、|二、|三、|四、|五、|六、|七、|八、|九、|十、)/g, '\n\n$1')
    .replace(/(?<!\n)(\d+、)/g, '\n$1')
    .replace(/(?<!\n)(\d+\))/g, '\n  $1')
    .replace(/(?<!\n)(①|②|③|④|⑤|⑥|⑦|⑧|⑨|⑩)/g, '\n    $1')
    .replace(/(?<!\n)(步骤\s*\d+：)/g, '\n$1')

  const lines = formattedText.split('\n').filter(line => line.trim().length > 0)

  return (
    <div className="flex flex-col xl:flex-row gap-8">
      {/* 文本步骤区 */}
      <div className="flex-1 text-sm text-gray-700 leading-relaxed font-normal">
        {lines.map((line, index) => {
          const trimmed = line.trim()
          
          // 大标题 (一、 二、 三、)
          if (/^[一二三四五六七八九十]、/.test(trimmed) || /^(测试|准备|操作|标定|测量|异常处理|处理)[：:]/.test(trimmed)) {
            return (
              <h4 key={index} className="text-base font-bold text-gray-900 mt-6 mb-3 pb-1 border-b border-gray-100 flex items-center gap-2">
                <span className="w-1 h-3.5 bg-blue-500 rounded-full inline-block" />
                {trimmed}
              </h4>
            )
          }
          
          // 中标题 (1. 或 1、 或者 步骤 1：) - 加粗突出
          if (/^\d+[.、]/.test(trimmed) || /^步骤\s*\d+[：:]/.test(trimmed)) {
            // 解析出标题，将数字后的主要短语加粗
            const match = trimmed.match(/^(\d+[.、])\s*(.*?)[：:](.*)/)
            if (match) {
              return (
                <div key={index} className="mt-4 mb-1 pl-1">
                  <span className="text-[15px] font-bold text-gray-800 mr-2">{match[1]} {match[2]}:</span>
                  <span className="text-gray-600">{match[3]}</span>
                </div>
              )
            }
            return (
              <h5 key={index} className="text-[15px] font-semibold text-gray-800 mt-4 mb-2 pl-1">
                {trimmed}
              </h5>
            )
          }

          // 小列表项 (1) 2) 或者 ① ②)
          if (/^\d+\)/.test(trimmed)) {
            const match = trimmed.match(/^(\d+\))(.*)/)
            return (
              <div key={index} className="flex items-start gap-2 pl-4 mb-2">
                <span className="text-blue-600 font-medium shrink-0 pt-0.5">{match?.[1]}</span>
                <span className="text-gray-600">{match?.[2]}</span>
              </div>
            )
          }

          // 特殊提醒 (【注意事项】等)
          if (/^【.*】/.test(trimmed)) {
            return (
              <div key={index} className="mt-6 mb-2">
                <span className="inline-flex items-center px-2.5 py-1 rounded-md bg-amber-50 text-amber-700 font-bold text-sm border border-amber-200/50">
                  {trimmed}
                </span>
              </div>
            )
          }

          // 强调行 (如：- 注意事项)
          if (/^-/.test(trimmed)) {
             return (
               <div key={index} className="flex items-start gap-2 pl-2 mb-2 mt-2 bg-amber-50/30 p-2.5 rounded-lg border border-amber-100/50">
                 <span className="text-amber-500 font-bold shrink-0">•</span>
                 <span className="text-gray-700 font-medium" dangerouslySetInnerHTML={{__html: trimmed.slice(1).replace(/\*\*(.*?)\*\*/g, '<strong class="text-amber-700">$1</strong>')}} />
               </div>
             )
          }

          // 普通段落 (支持 Markdown 加粗)
          return (
            <p key={index} className="mb-2 text-gray-600 pl-1" dangerouslySetInnerHTML={{__html: trimmed.replace(/\*\*(.*?)\*\*/g, '<strong class="text-gray-900">$1</strong>')}} />
          )
        })}
      </div>

      {/* SVG 流程图区 */}
      {svg && (
        <div className="w-full xl:w-5/12 shrink-0">
          <div className="sticky top-6">
            <h4 className="text-sm font-bold text-gray-800 mb-4 flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-500" />
              核心操作流程
            </h4>
            <div 
              className="bg-white border border-gray-100 rounded-2xl p-6 shadow-[0_2px_20px_-8px_rgba(0,0,0,0.05)]"
              dangerouslySetInnerHTML={{ __html: svg }} 
            />
          </div>
        </div>
      )}
    </div>
  )
}
