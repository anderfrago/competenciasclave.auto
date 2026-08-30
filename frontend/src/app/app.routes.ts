import { Routes } from '@angular/router';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, map, of } from 'rxjs';
import { AuthService } from './core/auth.service';
import { AdminComponent } from './pages/admin.component';
import { HomeComponent } from './pages/home.component';
import { InvitationComponent } from './pages/invitation.component';
import { LoginComponent } from './pages/login.component';
import { QuestionnaireComponent } from './pages/questionnaire.component';
import { ResultsComponent } from './pages/results.component';
import { TutorComponent } from './pages/tutor.component';

const roleGuard = (...roles: string[]) => () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (auth.user()) return roles.includes(auth.user()!.role) || router.createUrlTree(['/acceso']);
  if (!localStorage.getItem('cc_access_token')) return router.createUrlTree(['/acceso']);
  return auth.refresh().pipe(map(value => roles.includes(value.user.role) || router.createUrlTree(['/acceso'])), catchError(() => of(router.createUrlTree(['/acceso']))));
};

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'acceso', component: LoginComponent },
  { path: 'invitacion/:code', component: InvitationComponent },
  { path: 'formulario/:courseId', component: QuestionnaireComponent, canActivate: [roleGuard('student', 'tutor', 'admin')] },
  { path: 'resultado/:id', component: ResultsComponent, canActivate: [roleGuard('student', 'tutor', 'admin')] },
  { path: 'tutor', component: TutorComponent, canActivate: [roleGuard('tutor', 'admin')] },
  { path: 'administracion', component: AdminComponent, canActivate: [roleGuard('admin')] },
  { path: '**', redirectTo: '' }
];
