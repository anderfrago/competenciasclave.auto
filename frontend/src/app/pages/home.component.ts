import { Component, OnInit, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../core/api.service';
import { AuthService } from '../core/auth.service';
import { Submission } from '../core/models';

@Component({
  standalone: true, imports: [RouterLink, DatePipe], templateUrl: './home.component.html' })
export class HomeComponent implements OnInit {

  readonly submissions = signal<Submission[]>([]);
  readonly error = signal('');

  constructor(readonly auth: AuthService, readonly api: ApiService) { }

  ngOnInit() {
    if (this.auth.user()) {
      this.api.myCourses().subscribe({
        error: () => this.error.set('No se han podido cargar tus cursos.')
      });
      this.api.submissions().subscribe({
        next: value => this.submissions.set(value.submissions.slice(0, 5))
      });
    }
  }
}
