import { useEffect, useRef } from 'react';
import { useAuth, useUser } from '@clerk/clerk-react';
import api, { setAuthTokenGetter } from '../services/api';

/**
 * Hook that syncs the authenticated Clerk user to the backend
 * and attaches the JWT to all API requests.
 *
 * Should be called once near the root of the app (e.g., in App.tsx).
 */
export function useAuthSync() {
  const { getToken, isSignedIn } = useAuth();
  const { user } = useUser();
  const tokenGetterSet = useRef(false);
  const lastSyncedId = useRef<string | null>(null);

  // Set up the Axios auth interceptor once
  useEffect(() => {
    if (!tokenGetterSet.current) {
      setAuthTokenGetter(getToken);
      tokenGetterSet.current = true;
    }
  }, [getToken]);

  // Sync user to backend when they sign in or user data changes
  useEffect(() => {
    if (!isSignedIn || !user) return;
    if (lastSyncedId.current === user.id) return;

    const syncUser = async () => {
      try {
        await api.post('/api/auth/sync', {
          clerk_id: user.id,
          username:
            user.username ||
            user.firstName ||
            user.emailAddresses[0]?.emailAddress?.split('@')[0] ||
            'player',
          email: user.emailAddresses[0]?.emailAddress || null,
          avatar_url: user.imageUrl || null,
        });
        lastSyncedId.current = user.id;
      } catch (error) {
        console.error('Failed to sync user to backend:', error);
      }
    };

    syncUser();
  }, [isSignedIn, user]);
}
