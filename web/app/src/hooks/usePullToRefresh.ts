import { useEffect, useRef, useState, useCallback } from 'react'

const THRESHOLD = 72
const MAX_PULL = 110

export function usePullToRefresh(onRefresh: () => void) {
    const [pullDistance, setPullDistance] = useState(0)
    const [refreshing, setRefreshing] = useState(false)
    const startY = useRef(0)
    const pulling = useRef(false)

    const refresh = useCallback(async () => {
        setRefreshing(true)
        setPullDistance(0)
        try {
            await Promise.resolve(onRefresh())
        } finally {
            setTimeout(() => setRefreshing(false), 600)
        }
    }, [onRefresh])

    useEffect(() => {
        const onTouchStart = (e: TouchEvent) => {
            if (window.scrollY === 0) {
                startY.current = e.touches[0].clientY
                pulling.current = true
            }
        }

        const onTouchMove = (e: TouchEvent) => {
            if (!pulling.current) return
            const delta = e.touches[0].clientY - startY.current
            if (delta > 0 && window.scrollY === 0) {
                setPullDistance(Math.min(delta * 0.5, MAX_PULL))
            } else {
                pulling.current = false
                setPullDistance(0)
            }
        }

        const onTouchEnd = () => {
            if (!pulling.current) return
            pulling.current = false
            if (pullDistance >= THRESHOLD) {
                refresh()
            } else {
                setPullDistance(0)
            }
        }

        document.addEventListener('touchstart', onTouchStart, { passive: true })
        document.addEventListener('touchmove', onTouchMove, { passive: true })
        document.addEventListener('touchend', onTouchEnd)
        return () => {
            document.removeEventListener('touchstart', onTouchStart)
            document.removeEventListener('touchmove', onTouchMove)
            document.removeEventListener('touchend', onTouchEnd)
        }
    }, [pullDistance, refresh])

    return { pullDistance, refreshing, isReady: pullDistance >= THRESHOLD }
}
