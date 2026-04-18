import { useEffect, useRef, useState, useCallback } from 'react'

const THRESHOLD = 72
const MAX_PULL = 110

export function usePullToRefresh(onRefresh: () => void) {
    const [pullDistance, setPullDistance] = useState(0)
    const [refreshing, setRefreshing] = useState(false)
    const startY = useRef(0)
    const pulling = useRef(false)
    const pullRef = useRef(0)
    const startedAtTop = useRef(false)

    const refresh = useCallback(async () => {
        setRefreshing(true)
        setPullDistance(0)
        pullRef.current = 0
        try {
            await Promise.resolve(onRefresh())
        } finally {
            setTimeout(() => setRefreshing(false), 600)
        }
    }, [onRefresh])

    useEffect(() => {
        const onTouchStart = (e: TouchEvent) => {
            startY.current = e.touches[0].clientY
            startedAtTop.current = window.scrollY === 0
            pulling.current = false
        }

        const onTouchMove = (e: TouchEvent) => {
            if (!startedAtTop.current || window.scrollY !== 0) return
            const delta = e.touches[0].clientY - startY.current
            if (delta > 0) {
                pulling.current = true
                e.preventDefault()
                const dist = Math.min(delta * 0.5, MAX_PULL)
                pullRef.current = dist
                setPullDistance(dist)
            } else {
                pulling.current = false
                if (pullRef.current > 0) {
                    pullRef.current = 0
                    setPullDistance(0)
                }
            }
        }

        const onTouchEnd = () => {
            if (!pulling.current) return
            pulling.current = false
            if (pullRef.current >= THRESHOLD) {
                refresh()
            } else {
                pullRef.current = 0
                setPullDistance(0)
            }
        }

        document.addEventListener('touchstart', onTouchStart, { passive: true })
        document.addEventListener('touchmove', onTouchMove, { passive: false })
        document.addEventListener('touchend', onTouchEnd)
        return () => {
            document.removeEventListener('touchstart', onTouchStart)
            document.removeEventListener('touchmove', onTouchMove)
            document.removeEventListener('touchend', onTouchEnd)
        }
    }, [refresh])

    return { pullDistance, refreshing }
}
