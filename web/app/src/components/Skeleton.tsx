interface SkeletonProps {
    className?: string
}

export const Skeleton = ({ className }: SkeletonProps) => (
    <div className={`skeleton${className ? ' ' + className : ''}`} />
)

export const SkeletonCard = ({ className }: SkeletonProps) => (
    <div className={`card-base p-4 space-y-3${className ? ' ' + className : ''}`}>
        <div className="flex items-center gap-3">
            <Skeleton className="w-10 h-10 rounded-xl" />
            <div className="space-y-1.5 flex-1">
                <Skeleton className="h-3 w-32" />
                <Skeleton className="h-2.5 w-20" />
            </div>
        </div>
        <Skeleton className="h-2.5 w-full" />
        <Skeleton className="h-2.5 w-3/4" />
    </div>
)

export const SkeletonRow = ({ className }: SkeletonProps) => (
    <div className={`flex items-center gap-4 p-4${className ? ' ' + className : ''}`}>
        <Skeleton className="w-9 h-9 rounded-xl shrink-0" />
        <div className="flex-1 space-y-2">
            <Skeleton className="h-3 w-40" />
            <Skeleton className="h-2.5 w-24" />
        </div>
        <Skeleton className="h-5 w-16 rounded-full" />
        <Skeleton className="h-4 w-20" />
    </div>
)

export const SkeletonStat = ({ className }: SkeletonProps) => (
    <div className={`card-base p-5 space-y-3${className ? ' ' + className : ''}`}>
        <div className="flex items-center justify-between">
            <Skeleton className="w-10 h-10 rounded-2xl" />
        </div>
        <Skeleton className="h-2.5 w-24" />
        <Skeleton className="h-7 w-32" />
        <Skeleton className="h-4 w-16 rounded-full" />
    </div>
)

export const SkeletonList = ({ count = 5, className }: SkeletonProps & { count?: number }) => (
    <div className={`space-y-2${className ? ' ' + className : ''}`}>
        {[...Array(count)].map((_, i) => (
            <SkeletonRow key={i} />
        ))}
    </div>
)

export default Skeleton
