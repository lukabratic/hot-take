import { useAuth, RedirectToSignIn } from '@clerk/clerk-react';

/**
 * Route guard that requires authentication.
 * Renders children if the user is signed in.
 * Redirects to Clerk's sign-in flow if not authenticated.
 *
 * Requirements: 14.2, 14.3
 */
export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isSignedIn, isLoaded } = useAuth();

  if (!isLoaded) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-4 border-nba-gold border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!isSignedIn) {
    return <RedirectToSignIn />;
  }

  return <>{children}</>;
}
