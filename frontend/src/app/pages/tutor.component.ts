import { Component, OnInit, signal } from '@angular/core';
import { DecimalPipe, DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ApiService } from '../core/api.service';
import { Course } from '../core/models';

@Component({
  standalone: true, 
  imports: [FormsModule, DecimalPipe, DatePipe, RouterLink],
  templateUrl: './tutor.component.html' 
})
export class TutorComponent implements OnInit {
  readonly courses = signal<Course[]>([]);
  readonly dashboard = signal<any>(null);
  selectedCourseId = 0;

  constructor(private readonly api: ApiService) { }

  ngOnInit() {
    this.api.tutorCourses().subscribe({ next: value => this.courses.set(value.courses) });
  }
  loadDashboard() {
    if (!this.selectedCourseId) {
      this.dashboard.set(null); return;
    }

    this.api.dashboard(this.selectedCourseId).subscribe({
      next: value => this.dashboard.set(value)
    });
  }
}
