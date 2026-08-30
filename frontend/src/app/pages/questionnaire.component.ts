import { Component, OnInit, computed, signal } from '@angular/core';
import { ReactiveFormsModule, FormControl, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../core/api.service';
import { Competency, Item } from '../core/models';

@Component({ standalone: true, imports: [ReactiveFormsModule], template: `
  <section class="mb-4"><span class="badge text-bg-primary mb-2">Autopercepción</span><h1 class="h2">Valora tus competencias</h1><p class="text-secondary mb-0">Responde pensando en cómo actúas habitualmente. No hay respuestas correctas o incorrectas.</p></section>
  @if (error()) {<div class="alert alert-danger">{{ error() }}</div>}
  @if (courseName()) {<div class="alert alert-light border">Curso seleccionado: <strong>{{ courseName() }}</strong></div>}
  @if (api.questionnaire().length) {<form [formGroup]="form" (ngSubmit)="finish()">
    @for (competency of api.questionnaire(); track competency.id) {<section class="card competency-card mb-4"><div class="card-body p-4"><h2 class="h4">{{ competency.name }}</h2><p class="small-muted">Selecciona una opción para cada afirmación.</p>@for (item of competency.items || []; track item.id) {<div class="question-row"><p class="fw-medium mb-3">{{ item.statement }}</p><div class="d-flex flex-wrap gap-2">@for (option of options; track option.value) {<label class="option-label border rounded px-3 py-2" [class.border-primary]="answerControl(item.id).value === option.value" [class.bg-primary-subtle]="answerControl(item.id).value === option.value"><input class="form-check-input me-2" type="radio" [formControl]="answerControl(item.id)" [value]="option.value">{{ option.label }}</label>}</div></div>}</div></section>}
    <div class="sticky-bottom bg-body py-3 border-top"><button class="btn btn-primary btn-lg" [disabled]="form.invalid || sending()">{{ sending() ? 'Guardando…' : 'Ver mi resultado' }}</button><span class="ms-3 small-muted">{{ answered() }} de {{ totalItems() }} respuestas completadas</span></div>
  </form>} @else {<div class="text-center py-5">Cargando cuestionario…</div>}
` })
export class QuestionnaireComponent implements OnInit {
  readonly form = new FormGroup({}); readonly sending = signal(false); readonly error = signal(''); readonly courseName = signal(''); readonly options = [{value: 1, label: 'Nunca'}, {value: 2, label: 'A veces'}, {value: 3, label: 'En la mayoría de las veces'}, {value: 4, label: 'Siempre'}];
  readonly totalItems = computed(() => this.api.questionnaire().reduce((total, competency) => total + (competency.items?.length || 0), 0));
  readonly answered = signal(0);
  private courseId = 0;
  constructor(readonly api: ApiService, private readonly route: ActivatedRoute, private readonly router: Router) { this.form.valueChanges.subscribe(value => this.answered.set(Object.values(value).filter(item => item !== null && item !== undefined).length)); }
  ngOnInit() { this.courseId = Number(this.route.snapshot.paramMap.get('courseId')); this.api.myCourses().subscribe({next: value => { const course = value.courses.find(item => item.id === this.courseId); if (!course) this.error.set('No perteneces a este curso.'); else this.courseName.set(course.name); }, error: () => this.error.set('No se ha podido comprobar el curso.')}); this.api.loadQuestionnaire().subscribe({next: value => this.addControls(value.competencies), error: () => this.error.set('No se ha podido cargar el cuestionario.')}); }
  answerControl(itemId: number) { return this.form.get(`item_${itemId}`) as unknown as FormControl<number | null>; }
  private addControls(competencies: Competency[]) { competencies.forEach(competency => competency.items?.forEach(item => this.form.addControl(`item_${item.id}`, new FormControl<number | null>(null, Validators.required)))); }
  finish() { if (this.form.invalid || !this.courseId) return; this.sending.set(true); const answers = Object.entries(this.form.value).map(([key, value]) => ({itemId: Number(key.replace('item_', '')), value: Number(value)})); this.api.submit(this.courseId, answers).subscribe({next: value => this.router.navigate(['/resultado', value.submission.id]), error: response => {this.error.set(response.error?.error || 'No se ha podido guardar el formulario.'); this.sending.set(false);}}); }
}
