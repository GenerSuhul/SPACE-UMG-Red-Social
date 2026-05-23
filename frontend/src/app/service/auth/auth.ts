import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { UserLoginInterface, UserRegisterInterface } from '../../models/auth';
import { Observable } from 'rxjs';
import { Config } from '../config/config';

@Injectable({
  providedIn: 'root',
})
export class Auth {
  constructor(
    private http: HttpClient,
    private configService: Config
  ) {

  }

  registerUser(userRegister: UserRegisterInterface): Observable<any> {
    const url = `${this.configService.appConfig.apiUrl}/api/auth/register`
    return this.http.post<any>(url, userRegister);
  }

  loginUser(userLogin: UserLoginInterface): Observable<any> {
    const url = `${this.configService.appConfig.apiUrl}/api/auth/login`
    return this.http.post<any>(url, userLogin);
  }

  logoutUser(): Observable<any> {
    const url = `${this.configService.appConfig.apiUrl}/api/auth/logout`
    return this.http.post<any>(url, {});
  }
}
