import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { TokenService } from '../service/auth/token';

const PUBLIC_ROUTES = ['/auth/register', '/auth/login'];

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  if (PUBLIC_ROUTES.some(route => req.url.includes(route))) {
    return next(req);
  }
  const token = inject(TokenService).get();
  if (token) {
    req = req.clone({ setHeaders: { Authorization: `Bearer ${token}` } });
  }
  return next(req);
};
