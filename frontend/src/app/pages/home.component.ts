import { Component, OnInit, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../core/api.service';
import { AuthService } from '../core/auth.service';
import { Submission } from '../core/models';

@Component({ standalone: true, imports: [RouterLink, DatePipe], template: `
  @if (!auth.user()) { <section class="hero p-4 p-md-5"><h1 class="display-5 fw-bold">Autopercepción de competencias clave</h1><p class="lead col-lg-8">Un espacio para reconocer tus fortalezas, detectar oportunidades de mejora y seguir creciendo.</p><a class="btn btn-light btn-lg" routerLink="/acceso">Acceder o crear cuenta</a></section> }
  @if (auth.user()) { <section class="d-flex flex-wrap justify-content-between align-items-end gap-3 mb-4"><div><h1 class="h2 mb-1">Hola, {{ auth.user()?.fullName }}</h1><p class="text-secondary mb-0">Tus cursos y resultados personales.</p></div>@if (auth.user()?.role === 'tutor' || auth.user()?.role === 'admin') {<a class="btn btn-outline-primary" routerLink="/tutor">Ir al panel de tutoría</a>}</section>
    @if (error()) {<div class="alert alert-warning">{{ error() }}</div>}
    <div class="row g-4">@for (course of api.courses(); track course.id) {<div class="col-md-6"><article class="card h-100"><div class="card-body"><span class="badge text-bg-light mb-2">{{ course.academicYear }}</span><h2 class="h4">{{ course.name }}</h2><p class="small-muted">Tutores: {{ course.tutors.length ? course.tutors.map(t => t.fullName).join(', ') : 'Pendiente de asignación' }}</p><a class="btn btn-primary" [routerLink]="['/formulario', course.id]">Completar formulario</a></div></article></div>} @empty {<div class="col-12"><div class="card"><div class="card-body"><h2 class="h4">Todavía no perteneces a ningún curso</h2><p class="mb-0">Usa el enlace de invitación que te ha enviado tu tutor o tutora.</p></div></div></div>}</div>
    @if (submissions().length) {<section class="mt-5"><h2 class="h4">Resultados recientes</h2><div class="card"><ul class="list-group list-group-flush">@for (submission of submissions(); track submission.id) {<li class="list-group-item d-flex justify-content-between align-items-center"><span>{{ submission.course.name }} <small class="text-secondary">· {{ submission.completedAt | date:'shortDate' }}</small></span><a class="btn btn-sm btn-outline-primary" [routerLink]="['/resultado', submission.id]">Ver resultado</a></li>}</ul></div></section>}
  }
` })
export class HomeComponent implements OnInit { readonly submissions = signal<Submission[]>([]); readonly error = signal(''); constructor(readonly auth: AuthService, readonly api: ApiService) {} ngOnInit() { if (this.auth.user()) { this.api.myCourses().subscribe({error: () => this.error.set('No se han podido cargar tus cursos.')}); this.api.submissions().subscribe({next: value => this.submissions.set(value.submissions.slice(0, 5))}); } } }
