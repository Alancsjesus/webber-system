export default function Pagination({ page, count, pageSize, itemLabel = 'registro(s)', onPage }) {
  const totalPages = Math.max(1, Math.ceil((count || 0) / (pageSize || 1)))
  if (totalPages <= 1) return null

  const inicio = (page - 1) * pageSize + 1
  const fim    = Math.min(page * pageSize, count)

  return (
    <div className="flex items-center justify-between px-1 py-3 text-sm text-gray-500">
      <span>{inicio}–{fim} de {count} {itemLabel}</span>
      <div className="flex items-center gap-1">
        <button
          onClick={() => onPage(page - 1)}
          disabled={page <= 1}
          className="px-2 py-1 rounded border border-gray-200 disabled:opacity-40 hover:bg-gray-50"
        >
          ←
        </button>
        <span className="px-3 py-1 text-gray-700 font-medium">
          {page} / {totalPages}
        </span>
        <button
          onClick={() => onPage(page + 1)}
          disabled={page >= totalPages}
          className="px-2 py-1 rounded border border-gray-200 disabled:opacity-40 hover:bg-gray-50"
        >
          →
        </button>
      </div>
    </div>
  )
}
