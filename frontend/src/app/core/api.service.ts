import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { Competency, Course, Item, Submission, User } from './models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  readonly questionnaire = signal<Competency[]>([]);
  readonly courses = signal<Course[]>([]);
  readonly loading = signal(false);
  constructor(private readonly http: HttpClient) { }

  loadQuestionnaire(): Observable<{ competencies: Competency[] }> {
    this.loading.set(true);
    return this.http.get<{ competencies: Competency[] }>('/api/questionnaire')
      .pipe(tap(response => { this.questionnaire.set(response.competencies); this.loading.set(false); }));
  }
  invitation(code: string) {
    return this.http.get<{ course: Course }>(`/api/invitations/${code}`);
  }
  myCourses() {
    return this.http.get<{ courses: Course[] }>('/api/student/courses')
      .pipe(tap(value => this.courses.set(value.courses)));
  }
  enroll(code: string) {
    return this.http.post<{ course: Course }>(`/api/student/courses/${code}/enroll`, {});
  }
  submit(courseId: number, answers: { itemId: number; value: number }[]) {
    return this.http.post<{ submission: Submission }>('/api/student/submissions', { courseId, answers });
  }
  submissions(courseId?: number) {
    return this.http.get<{ submissions: Submission[] }>(`/api/student/submissions${courseId ?
      `?courseId=${courseId}` :
      ''}`);
  }
  submission(id: number) {
    return this.http.get<{ submission: Submission }>(`/api/student/submissions/${id}`);
  }
  tutorCourses() {
    return this.http.get<{ courses: Course[] }>('/api/tutor/courses');
  }
  dashboard(courseId: number) {
    return this.http.get<any>(`/api/tutor/courses/${courseId}/dashboard`);
  }
  tutorSubmission(id: number) {
    return this.http.get<{ submission: Submission }>(`/api/tutor/submissions/${id}`);
  }
  exportCourse(courseId: number, format: 'xlsx' | 'pdf') {
    return this.http.get(`/api/tutor/courses/${courseId}/export.${format}`, { responseType: 'blob' });
  }
  adminCourses() {
    return this.http.get<{ courses: Course[] }>('/api/admin/courses');
  }
  createCourse(payload: Partial<Course>) {
    return this.http.post<{ course: Course }>('/api/admin/courses', payload);
  }
  updateCourse(id: number, payload: Partial<Course>) {
    return this.http.patch<{ course: Course }>(`/api/admin/courses/${id}`, payload);
  }
  deleteCourse(id: number) {
    return this.http.delete(`/api/admin/courses/${id}`);
  }
  users(query = '') {
    return this.http.get<{ users: User[] }>(`/api/admin/users?query=${encodeURIComponent(query)}`);
  }
  createUser(payload: Partial<User> & { password?: string }) {
    return this.http.post<{ user: User }>('/api/admin/users', payload);
  }
  updateUser(id: number, payload: Partial<User> & { password?: string }) {
    return this.http.patch<{ user: User }>(`/api/admin/users/${id}`, payload);
  }
  deleteUser(id: number) { return this.http.delete(`/api/admin/users/${id}`); }
  removeTutor(courseId: number, userId: number) {
    return this.http.delete(`/api/admin/courses/${courseId}/tutors/${userId}`);
  }
  assignTutor(courseId: number, userId: number) {
    return this.http.post<{ course: Course }>(`/api/admin/courses/${courseId}/tutors`, { userId });
  }
  adminCompetencies() {
    return this.http.get<{ competencies: Competency[] }>('/api/admin/competencies');
  }
  createCompetency(payload: Partial<Competency>) {
    return this.http.post<{ competency: Competency }>('/api/admin/competencies', payload);
  }
  updateCompetency(id: number, payload: Partial<Competency>) {
    return this.http.patch<{ competency: Competency }>(`/api/admin/competencies/${id}`, payload);
  }
  deleteCompetency(id: number) {
    return this.http.delete(`/api/admin/competencies/${id}`);
  }
  createItem(competencyId: number, payload: Partial<Item>) {
    return this.http.post<{ item: Item }>(`/api/admin/competencies/${competencyId}/items`, payload);
  }
  updateItem(id: number, payload: Partial<Item>) {
    return this.http.patch<{ item: Item }>(`/api/admin/items/${id}`, payload);
  }
  deleteItem(id: number) {
    return this.http.delete(`/api/admin/items/${id}`);
  }
  updateRubric(id: number, payload: Partial<Competency['rubricLevels'][number]>) {
    return this.http.patch(`/api/admin/rubric-levels/${id}`, payload);
  }
  settings() {
    return this.http.get<{ encouragementMessage: string }>('/api/admin/settings');
  }
  updateSettings(encouragementMessage: string) {
    return this.http.patch('/api/admin/settings', { encouragementMessage });
  }
}
