import { useState, useEffect, useRef } from 'react';
import apiClient from '../../api/client';
import type { ChatMessage, TableData } from '../../types';

function Avatar({ role }: { role: 'user' | 'assistant' }) {
  const isUser = role === 'user';
  return (
    <div
      className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
      style={{ backgroundColor: isUser ? '#52C41A' : '#1677FF' }}
    >
      {isUser ? 'U' : 'AI'}
    </div>
  );
}

export default function AIAssistant() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [available, setAvailable] = useState<boolean | null>(null);
  const chatEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    apiClient.get('/ai/health').then((res) => {
      setAvailable(res.data.available);
    }).catch(() => setAvailable(false));
  }, []);

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function send() {
    const text = input.trim();
    if (!text || loading) return;
    setInput('');

    const userMsg: ChatMessage = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const res = await apiClient.post('/ai/chat', { message: text, history });
      const data = res.data;

      const assistantMsg: ChatMessage = {
        role: 'assistant',
        content: data.text || '无响应',
        tables: data.tables || [],
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      const errMsg: ChatMessage = {
        role: 'assistant',
        content: err?.response?.data?.detail || 'AI助手请求失败，请检查服务状态。',
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  }

  const examples = [
    '比亚迪的ESG表现怎么样？',
    'ESG综合得分排名前10的公司',
    '对比美的集团和格力电器的碳排放',
    '哪些公司在环保投入上最多？',
    '科技行业平均研发投入占比多少？',
  ];

  return (
    <div className="space-y-4 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900">AI智能助手</h1>

      {available === false && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-center">
          <p className="text-amber-800 font-medium">AI助手未就绪</p>
          <p className="text-sm text-amber-600 mt-1">请设置 DEEPSEEK_API_KEY 环境变量后重启后端服务。</p>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 flex flex-col" style={{ minHeight: 520 }}>
        {/* 消息列表 */}
        <div className="flex-1 p-4 space-y-4 overflow-y-auto" style={{ maxHeight: '55vh' }}>
          {messages.length === 0 && (
            <div className="py-12 text-center">
              <div className="w-16 h-16 rounded-full bg-[#1677FF]/10 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-[#1677FF]">AI</span>
              </div>
              <p className="text-gray-400 text-base">ESG智能助手 — 直接输入问题即可获取答案</p>
              <div className="mt-4 flex flex-wrap justify-center gap-2">
                {examples.map((ex, i) => (
                  <button
                    key={i}
                    onClick={() => setInput(ex)}
                    className="px-3 py-1.5 text-sm bg-gray-50 hover:bg-[#1677FF]/10 hover:text-[#1677FF] rounded-full text-gray-500 transition-colors cursor-pointer"
                  >
                    {ex}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex items-end gap-2 msg-fade-in ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
            >
              <Avatar role={msg.role === 'user' ? 'user' : 'assistant'} />
              <div
                className={`max-w-[80%] px-4 py-3 text-sm whitespace-pre-wrap ${
                  msg.role === 'user'
                    ? 'bg-[#1677FF] text-white rounded-2xl rounded-br-sm'
                    : 'bg-gray-100 text-gray-800 rounded-2xl rounded-bl-sm'
                }`}
              >
                {msg.content}

                {msg.tables?.map((tb: TableData, j: number) => (
                  <div key={j} className="mt-3">
                    {tb.title && <p className="text-xs font-medium mb-1 opacity-70">{tb.title}</p>}
                    <div className="overflow-x-auto">
                      <table className="text-xs border-collapse w-full">
                        <thead>
                          <tr>
                            {tb.headers.map((h, k) => (
                              <th key={k} className="border border-gray-300 px-2 py-1 text-left font-medium bg-gray-50 text-gray-700">
                                {h}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {tb.rows.map((row, ri) => (
                            <tr key={ri} className={ri % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                              {Array.isArray(row) ? row.map((cell, ci) => (
                                <td key={ci} className="border border-gray-200 px-2 py-1">
                                  {cell != null ? String(cell) : '-'}
                                </td>
                              )) : null}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex items-end gap-2 msg-fade-in">
              <Avatar role="assistant" />
              <div className="bg-gray-100 rounded-2xl rounded-bl-sm px-4 py-3 text-sm text-gray-500">
                <span className="inline-flex gap-1">
                  <span className="animate-bounce">·</span>
                  <span className="animate-bounce" style={{ animationDelay: '0.15s' }}>·</span>
                  <span className="animate-bounce" style={{ animationDelay: '0.3s' }}>·</span>
                </span>
              </div>
            </div>
          )}

          <div ref={chatEnd} />
        </div>

        {/* 输入区 */}
        <div className="border-t border-gray-100 p-4">
          <div className="flex gap-2 items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
              placeholder="输入您的ESG数据问题..."
              className="flex-1 px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-[#1677FF] focus:border-transparent outline-none"
              disabled={loading || available === false}
            />
            <button
              onClick={send}
              disabled={loading || !input.trim() || available === false}
              className="w-10 h-10 rounded-full bg-[#1677FF] text-white flex items-center justify-center hover:bg-[#0958d9] disabled:opacity-40 transition-colors cursor-pointer flex-shrink-0"
              title="发送"
            >
              <svg className="w-4 h-4 rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-2">基于DeepSeek大模型 · 可查询ESG数据、排名、对比等</p>
        </div>
      </div>
    </div>
  );
}
