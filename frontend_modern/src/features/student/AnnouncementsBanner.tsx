import { useAnnouncements } from './useAnnouncements';

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  } catch {
    return '';
  }
}

export const AnnouncementsBanner = () => {
  const { data: announcements, isLoading } = useAnnouncements();

  if (isLoading || !announcements || announcements.length === 0) return null;

  return (
    <div className="mb-6 space-y-2">
      {announcements.map((a) => (
        <div
          key={a.id}
          className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3"
          role="status"
        >
          <div className="flex items-start gap-2">
            <span aria-hidden className="mt-0.5">📢</span>
            <div className="min-w-0">
              <p className="text-sm text-amber-900 whitespace-pre-wrap break-words">{a.message}</p>
              <p className="mt-1 text-xs text-amber-700">
                {a.subject_room_display}
                {a.author_name ? ` · ${a.author_name}` : ''} · {formatDate(a.created_at)}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
