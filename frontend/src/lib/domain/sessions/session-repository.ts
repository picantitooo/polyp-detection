import type { Session } from './session';

export interface SessionRepository {
	load(): Session[];
	save(records: Session[]): void;
}
