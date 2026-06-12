type SkeletonMode = 'card' | 'table' | 'chart';

interface Props {
  mode?: SkeletonMode;
  rows?: number;
  cols?: number;
}

function CardSkeleton({ count }: { count: number }) {
  return (
    <div className={`grid grid-cols-1 sm:grid-cols-2 md:grid-cols-${Math.min(count, 4)} gap-4`}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="bg-white rounded-xl p-5 space-y-3 animate-pulse">
          <div className="h-3 bg-gray-200 rounded w-1/2" />
          <div className="h-8 bg-gray-200 rounded w-2/3" />
          <div className="h-8 bg-gray-100 rounded w-full mt-2" />
        </div>
      ))}
    </div>
  );
}

function TableSkeleton({ rows, cols }: { rows: number; cols: number }) {
  return (
    <div className="bg-white rounded-xl overflow-hidden animate-pulse">
      <div className="grid gap-px bg-gray-100" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
        {Array.from({ length: cols }).map((_, i) => (
          <div key={i} className="h-10 bg-gray-200 px-4 flex items-center">
            <div className="h-3 bg-gray-300 rounded w-3/4" />
          </div>
        ))}
        {Array.from({ length: rows * cols }).map((_, i) => (
          <div key={i} className={`h-12 px-4 flex items-center ${Math.floor(i / cols) % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
            <div className="h-3 bg-gray-200 rounded" style={{ width: `${40 + Math.random() * 40}%` }} />
          </div>
        ))}
      </div>
    </div>
  );
}

function ChartSkeleton() {
  return (
    <div className="bg-white rounded-xl p-6 animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-1/4 mb-6" />
      <div className="flex items-end gap-3 h-48">
        {[60, 80, 45, 90, 70, 55, 85, 65].map((h, i) => (
          <div
            key={i}
            className="flex-1 bg-gray-200 rounded-t"
            style={{ height: `${h}%` }}
          />
        ))}
      </div>
    </div>
  );
}

export default function DataSkeleton({ mode = 'card', rows = 5, cols = 4 }: Props) {
  if (mode === 'table') return <TableSkeleton rows={rows} cols={cols} />;
  if (mode === 'chart') return <ChartSkeleton />;
  return <CardSkeleton count={cols} />;
}
