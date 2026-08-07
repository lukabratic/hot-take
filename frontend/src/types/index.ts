/** Basketball position categories */
export type Position = 'PG' | 'SG' | 'SF' | 'PF' | 'C' | 'Wings' | 'Big Men' | 'Mixed';

/** Category type for grouping players */
export type CategoryType = 'all' | 'position' | 'team' | 'decade' | 'conference';

/** A single category value with metadata */
export interface CategoryValue {
  value: string;
  label: string;
  playerCount: number;
  disabled: boolean; // true if playerCount < 5
}

/** Selection mode for choosing a category */
export type SelectionMode = 'spin' | 'pick';

/** Theme modifiers that define the ranking evaluation lens */
export type ThemeModifier =
  | 'All-Time'
  | 'Peak Season Only'
  | 'Playoff Performance'
  | 'Defensive Impact'
  | 'Regular Season Only'
  | 'Championship Era Only';

/** Game modes available */
export type GameMode = 'daily' | 'quickplay' | 'hoopiq' | 'debate';

/** Scoring rubric options */
export type Rubric = 'analytics' | 'reputation';

/** Letter grades assigned based on Kendall tau distance */
export type LetterGrade = 'S' | 'A' | 'B' | 'C' | 'D';

/** A Roll represents a position + theme modifier combination for a game session */
export interface Roll {
  id: number;
  position: Position;
  themeModifier: ThemeModifier;
  dailyDate: string | null;
  mode: GameMode;
  players: Player[];
  categoryType?: CategoryType;
  categoryValue?: string;
}

/** Player stats structure for career/peak/playoff statistics */
export interface PlayerStats {
  pts: number;
  reb: number;
  ast: number;
  stl: number;
  blk: number;
  per: number;
  bpm: number;
  vorp: number;
  ws: number;
}

/** An NBA player in the player pool */
export interface Player {
  id: number;
  name: string;
  position: string;
  era: string;
  careerStats: PlayerStats;
  peakStats: PlayerStats;
  playoffStats: PlayerStats | null;
  allNbaSelections: number;
  mvpVoteShares: number;
  championships: number;
  allStarSelections: number;
  hofRank: number | null;
  bbrefId: string;
}

/** A user-submitted ranking for a roll */
export interface Ranking {
  id: number;
  userId: string;
  rollId: number;
  rubric: Rubric;
  playerOrder: number[];
  kendallTauDistance: number;
  letterGrade: LetterGrade;
  mode: GameMode;
  createdAt: string;
}

/** Community heatmap data showing distribution of player placements */
export interface CommunityHeatmap {
  /** Map of player ID to slot distribution percentages */
  data: Record<number, Record<number, number>>;
  totalSubmissions: number;
}

/** The full reveal result returned after submitting a ranking */
export interface RevealResult {
  ranking: Ranking;
  consensusOrder: number[];
  communityHeatmap: CommunityHeatmap;
  controversialPick: ControversialPick | null;
  commentary: string;
}

/** Identifies the user's most controversial pick */
export interface ControversialPick {
  playerId: number;
  slot: number;
  communityAgreement: number;
}

/** Leaderboard scope options */
export type LeaderboardScope = 'today' | 'week' | 'alltime' | 'friends';

/** Debate session status */
export type DebateStatus = 'waiting' | 'complete';

/** A debate session between two users */
export interface DebateSession {
  id: string;
  rollId: number;
  creatorId: string;
  opponentId: string | null;
  status: DebateStatus;
  createdAt: string;
}

/** A participant's result in a debate comparison */
export interface DebateParticipantResult {
  userId: string;
  username: string;
  ranking: {
    id: number;
    rubric: Rubric;
    playerOrder: number[];
    kendallTauDistance: number;
    letterGrade: LetterGrade;
  };
  consensusOrder: number[];
}

/** Full comparison data for a completed debate */
export interface DebateComparison {
  sessionId: string;
  status: DebateStatus;
  roll: {
    id: number;
    position: Position;
    themeModifier: ThemeModifier;
  };
  creator: DebateParticipantResult;
  opponent: DebateParticipantResult;
  differences: number[];
  playerNames: Record<number, string>;
}

/** Roll data returned for a debate session */
export interface DebateRoll {
  id: number;
  position: Position;
  themeModifier: ThemeModifier;
  mode: 'debate';
  players: Pick<Player, 'id' | 'name' | 'position' | 'era'>[];
}

/** A single entry in the leaderboard */
export interface LeaderboardEntry {
  rank: number;
  userId: string;
  username: string;
  score: number;
  currentStreak: number;
}

/** Response from the leaderboard API */
export interface LeaderboardData {
  scope: LeaderboardScope;
  entries: LeaderboardEntry[];
}

/** A single entry in the user's ranking history for the profile */
export interface ProfileRankingHistoryEntry {
  id: number;
  rollPosition: string;
  rollThemeModifier: string;
  letterGrade: LetterGrade;
  mode: GameMode;
  rubric: Rubric;
  kendallTauDistance: number;
  createdAt: string;
}

/** User profile stats response */
export interface ProfileStats {
  id: string;
  username: string;
  avatarUrl: string | null;
  totalGames: number;
  averageGrade: number;
  bestGrade: string;
  currentStreak: number;
  longestStreak: number;
  gradeDistribution: Record<LetterGrade, number>;
  recentHistory: ProfileRankingHistoryEntry[];
}
