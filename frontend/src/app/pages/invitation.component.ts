import { Component, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ApiService } from '../core/api.service';
import { AuthService } from '../core/auth.service';
import { Course } from '../core/models';

@Component({ standalone: true, imports: [RouterLink], template: `
  <div class="row justify-content-center"><div class="col-lg-8"><div class="card"><div class="card-body p-4 p-md-5">
    @if (course(); as item) {<span class="badge text-bg-primary mb-2">Invitación de curso</span><h1 class="h2">{{ item.name }}</h1><p class="lead text-secondary">Curso académico {{ item.academicYear }}</p><p>Al unirte, podrás completar el formulario tantas veces como sea necesario y consultar tu evolución.</p>@if (message()) {<div class="alert" [class.alert-danger]="error()" [class.alert-success]="!error()">{{ message() }}</div>} @if (auth.user()) {<button class="btn btn-primary" (click)="join()">Unirme al curso</button>} @else {<a class="btn btn-primary" [routerLink]="['/acceso']">Accede para unirte</a>}}
    @else {<p class="mb-0">{{ message() || 'Comprobando invitación…' }}</p>}
  </div></div></div></div>
` })
export class InvitationComponent implements OnInit { readonly course = signal<Course | null>(null); readonly message = signal(''); readonly error = signal(false); private code = ''; constructor(readonly api: ApiService, readonly auth: AuthService, private readonly route: ActivatedRoute, private readonly router: Router) {} ngOnInit() { this.code = this.route.snapshot.paramMap.get('code') || ''; this.api.invitation(this.code).subscribe({next: value => this.course.set(value.course), error: () => {this.message.set('Este enlace no es válido o el curso ya no está disponible.'); this.error.set(true);}}); } join() { this.api.enroll(this.code).subscribe({next: value => this.router.navigate(['/formulario', value.course.id]), error: response => {this.message.set(response.error?.error || 'No se ha podido realizar la inscripción.'); this.error.set(true);}}); } }

