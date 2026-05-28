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
    <div className="mt-8 rounded-xl border border-gray-200 bg-white p-5">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-3">
        <span aria-hidden>🎬</span> Learn this chapter
      </h3>
      <ul className="space-y-2">
        {videos.map((video) => {
          const isOpen = openId === video.id;
          return (
            <li key={video.id} className="rounded-lg border border-gray-100">
              <button
                type="button"
                onClick={() => setOpenId(isOpen ? null : video.id)}
                className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-50 rounded-lg"
                aria-expanded={isOpen}
              >
                <span className="text-sm font-medium text-gray-800">{video.title}</span>
                <span className="text-gray-400 text-xs">{isOpen ? '▲ Hide' : '▶ Watch'}</span>
              </button>
              {isOpen && (
                <div className="px-4 pb-4">
                  <div className="relative w-full overflow-hidden rounded-lg" style={{ paddingTop: '56.25%' }}>
                    <iframe
                      src={video.embed_url}
                      title={video.title}
                      className="absolute inset-0 h-full w-full"
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      allowFullScreen
                    />
                  </div>
                  {video.description && (
                    <p className="mt-2 text-xs text-gray-500">{video.description}</p>
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
