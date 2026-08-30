import { Injectable, computed, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { tap } from 'rxjs';
import { User } from './models';

@Injectable({ providedIn: 'root' })
export class AuthService {
  readonly user = signal<User | null>(null);
  readonly isAuthenticated = computed(() => !!this.user());
  constructor(private readonly http: HttpClient, private readonly router: Router) { if (localStorage.getItem('cc_access_token')) this.refresh().subscribe({error: () => this.logout()}); }
  login(email: string, password: string) { return this.http.post<{accessToken: string; user: User}>('/api/auth/login', {email, password}).pipe(tap(value => this.setSession(value))); }
  register(fullName: string, email: string, password: string) { return this.http.post<{message: string; verificationUrl?: string}>('/api/auth/register', {fullName, email, password}); }
  refresh() { return this.http.get<{user: User}>('/api/auth/me').pipe(tap(value => this.user.set(value.user))); }
  setGoogleToken(token: string) { localStorage.setItem('cc_access_token', token); return this.refresh(); }
  setSession(value: {accessToken: string; user: User}) { localStorage.setItem('cc_access_token', value.accessToken); this.user.set(value.user); }
  logout() { localStorage.removeItem('cc_access_token'); this.user.set(null); this.router.navigateByUrl('/acceso'); }
  googleLogin() { window.location.assign('/api/auth/google'); }
}

