import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import ErrorBoundary from './components/ErrorBoundary';
import Home from './pages/Home';
import Companies from './pages/Companies';
import Comparison from './pages/Comparison';
import Analysis from './pages/Analysis';
import AIAssistant from './pages/AIAssistant';
import Reports from './pages/Reports';
import Indicators from './pages/Indicators';
import Trends from './pages/Trends';
import Policy from './pages/Policy';
import NotFound from './pages/NotFound';

export default function App() {
  return (
    <ErrorBoundary>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="companies" element={<Companies />} />
          <Route path="companies/:stockCode" element={<Companies />} />
          <Route path="comparison" element={<Comparison />} />
          <Route path="indicators" element={<Indicators />} />
          <Route path="analysis" element={<Analysis />} />
          <Route path="trends" element={<Trends />} />
          <Route path="policy" element={<Policy />} />
          <Route path="ai-assistant" element={<AIAssistant />} />
          <Route path="reports" element={<Reports />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </ErrorBoundary>
  );
}
