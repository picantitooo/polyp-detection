import type { Session } from '$lib/domain/sessions/session';

export type ReviewDecision = 'pending' | 'confirmed' | 'adenoma' | 'hiperplasico';
export type Validation = { decision: ReviewDecision; note: string };
export type ReportStatus = 'draft' | 'reviewed' | 'final';
export type SessionReport = {
	id: string;
	session: Session;
	evidenceIds: string[];
	reviewIds: string[];
	validations: Record<string, Validation>;
	observations: string;
	createdAt: string;
	updatedAt: string;
	status: ReportStatus;
};

export const reportLabels: Record<ReportStatus, string> = {
	draft: 'Borrador', reviewed: 'Revisado', final: 'Finalizado'
};
export const reviewLabels: Record<ReviewDecision, string> = {
	pending: 'Pendiente', confirmed: 'Sugerencia confirmada',
	adenoma: 'Corregido a adenoma', hiperplasico: 'Corregido a hiperplásico'
};

export function reviewComplete(report: SessionReport) {
	return report.evidenceIds.every((id) =>
		report.validations[id] !== undefined && report.validations[id].decision !== 'pending'
	);
}
