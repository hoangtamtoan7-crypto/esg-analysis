import { useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  HomeIcon,
  BuildingOffice2Icon,
  ChartBarIcon,
  ScaleIcon,
  SparklesIcon,
  DocumentTextIcon,
  Bars3Icon,
  XMarkIcon,
  MagnifyingGlassIcon,
  ArrowTrendingUpIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';

const navigation = [
  { name: '首页概览', href: '/', icon: HomeIcon },
  { name: '公司详情', href: '/companies', icon: BuildingOffice2Icon },
  { name: '指标浏览器', href: '/indicators', icon: MagnifyingGlassIcon },
  { name: '指标对比', href: '/comparison', icon: ChartBarIcon },
  { name: 'ESG分析', href: '/analysis', icon: ScaleIcon },
  { name: '趋势分析', href: '/trends', icon: ArrowTrendingUpIcon },
  { name: '披露合规', href: '/policy', icon: ShieldCheckIcon },
  { name: 'AI助手', href: '/ai-assistant', icon: SparklesIcon },
  { name: '自定义报告', href: '/reports', icon: DocumentTextIcon },
];

const routeNames: Record<string, string> = {
  '/': '首页概览',
  '/companies': '公司详情',
  '/indicators': '指标浏览器',
  '/comparison': '指标对比',
  '/analysis': 'ESG分析',
  '/trends': '趋势分析',
  '/policy': '披露合规',
  '/ai-assistant': 'AI助手',
  '/reports': '报告生成',
};

function SidebarContent({ onClose }: { onClose?: () => void }) {
  return (
    <>
      <nav className="flex-1 mt-4 space-y-1 px-3 overflow-y-auto">
        {navigation.map((item) => (
          <NavLink
            key={item.href}
            to={item.href}
            end={item.href === '/'}
            onClick={onClose}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                isActive
                  ? 'bg-[#1677FF] text-white'
                  : 'text-white/70 hover:bg-white/10'
              }`
            }
          >
            <item.icon className="h-5 w-5 flex-shrink-0" />
            {item.name}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-white/10 text-center text-[12px] text-white/50">
        数据要素大赛 · ESG报告智能提取与分析
      </div>
    </>
  );
}

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const currentName = routeNames[location.pathname] ?? '';
  const isHome = location.pathname === '/';

  return (
    <div className="min-h-screen bg-[#f5f5f5]">
      {/* Mobile sidebar */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="fixed inset-0 bg-gray-900/60" onClick={() => setSidebarOpen(false)} />
          <div className="fixed inset-y-0 left-0 flex w-64 flex-col bg-[#001529] shadow-xl">
            <div className="flex h-16 items-center justify-between px-4 border-b border-white/10">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-[#1677FF] flex items-center justify-center">
                  <ScaleIcon className="h-5 w-5 text-white" />
                </div>
                <span className="text-[18px] font-bold text-white">ESG数据智能平台</span>
              </div>
              <button
                onClick={() => setSidebarOpen(false)}
                className="p-1 rounded-md cursor-pointer text-white/70 hover:text-white"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
            <SidebarContent onClose={() => setSidebarOpen(false)} />
          </div>
        </div>
      )}

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col bg-[#001529]">
        <div className="flex h-16 items-center gap-2 px-6 border-b border-white/10">
          <div className="h-8 w-8 rounded-lg bg-[#1677FF] flex items-center justify-center flex-shrink-0">
            <ScaleIcon className="h-5 w-5 text-white" />
          </div>
          <span className="text-[18px] font-bold text-white">ESG数据智能平台</span>
        </div>
        <SidebarContent />
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        <div className="sticky top-0 z-30 flex h-16 items-center gap-4 bg-white border-b border-gray-200 px-4 lg:px-6 shadow-sm">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-1 rounded-md hover:bg-gray-100 cursor-pointer lg:hidden"
          >
            <Bars3Icon className="h-6 w-6 text-gray-600" />
          </button>
          <span className="text-lg font-bold text-[#1677FF] lg:hidden">ESG数据智能平台</span>

          {/* Breadcrumb (desktop) */}
          <div className="hidden lg:flex items-center text-sm text-gray-400 flex-1">
            <span>首页</span>
            {!isHome && currentName && (
              <>
                <span className="mx-1.5">&gt;</span>
                <span className="text-gray-700 font-medium">{currentName}</span>
              </>
            )}
          </div>

          {/* Search placeholder */}
          <div className="hidden lg:flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5 w-56">
            <MagnifyingGlassIcon className="h-4 w-4 text-gray-400 flex-shrink-0" />
            <span className="text-sm text-gray-400">搜索...</span>
          </div>
        </div>

        {/* Mobile breadcrumb */}
        <div className="lg:hidden flex items-center text-xs text-gray-400 px-4 py-2 bg-white border-b border-gray-100">
          <span>首页</span>
          {!isHome && currentName && (
            <>
              <span className="mx-1.5">&gt;</span>
              <span className="text-gray-600 font-medium">{currentName}</span>
            </>
          )}
        </div>

        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
