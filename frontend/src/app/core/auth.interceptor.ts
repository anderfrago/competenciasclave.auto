import { HttpInterceptorFn } from '@angular/common/http';

export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const token = localStorage.getItem('cc_access_token');

  return next(token && request.url.startsWith('/api') ?
    request.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) :
    request);
};

