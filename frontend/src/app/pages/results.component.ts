import { Component, OnInit, signal } from '@angular/core';
import { DatePipe, DecimalPipe } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ApiService } from '../core/api.service';
import { AuthService } from '../core/auth.service';
import { Submission } from '../core/models';

@Component({
  standalone: true,
  imports: [RouterLink, DatePipe, DecimalPipe],
  templateUrl: './results.component.html'
})
export class ResultsComponent implements OnInit {
  readonly submission = signal<Submission | null>(null);

  constructor(private readonly api: ApiService, private readonly auth: AuthService, private readonly route: ActivatedRoute) { }

  ngOnInit() {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    const request = this.auth.user()?.role === 'student' ? this.api.submission(id) : this.api.tutorSubmission(id);

    request.subscribe({ next: value => this.submission.set(value.submission) });
  }
}
