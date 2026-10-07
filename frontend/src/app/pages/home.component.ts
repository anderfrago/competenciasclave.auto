import { Component, effect, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../core/api.service';
import { AuthService } from '../core/auth.service';
import { Submission } from '../core/models';

@Component({
  standalone: true, imports: [RouterLink, DatePipe], templateUrl: './home.component.html' })
export class HomeComponent {

  readonly submissions = signal<Submission[]>([]);
  readonly error = signal('');

  constructor(readonly auth: AuthService, readonly api: ApiService) {
    effect((onCleanup) => {
      this.submissions.set([]);
      this.api.courses.set([]);
      if (!this.auth.user()) return;
      const courses = this.api.myCourses().subscribe({
        error: () => this.error.set('No se han podido cargar tus cursos.')
      });
      const submissions = this.api.submissions().subscribe({
        next: value => this.submissions.set(value.submissions.slice(0, 5))
      });
      onCleanup(() => { courses.unsubscribe(); submissions.unsubscribe(); });
    });
  }
}
