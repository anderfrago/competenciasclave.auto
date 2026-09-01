import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from '../core/auth.service';

@Component({
  standalone: true,
  imports: [FormsModule],
  templateUrl: './login.component.html' 
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
