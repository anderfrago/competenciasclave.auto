export type Role = 'student' | 'tutor' | 'admin';
export interface User { id: number; email: string; fullName: string; role: Role; emailVerified: boolean; authProvider: string; }
export interface RubricLevel { id: number; label: string; maxScore: number; feedback: string; }
export interface Item { id: number; competencyId: number; statement: string; reverseScore: boolean; sortOrder: number; active: boolean; }
export interface Competency { id: number; name: string; description?: string; sortOrder: number; active: boolean; rubricLevels: RubricLevel[]; items?: Item[]; }
export interface Course { id: number; name: string; academicYear: string; active: boolean; inviteCode?: string; tutors: User[]; }
export interface Result { competencyId: number; competency: string; score: number; level: string; feedback: string; }
export interface Submission { id: number; student: User; course: Course; completedAt: string; encouragement?: string; results: Result[]; answers?: {itemId: number; value: number}[]; }

