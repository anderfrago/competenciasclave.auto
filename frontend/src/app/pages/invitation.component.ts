import { Component, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ApiService } from '../core/api.service';
import { AuthService } from '../core/auth.service';
import { Course } from '../core/models';

@Component({
  standalone: true, imports: [RouterLink], templateUrl: './invitation.component.html' })
export class InvitationComponent implements OnInit {
  readonly course = signal<Course | null>(null);
  readonly message = signal('');
  readonly error = signal(false);
  private code = '';

  constructor(readonly api: ApiService, readonly auth: AuthService, private readonly route: ActivatedRoute, private readonly router: Router) { }

  ngOnInit() {
    this.code = this.route.snapshot.paramMap.get('code') || '';
    this.api.invitation(this.code).subscribe({
      next:
        value => this.course.set(value.course),
      error: () => {
        this.message.set('Este enlace no es válido o el curso ya no está disponible.'); this.error.set(true);

      }
    });
  } join() {
    this.api.enroll(this.code).subscribe({
      next: value => this.router.navigate(['/formulario',
        value.course.id]),
      error: response => {
        this.message.set(response.error?.error || 'No se ha podido realizar la inscripción.');
        this.error.set(true);
      }
    });
  }
}

