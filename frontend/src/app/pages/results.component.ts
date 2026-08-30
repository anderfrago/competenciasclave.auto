import { Component, OnInit, signal } from '@angular/core';
import { DatePipe, DecimalPipe } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ApiService } from '../core/api.service';
import { AuthService } from '../core/auth.service';
import { Submission } from '../core/models';

@Component({ standalone: true, imports: [RouterLink, DatePipe, DecimalPipe], template: `
  @if (submission(); as item) {<section class="hero p-4 p-md-5 mb-4"><span class="badge text-bg-light mb-3">Resultado completado el {{ item.completedAt | date:'longDate' }}</span><h1 class="display-6 fw-bold">Tu perfil de competencias</h1><p class="lead mb-0">{{ item.encouragement }}</p></section><div class="row g-4">@for (result of item.results; track result.competencyId) {<div class="col-md-6"><article class="card h-100"><div class="card-body"><div class="d-flex justify-content-between align-items-start"><div><h2 class="h5">{{ result.competency }}</h2><span class="badge text-bg-info">{{ result.level }}</span></div><div class="text-end"><div class="score-number">{{ result.score | number:'1.2-2' }}</div><div class="small-muted">sobre 4</div></div></div><div class="chart-bar my-3"><span [style.width.%]="result.score * 25"></span></div><p class="mb-0">{{ result.feedback }}</p></div></article></div>}</div><div class="mt-4"><a class="btn btn-primary" routerLink="/">Volver a mi espacio</a></div>} @else {<p class="text-center py-5">Cargando resultado…</p>}
` })
export class ResultsComponent implements OnInit { readonly submission = signal<Submission | null>(null); constructor(private readonly api: ApiService, private readonly auth: AuthService, private readonly route: ActivatedRoute) {} ngOnInit() { const id = Number(this.route.snapshot.paramMap.get('id')); const request = this.auth.user()?.role === 'student' ? this.api.submission(id) : this.api.tutorSubmission(id); request.subscribe({next: value => this.submission.set(value.submission)}); } }
