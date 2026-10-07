import { Injectable, computed, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { tap } from 'rxjs';
import { User } from './models';

@Injectable({ providedIn: 'root' })
export class AuthService {
  readonly user = signal<User | null>(null);
  readonly sessionError = signal('');

  readonly isAuthenticated = computed(() => !!this.user());

  constructor(private readonly http: HttpClient, private readonly router: Router) {
    localStorage.removeItem('cc_access_token');
    this.refresh().subscribe({ error: () => this.user.set(null) });
  }

  login(email: string, password: string) {
    return this.http.post<{ user: User }>('/api/auth/login', { email, password })
      .pipe(tap(value => this.setSession(value)));
  }
  register(fullName: string, email: string, password: string) {
    return this.http.post<{ message: string }>('/api/auth/register', { fullName, email, password });
  }
  refresh() {
    return this.http.get<{ user: User }>('/api/auth/me').pipe(tap(value => this.user.set(value.user)));
  }
  setSession(value: { user: User }) {
    this.user.set(value.user);
  }
  logout() {
    this.sessionError.set('');
    this.http.post('/api/auth/logout', {}).subscribe({
      next: () => { this.user.set(null); this.router.navigateByUrl('/acceso'); },
      error: response => {
        if (response.status === 401) {
          this.user.set(null); this.router.navigateByUrl('/acceso');
        } else {
          this.sessionError.set('No se ha podido cerrar la sesión. Comprueba la conexión y vuelve a intentarlo.');
        }
      }
    });
  }
  googleLogin() {
    window.location.assign('/api/auth/google');
  }
}

