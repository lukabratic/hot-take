import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDebate } from '../../hooks/useDebate';

/**
 * DebateCreate component — allows a user to generate a new debate session
 * and copy the shareable link to their clipboard.
 */
export function DebateCreate() {
  const navigate = useNavigate();
  const { createSession, loading, error } = useDebate();
  const [shareLink, setShareLink] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleCreate = useCallback(async () => {
    const sessionId = await createSession();
    if (sessionId) {
      const link = `${window.location.origin}/debate/${sessionId}`;
      setShareLink(link);
      // Navigate to the debate page
      navigate(`/debate/${sessionId}`);
    }
  }, [createSession, navigate]);

  const handleCopyLink = useCallback(async () => {
    if (!shareLink) return;

    try {
      await navigator.clipboard.writeText(shareLink);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement('textarea');
      textarea.value = shareLink;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }, [shareLink]);

  return (
    <div className="flex flex-col items-center gap-6 p-6">
      <h2 className="text-2xl font-bold text-white">Challenge a Friend</h2>
      <p className="text-gray-400 text-center max-w-md">
        Create a debate session and share the link with a friend. You'll both
        rank the same players, then compare your takes head-to-head.
      </p>

      {!shareLink ? (
        <button
          onClick={handleCreate}
          disabled={loading}
          className="px-6 py-3 bg-orange-500 hover:bg-orange-600 disabled:bg-gray-600 
                     text-white font-semibold rounded-lg transition-colors"
          aria-label="Create debate session"
        >
          {loading ? 'Creating...' : 'Start a Debate'}
        </button>
      ) : (
        <div className="flex flex-col items-center gap-3">
          <div className="flex items-center gap-2 bg-gray-800 rounded-lg p-3">
            <input
              type="text"
              readOnly
              value={shareLink}
              className="bg-transparent text-gray-200 text-sm w-72 outline-none"
              aria-label="Debate share link"
            />
            <button
              onClick={handleCopyLink}
              className="px-3 py-1 bg-orange-500 hover:bg-orange-600 text-white 
                         text-sm font-medium rounded transition-colors"
              aria-label="Copy link to clipboard"
            >
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>
          <p className="text-gray-500 text-sm">
            Share this link with your opponent
          </p>
        </div>
      )}

      {error && (
        <p className="text-red-400 text-sm" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
