import { useState, useEffect } from 'react'
import { Wifi, WifiOff } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { OfflineService } from '../services/offline'

export default function NetworkStatus() {
    const [isOnline, setIsOnline] = useState(navigator.onLine)
    const [showStatus, setShowStatus] = useState(false)
    const [syncError, setSyncError] = useState<string | null>(null)
    const [queueCount, setQueueCount] = useState(OfflineService.getQueue().length)
    const [lastQueuedTitle, setLastQueuedTitle] = useState<string | null>(null)
    const [lastSyncedTitle, setLastSyncedTitle] = useState<string | null>(null)
    const [showToast, setShowToast] = useState(false)

    useEffect(() => {
        const handleOnline = () => {
            setIsOnline(true)
            setShowStatus(true)
            OfflineService.sync()
            setTimeout(() => setShowStatus(false), 3000)
        }
        const handleOffline = () => {
            setIsOnline(false)
            setShowStatus(true)
            setSyncError(null)
        }

        const handleSyncError = (e: any) => {
            setSyncError(e.detail.error);
        }

        const handleQueueChange = () => {
            const queue = OfflineService.getQueue()
            const last = queue[queue.length - 1]
            setQueueCount(queue.length)
            // Shfaq "U ruajt offline" vetëm kur jemi offline – kur jemi online pas suksesi (email, etj.) mos ngatërro përdoruesin
            if (last && !navigator.onLine) {
                setLastQueuedTitle(last.title || 'Veprim')
                setShowToast(true)
                setTimeout(() => setShowToast(false), 2500)
            } else {
                setLastQueuedTitle(null)
            }
        }

        const handleSyncCompleted = (e: any) => {
            const actionTitle = e?.detail?.title || 'Veprim'
            setLastSyncedTitle(actionTitle)
            setQueueCount(OfflineService.getQueue().length)
            setShowToast(true)
            setTimeout(() => setShowToast(false), 2500)
        }

        window.addEventListener('online', handleOnline)
        window.addEventListener('offline', handleOffline)
        window.addEventListener('offline_sync_error', handleSyncError)
        window.addEventListener('offline_queue_changed', handleQueueChange)
        window.addEventListener('offline_sync_completed', handleSyncCompleted)

        const syncInterval = setInterval(() => {
            if (navigator.onLine) OfflineService.sync();
        }, 30000);

        return () => {
            window.removeEventListener('online', handleOnline)
            window.removeEventListener('offline', handleOffline)
            window.removeEventListener('offline_sync_error', handleSyncError)
            window.removeEventListener('offline_queue_changed', handleQueueChange)
            window.removeEventListener('offline_sync_completed', handleSyncCompleted)
            clearInterval(syncInterval)
        }
    }, [])

    return (
        <AnimatePresence>
            {(showStatus || syncError) && (
                <motion.div
                    initial={{ y: -50, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    exit={{ y: -50, opacity: 0 }}
                    onClick={() => setSyncError(null)}
                    className={`fixed top-4 left-1/2 -track-x-1/2 z-[9999] px-4 py-3 rounded-2xl shadow-xl flex items-center gap-3 font-bold text-sm cursor-pointer max-w-[90vw] whitespace-normal ${syncError ? 'bg-rose-600 text-white' : (isOnline ? 'bg-emerald-500 text-white' : 'bg-slate-800 text-white')
                        }`}
                    style={{ left: '50%', transform: 'translateX(-50%)' }}
                >
                    {syncError ? (
                        <>
                            <WifiOff size={18} />
                            <div className="flex flex-col">
                                <span>Konflikt gjatë sinkronizimit</span>
                                <span className="text-[10px] opacity-80 font-medium">{syncError}</span>
                            </div>
                        </>
                    ) : isOnline ? (
                        <>
                            <Wifi size={18} />
                            <span>Jeni përsëri online</span>
                        </>
                    ) : (
                        <>
                            <WifiOff size={18} />
                            <span>Jeni offline. Veprimet do ruhen në telefon.</span>
                        </>
                    )}
                </motion.div>
            )}
            {showToast && (lastQueuedTitle || lastSyncedTitle) && (
                <motion.div
                    initial={{ y: -50, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    exit={{ y: -50, opacity: 0 }}
                    className={`fixed top-16 left-1/2 -track-x-1/2 z-[9999] px-4 py-3 rounded-2xl shadow-xl flex items-center gap-3 font-bold text-sm max-w-[90vw] whitespace-normal ${lastSyncedTitle ? 'bg-emerald-600 text-white' : 'bg-amber-500 text-white'
                        }`}
                    style={{ left: '50%', transform: 'translateX(-50%)' }}
                >
                    {lastSyncedTitle ? (
                        <span>U sinkronizua: {lastSyncedTitle}</span>
                    ) : (
                        <span>U ruajt offline: {lastQueuedTitle}</span>
                    )}
                </motion.div>
            )}
            {!isOnline && !showStatus && !syncError && (
                <div className="fixed top-4 left-1/2 -translate-x-1/2 z-[9999] opacity-50">
                    <div className="bg-rose-500 text-white px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest flex items-center gap-1.5 shadow-sm">
                        <WifiOff size={10} />
                        Offline {queueCount > 0 ? `(${queueCount})` : ''}
                    </div>
                </div>
            )}
        </AnimatePresence>
    )
}
