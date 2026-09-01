import { Component, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../core/api.service';
import { Competency, Course, User } from '../core/models';
@Component({
  standalone: true,
  imports: [FormsModule],
  templateUrl: './admin.component.html'
})
export class AdminComponent implements OnInit {
  readonly courses = signal<Course[]>([]);
  readonly users = signal<User[]>([]);
  readonly competencies = signal<Competency[]>([]);
  readonly selectedCourse = signal<Course | null>(null);
  readonly message = signal('');
  readonly isError = signal(false);

  newCourse = { name: '', academicYear: '' };
  newUser = { fullName: '', email: '', role: 'student' as User['role'], password: '', emailVerified: false };
  userQuery = '';
  encouragement = '';
  newCompetencyName = '';
  newItemText = '';

  constructor(private readonly api: ApiService) { }

  ngOnInit() {
    this.reload(); this.loadUsers(); this.api.settings().subscribe({ next: value => this.encouragement = value.encouragementMessage });
    this.api.adminCompetencies().subscribe({ next: value => this.competencies.set(value.competencies) });
  }
  reload() {
    this.api.adminCourses().subscribe({ next: value => this.courses.set(value.courses) });
  }
  createCourse() {
    this.api.createCourse(this.newCourse).subscribe({
      next: () => {
        this.newCourse = { name: '', academicYear: '' };
        this.reload();
        this.notice('Curso creado.');
      }, error: response => this.notice(response.error?.error || 'No se ha podido crear.', true)
    });

  }
  removeCourse(course: Course) {
    if (!confirm(`¿Eliminar el curso ${course.name}? También se eliminarán sus respuestas.`))
      return; this.api.deleteCourse(course.id).subscribe({
        next: () => {
          this.reload();
          this.notice('Curso eliminado.');
        }
      });
  }

  selectCourse(course: Course) {
    this.selectedCourse.set(course);
    this.users.set([]);
    this.userQuery = '';
  }
  findUsers() {
    if (this.userQuery.length < 2) {
      this.users.set([]);
      return;
    }
    this.api.users(this.userQuery).subscribe({
      next: value => this.users.set(value.users)
    });
  }
  loadUsers() { this.api.users().subscribe({ next: value => this.users.set(value.users) }); }
  createUser() {
    this.api.createUser(this.newUser).subscribe({
      next: () => { this.newUser = { fullName: '', email: '', role: 'student', password: '', emailVerified: false }; this.loadUsers(); this.notice('Usuario creado.'); },
      error: response => this.notice(response.error?.error || 'No se ha podido crear el usuario.', true)
    });
  }
  saveUser(user: User) {
    this.api.updateUser(user.id, user).subscribe({ next: () => this.notice('Usuario actualizado.'), error: response => this.notice(response.error?.error || 'No se ha podido actualizar.', true) });
  }
  removeUser(user: User) {
    if (!confirm(`¿Eliminar la cuenta de ${user.fullName}?`)) return;
    this.api.deleteUser(user.id).subscribe({ next: () => { this.loadUsers(); this.notice('Usuario eliminado.'); }, error: response => this.notice(response.error?.error || 'No se ha podido eliminar.', true) });
  }
  unassignTutor(course: Course, user: User) {
    this.api.removeTutor(course.id, user.id).subscribe({ next: () => { this.reload(); this.notice('Tutor desasignado.'); } });
  }

  assignTutor(user: User) {
    const course = this.selectedCourse();
    if (!course) return;
    this.api.assignTutor(course.id, user.id).subscribe({
      next: value => {
        this.selectedCourse.set(value.course);
        this.reload();
        this.notice('Tutor asignado.');
      }, error: response => this.notice(response.error?.error || 'No se ha podido asignar.', true)
    });
  }
  saveEncouragement() {
    this.api.updateSettings(this.encouragement).subscribe({
      next: () => this.notice('Mensaje actualizado.')
    });
  }
  saveLevel(level: Competency['rubricLevels'][number]) {
    this.api.updateRubric(level.id, level).subscribe({
      next: () => this.notice('Rúbrica actualizada.')
    }
    );
  }

  addCompetency() {
    this.api.createCompetency({ name: this.newCompetencyName, sortOrder: this.competencies().length + 1 }).subscribe({
      next: () => {
        this.newCompetencyName = '';
        this.reloadCompetencies();
        this.notice('Competencia creada.');
      },
      error: response =>
        this.notice(response.error?.error || 'No se ha podido crear.', true)
    })
      ;
  }

  saveCompetency(competency: Competency) {
    this.api.updateCompetency(competency.id, competency).subscribe({
      next: () =>
        this.notice('Competencia actualizada.')
    });
  }

  removeCompetency(competency: Competency) {
    if (!confirm(`¿Eliminar ${competency.name}?`))
      return;
    this.api.deleteCompetency(competency.id).subscribe({
      next: () => {
        this.reloadCompetencies();
        this.notice('Competencia eliminada.');
      }



    });
  }
  addItem(competencyId: number) {
    if (!this.newItemText.trim()) return;
    this.api.createItem(competencyId, { statement: this.newItemText, sortOrder: 999 }).subscribe({
      next: () => {
        this.newItemText = ''; this.reloadCompetencies();
        this.notice('Ítem creado.');
      }
    });
  }
  saveItem(item: any) {
    this.api.updateItem(item.id, item).subscribe({
      next: () =>
        this.notice('Ítem actualizado.')
    });
  }
  removeItem(item: any) {
    if (!confirm('¿Eliminar este ítem?')) return;
    this.api.deleteItem(item.id).subscribe({
      next: () => {
        this.reloadCompetencies(); this.notice('Ítem eliminado.');
      }
    });
  }
  private reloadCompetencies() {
    this.api.adminCompetencies().subscribe({ next: value => this.competencies.set(value.competencies) });
  }
  private notice(text: string, error = false) {
    this.message.set(text); this.isError.set(error);
  }
}
