import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { TokenService } from '../service/auth/token';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  if (req.url.includes('/auth/')) {
    return next(req);
  }
  const token = inject(TokenService).get();
  if (token) {
    req = req.clone({ setHeaders: { Authorization: `Bearer ${token}` } });
  }
  return next(req);
};
