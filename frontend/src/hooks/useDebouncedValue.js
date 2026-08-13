import { useEffect, useState } from 'react'

export default function useDebouncedValue(value, delay = 400) {
  const [debounced, setDebounced] = useState(value)

  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), value ? delay : 0)
    return () => clearTimeout(id)
  }, [value, delay])

  return debounced
}
