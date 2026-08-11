export interface AnkiConnectResponse<T> {
  result: T;
  error: string | null;
}

// AnkiConnect returns {} (not an error) for IDs that don't exist, so bulk
// lookups are typed Partial and callers must check for the empty-object case.
export interface NoteInfo {
  noteId: number;
  modelName: string;
  tags: string[];
  fields: Record<string, { value: string; order: number }>;
  cards?: number[];
}

export interface CardInfo {
  cardId: number;
  note: number;
  deckName: string;
  modelName: string;
  type: number;
  queue: number;
  due: number;
  reps: number;
  lapses: number;
  interval: number;
  factor: number;
}

export interface CardReview {
  id: number;
  ease: number;
  ivl: number;
  lastIvl: number;
  factor: number;
  time: number;
  type: number;
}
