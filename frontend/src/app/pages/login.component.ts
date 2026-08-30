import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from '../core/auth.service';

@Component({
  standalone: true,
  imports: [FormsModule],
  template: `
    <div class="row justify-content-center"><div class="col-lg-8 col-xl-7">
      <section class="hero p-4 p-md-5 mb-4"><h1 class="display-6 fw-bold">Conócete. Avanza.</h1><p class="mb-0 fs-5">Valora tus competencias clave y descubre cómo seguir mejorando.</p></section>
      <div class="card"><div class="card-body p-4 p-md-5">
        @if (verified()) { <div class="alert alert-success">Correo verificado. Ya puedes iniciar sesión.</div> }
        @if (message()) { <div class="alert" [class.alert-danger]="error()" [class.alert-info]="!error()">{{ message() }}</div> }
        <div class="btn-group w-100 mb-4"><button class="btn" [class.btn-primary]="mode() === 'login'" [class.btn-outline-primary]="mode() !== 'login'" (click)="mode.set('login')">Iniciar sesión</button><button class="btn" [class.btn-primary]="mode() === 'register'" [class.btn-outline-primary]="mode() !== 'register'" (click)="mode.set('register')">Crear cuenta</button></div>
        <form (ngSubmit)="submit()">
          @if (mode() === 'register') { <div class="mb-3"><label class="form-label">Nombre y apellidos</label><input class="form-control" name="name" [(ngModel)]="fullName" required></div> }
          <div class="mb-3"><label class="form-label">Correo electrónico</label><input class="form-control" type="email" name="email" [(ngModel)]="email" required></div>
          <div class="mb-3"><label class="form-label">Contraseña</label><input class="form-control" type="password" name="password" [(ngModel)]="password" minlength="8" required><div class="form-text">Mínimo 8 caracteres.</div></div>
          <button class="btn btn-primary w-100" [disabled]="busy()">{{ mode() === 'login' ? 'Entrar' : 'Crear cuenta y verificar correo' }}</button>
        </form>
        <div class="d-flex align-items-center gap-2 my-3"><hr class="flex-grow-1"><span class="small-muted">o</span><hr class="flex-grow-1"></div>
        <button class="btn btn-outline-dark w-100" (click)="auth.googleLogin()">Continuar con Google</button>
        <p class="small-muted mt-4 mb-0">Al crear una cuenta aceptas el tratamiento de datos descrito en <a href="https://cuatrovientos.org/rgpd/" target="_blank" rel="noopener">la política de privacidad</a>.</p>
      </div></div>
    </div></div>
  `
})
export class LoginComponent {
  readonly mode = signal<'login' | 'register'>('login'); readonly busy = signal(false); readonly message = signal(''); readonly error = signal(false); readonly verified = signal(false);
  fullName = ''; email = ''; password = '';
  constructor(readonly auth: AuthService, private readonly router: Router, route: ActivatedRoute) {
    this.verified.set(route.snapshot.queryParamMap.get('verified') === '1');
    const token = route.snapshot.queryParamMap.get('token');
    if (token) auth.setGoogleToken(token).subscribe({next: () => router.navigateByUrl('/'), error: () => this.show('No se pudo completar el acceso con Google.', true)});
  }
  submit() {
    this.busy.set(true); this.message.set('');
    if (this.mode() === 'login') {
      this.auth.login(this.email, this.password).subscribe({next: () => { this.busy.set(false); this.router.navigateByUrl('/'); }, error: (response: any) => this.handleError(response)});
    } else {
      this.auth.register(this.fullName, this.email, this.password).subscribe({next: value => { this.busy.set(false); this.show(value.message, false); }, error: (response: any) => this.handleError(response)});
    }
  }
  private handleError(response: any) { this.busy.set(false); this.show(response.error?.error || 'No se ha podido completar la solicitud.', true); }
  private show(text: string, isError: boolean) { this.message.set(text); this.error.set(isError); }
}
