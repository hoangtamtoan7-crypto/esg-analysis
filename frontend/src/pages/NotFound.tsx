import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#f5f5f5] flex items-center justify-center p-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 max-w-md w-full text-center">
        <div className="text-7xl font-bold text-[#1677FF]/20 mb-4">404</div>
        <h1 className="text-xl font-bold text-gray-900 mb-2">页面未找到</h1>
        <p className="text-sm text-gray-500 mb-6">您访问的页面不存在或已被移除。</p>
        <Link
          to="/"
          className="inline-block px-6 py-2.5 bg-[#1677FF] text-white rounded-lg text-sm font-medium hover:bg-[#0958d9] transition-colors cursor-pointer"
        >
          返回首页
        </Link>
      </div>
    </div>
  );
}
