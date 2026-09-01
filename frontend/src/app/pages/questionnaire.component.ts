import { Component, OnInit, computed, signal } from '@angular/core';
import { ReactiveFormsModule, FormControl, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../core/api.service';
import { Competency, Item } from '../core/models';

@Component({
  standalone: true, imports: [ReactiveFormsModule], templateUrl: './questionnaire.component.html' })
export class QuestionnaireComponent implements OnInit {
  readonly form = new FormGroup({});
  readonly sending = signal(false);
  readonly error = signal(''); readonly courseName = signal('');
  readonly options = [{ value: 1, label: 'Nunca' }, { value: 2, label: 'A veces' }, { value: 3, label: 'En la mayoría de las veces' }, { value: 4, label: 'Siempre' }];

  readonly totalItems = computed(() => this.api.questionnaire().reduce((total, competency) => total + (competency.items?.length || 0), 0));

  readonly answered = signal(0);

  private courseId = 0;

  constructor(readonly api: ApiService, private readonly route: ActivatedRoute, private readonly router: Router) {
    this.form.valueChanges.subscribe(value => this.answered.set(Object.values(value).filter(item => item !== null && item !== undefined).length));
  }
  ngOnInit() {
    this.courseId = Number(this.route.snapshot.paramMap.get('courseId'));
    this.api.myCourses().subscribe({
      next: value => {
        const course = value.courses.find(item => item.id === this.courseId);
        if (!course) this.error.set('No perteneces a este curso.'); else this.courseName.set(course.name);
      },
      error: () =>
        this.error.set('No se ha podido comprobar el curso.')
    }
    );
    this.api.loadQuestionnaire().subscribe({
      next: value => this.addControls(value.competencies),
      error: () => this.error.set('No se ha podido cargar el cuestionario.')
    });
  }
  answerControl(itemId: number) {
    return this.form.get(`item_${itemId}`) as unknown as FormControl<number | null>;
  }
  private addControls(competencies: Competency[]) {
    competencies.forEach(competency => competency.items?.forEach(item =>
      this.form.addControl(`item_${item.id}`,
        new FormControl<number | null>(null, Validators.required))));
  }
  finish() {
    if (this.form.invalid || !this.courseId)
      return; this.sending.set(true);
    const answers = Object.entries(this.form.value).map(([key, value]) => ({
      itemId: Number(key.replace('item_', '')), value: Number(value)
    }));
    this.api.submit(this.courseId, answers).subscribe({
      next: value => this.router.navigate(['/resultado', value.submission.id]),
      error: response => {
        this.error.set(response.error?.error || 'No se ha podido guardar el formulario.');
        this.sending.set(false);
      }
    });
  }
}
