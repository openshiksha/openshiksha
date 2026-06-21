import { useState } from 'react';
import { useChapterVideos } from './useChapterVideos';

interface VideosPanelProps {
  chapterId: number;
}

export const VideosPanel = ({ chapterId }: VideosPanelProps) => {
  const { data: videos, isLoading } = useChapterVideos(chapterId);
  const [openId, setOpenId] = useState<number | null>(null);

  // Nothing to show until we know there are videos — keep the page uncluttered.
  if (isLoading || !videos || videos.length === 0) return null;

  return (
    <div className="os-card mt-8 p-5">
      <h3 className="mb-3 flex items-center gap-2 font-display text-sm font-semibold text-ink-800">
        <span aria-hidden>🎬</span> Learn this chapter
      </h3>
      <ul className="space-y-2">
        {videos.map((video) => {
          const isOpen = openId === video.id;
          return (
            <li key={video.id} className="rounded-lg border border-ink-100">
              <button
                type="button"
                onClick={() => setOpenId(isOpen ? null : video.id)}
                className="flex w-full items-center justify-between rounded-lg px-4 py-3 text-left transition-colors hover:bg-brand-50/40 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-brand-500"
                aria-expanded={isOpen}
              >
                <span className="text-sm font-medium text-ink-800">{video.title}</span>
                <span className="text-xs font-semibold text-brand-700">
                  {isOpen ? '▲ Hide' : '▶ Watch'}
                </span>
              </button>
              {isOpen && (
                <div className="px-4 pb-4">
                  <div
                    className="relative w-full overflow-hidden rounded-lg"
                    style={{ paddingTop: '56.25%' }}
                  >
                    <iframe
                      src={video.embed_url}
                      title={video.title}
                      className="absolute inset-0 h-full w-full"
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      allowFullScreen
                    />
                  </div>
                  {video.description && (
                    <p className="mt-2 text-xs text-ink-500">{video.description}</p>
                  )}
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
};
